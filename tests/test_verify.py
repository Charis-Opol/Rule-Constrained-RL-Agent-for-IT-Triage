"""Phase 9, part B: fix with verification (opt-in through pilot_settings_v3.json)."""
import json
from pathlib import Path

import numpy as np
import pytest
from gymnasium.utils.env_checker import check_env

from src.agents.baselines import AlwaysEscalate, Threshold
from src.agents.dqn import make_env
from src.agents.exact import solve
from src.evaluation import run_episodes, summarise
from src.sim.scenario import build_scenario, load_scenario
from src.sim.triage_env import TriageEnv

PILOT = Path(__file__).resolve().parents[1] / "experiments" / "pilot"
MODEL, V2, V3 = PILOT / "pilot_model_v2.json", PILOT / "pilot_settings_v2.json", PILOT / "pilot_settings_v3.json"
SCENARIO = load_scenario(MODEL, V3)


def env_with_cause(cause, seed=0):
    env = TriageEnv(SCENARIO)
    for k in range(10_000):
        env.reset(seed=seed + k)
        if env.cause == cause:
            return env
    raise AssertionError("cause never drawn")


def test_off_by_default_and_v2_unchanged():
    v2 = load_scenario(MODEL, V2)
    assert not v2.verify
    env = TriageEnv(v2)
    obs, _ = env.reset(seed=1)
    assert env.layout.n_fix_flags == 0 and len(env.layout.failed_fixes(obs)) == 0
    fix = env.n_checks + (env.cause + 1) % env.n_causes          # a wrong fix ends the episode
    _, reward, terminated, _, info = env.step(fix)
    assert terminated and info["outcome"] == "wrong" and reward == -v2.cost_wrong and info["wrong_fixes"] == 1


def test_harm_is_anchored_to_the_elicited_multiple():
    s = SCENARIO
    model = json.loads(MODEL.read_text(encoding="utf-8"))
    assert s.verify and s.max_failed_fixes == 2
    assert np.isclose(s.wrong_fix_harm.mean(), (model["costs"]["wrong_fix_multiple"] - 1) * s.cost_esc)
    assert (s.r_correct - s.fix_costs > -s.cost_esc).all()
    c = [c["id"] for c in model["causes"]]
    assert s.wrong_fix_harm[c.index("C07")] > s.wrong_fix_harm[c.index("C04")]   # deletes weigh more


def test_check_env_passes():
    check_env(TriageEnv(SCENARIO), skip_render_check=True)


def test_correct_fix_resolves_and_pays_the_apply_cost():
    env = env_with_cause(3)
    _, reward, terminated, _, info = env.step(env.n_checks + 3)
    assert terminated and info["outcome"] == "correct" and info["wrong_fixes"] == 0
    assert np.isclose(reward, SCENARIO.r_correct - SCENARIO.fix_costs[3])


def test_wrong_fix_continues_flags_and_masks():
    env = env_with_cause(3)
    obs, reward, terminated, _, _ = env.step(env.n_checks + 0)
    assert not terminated
    assert np.isclose(reward, -(SCENARIO.fix_costs[0] + SCENARIO.wrong_fix_harm[0]))
    assert env.layout.failed_fixes(obs).tolist() == [True] + [False] * (env.n_causes - 1)
    assert not env.action_masks()[env.n_checks + 0]
    _, reward, terminated, _, info = env.step(env.n_checks + 3)         # then the right one
    assert terminated and info["outcome"] == "correct" and info["wrong_fixes"] == 1


def test_second_failed_fix_hands_over_to_a_person():
    env = env_with_cause(3)
    env.step(env.n_checks + 0)
    _, reward, terminated, _, info = env.step(env.n_checks + 1)
    assert terminated and info["outcome"] == "fix_limit" and info["wrong_fixes"] == 2
    assert np.isclose(reward, -(SCENARIO.fix_costs[1] + SCENARIO.wrong_fix_harm[1] + SCENARIO.cost_esc))


def test_baselines_and_metrics_run_under_the_safety_mechanism():
    env = make_env(SCENARIO, "shielded", train=False)
    rows = run_episodes(Threshold(env, 0.65), env, 120)
    m = summarise(rows)
    assert m["executed_violation_rate"] == 0
    assert m["wrong_fix_rate"] >= m["wrong_rate"] == 0.0     # a wrong fix never ends the episode here
    assert np.isclose(m["resolution_accuracy"] + m["escalation_rate"], 1.0)
    esc = summarise(run_episodes(AlwaysEscalate(env), env, 50))
    assert esc["wrong_fix_rate"] == 0 and esc["escalation_rate"] == 1


def test_threshold_never_repeats_a_failed_fix():
    env = make_env(SCENARIO, "shielded", train=False)
    policy = Threshold(env, 0.3)
    base = env.unwrapped
    for k in range(60):
        obs, _ = env.reset(seed=k)
        done = False
        while not done:
            action = policy(obs, env.action_masks())
            if base.n_checks <= action < base.ESCALATE:     # a blocked fix was never applied, so only
                assert not base.failed[action - base.n_checks]   # applied-and-failed ones are ruled out
            obs, _, terminated, truncated, _ = env.step(action)
            done = terminated or truncated


def test_training_env_observation_includes_the_flags():
    env = make_env(SCENARIO, "shielded", train=True)
    obs, _ = env.reset(seed=0)
    base = env.unwrapped
    assert obs.shape[0] == base.observation_space.shape[0] + base.n_actions
    assert base.observation_space.shape[0] == TriageEnv(load_scenario(MODEL, V2)).observation_space.shape[0] + base.n_causes


def test_exact_solver_refuses_verification():
    with pytest.raises(ValueError, match="verification"):
        solve(TriageEnv(SCENARIO))


def test_bad_settings_are_rejected():
    model = json.loads(MODEL.read_text(encoding="utf-8"))
    settings = json.loads(V3.read_text(encoding="utf-8"))
    del settings["fix_with_verification"]["remedies"]["C01"]
    with pytest.raises(ValueError, match="C01"):
        build_scenario(model, settings)


def test_escalation_override_keeps_the_elicited_ratio():
    """Sensitivity analysis: the override changes escalation, and wrong fix stays 5x escalation."""
    base = load_scenario(MODEL, V3)
    for minutes in (60.0, 240.0):
        s = load_scenario(MODEL, V3, escalation_minutes=minutes)
        scale = minutes / 120.0
        assert s.cost_esc == pytest.approx(base.cost_esc * scale)
        assert s.cost_wrong / s.cost_esc == pytest.approx(base.cost_wrong / base.cost_esc)
        assert np.allclose(s.wrong_fix_harm, base.wrong_fix_harm * scale)
        assert np.allclose(s.fix_costs, base.fix_costs)
    assert json.loads(MODEL.read_text(encoding="utf-8"))["costs"]["escalation_minutes"] == 120.0
