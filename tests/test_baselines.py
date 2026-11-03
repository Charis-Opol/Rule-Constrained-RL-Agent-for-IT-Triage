"""Phase 3 gate: the exact policy scores its own value in the real environment, the baselines
behave as defined, and no policy beats what the evidence allows."""
import itertools
from pathlib import Path

import numpy as np
import pytest

from src.agents.baselines import AlwaysEscalate, Scripted, SymptomsOnly, Threshold
from src.agents.belief import information_gain, posterior
from src.agents.exact import ExactPolicy, solve
from src.evaluation import run_episodes, summarise
from src.rules.safety import RuleMonitor, SafetyMechanism
from src.sim.scenario import load_scenario
from src.sim.triage_env import TriageEnv

PILOT = Path(__file__).resolve().parents[1] / "experiments" / "pilot"
SCENARIO = load_scenario(PILOT / "pilot_model.json", PILOT / "pilot_settings.json")
N = 3000


def make(**kwargs):
    return SafetyMechanism(TriageEnv(SCENARIO, **kwargs))


@pytest.fixture(scope="module")
def exact():
    env = make()
    return env, solve(env)


# ----- Gate: exact policy ----------------------------------------------------
def test_exact_value_matches_the_pre_training_diagnostics(exact):
    _, solution = exact
    assert solution.value == pytest.approx(0.390, abs=0.002)
    assert solution.stats["correct"] == pytest.approx(0.612, abs=0.002)
    assert solution.stats["escalated"] == pytest.approx(0.215, abs=0.002)
    assert sum(solution.stats[k] for k in ("correct", "wrong", "escalated")) == pytest.approx(1.0)


def test_exact_policy_scores_its_value_in_the_real_environment(exact):
    env, solution = exact
    m = summarise(run_episodes(ExactPolicy(env, solution), env, 20_000))
    low, high = m["return_ci"]
    assert low <= solution.value <= high
    assert m["resolution_accuracy"] == pytest.approx(solution.stats["correct"], abs=0.012)
    assert m["wrong_rate"] == pytest.approx(solution.stats["wrong"], abs=0.012)
    assert m["mean_checks"] == pytest.approx(solution.stats["n_checks"], abs=0.05)
    assert m["proposed_violation_rate"] == 0.0           # it never proposes a prohibited fix


def test_exact_action_values_agree_with_the_solution(exact):
    env, solution = exact
    policy = ExactPolicy(env, solution)
    for k in range(300):
        obs, _ = env.reset(seed=k)
        done = False
        while not done:
            status, symptoms, context, *_ = env.unwrapped.layout.decode(obs)
            q = solution.q_values(status, symptoms, context)
            idx, ctx, pat = solution.index(status, symptoms, context)
            total = (solution.base[pat] * solution.likelihood[idx]).sum()
            assert np.nanmax(q) == pytest.approx(solution.V[idx, ctx, pat] / total)
            action = policy(obs, env.action_masks())
            assert q[action] == pytest.approx(np.nanmax(q))
            obs, _, done, *_ = env.step(action)


def test_exact_action_values_mark_unavailable_actions(exact):
    env, solution = exact
    obs, _ = env.reset(seed=0)
    env.unwrapped.context = np.array([0, 2])                 # production, high priority
    env.step(1)
    status, symptoms, context, *_ = env.unwrapped.layout.decode(env.unwrapped._obs())
    q = solution.q_values(status, symptoms, context)
    assert np.isnan(q[1])                                     # already run
    assert all(np.isnan(q[10 + c]) for c in (0, 1, 2, 5, 6))  # every rule active, no named check run
    assert not np.isnan(q[13]) and q[18] == -2.0


def test_exact_solver_refuses_missing_checks():
    with pytest.raises(ValueError):
        solve(make(p_miss=0.2))


# ----- Gate: simple references -----------------------------------------------
def test_always_escalate_scores_exactly_minus_two():
    env = make()
    rows = run_episodes(AlwaysEscalate(env), env, N)
    assert all(r["return"] == -2.0 for r in rows)
    m = summarise(rows)
    assert m["escalation_rate"] == 1.0 and m["escalation_recall"] == 1.0
    assert m["escalation_precision"] == pytest.approx(1 - m["ceiling"])


@pytest.mark.parametrize("p_miss", [0.0, 0.4])
def test_no_baseline_beats_the_ceiling_or_the_exact_return(exact, p_miss):
    env_exact, solution = exact
    env = make(p_miss=p_miss)
    for policy in (SymptomsOnly(env), Scripted(env, 4), Threshold(env, 0.7)):
        m = summarise(run_episodes(policy, env, N))
        se = np.sqrt(m["ceiling"] * (1 - m["ceiling"]) / N)
        assert m["resolution_accuracy"] <= m["ceiling"] + 3 * se, policy.name
        assert m["return_ci"][0] <= solution.value, policy.name
        assert m["executed_violation_rate"] == 0.0


# ----- Baselines behave as defined -------------------------------------------
def test_policies_see_only_the_observation():
    env = make()
    obs, _ = env.reset(seed=5)
    status, symptoms, context, t, blocked = env.unwrapped.layout.decode(obs)
    base = env.unwrapped
    assert np.array_equal(symptoms, base.symptoms) and np.array_equal(context, base.context)
    assert (t, blocked) == (0, False) and (status == base.NOT_REQUESTED).all()
    for policy in (SymptomsOnly(env), Scripted(env, 3), Threshold(env, 0.7)):
        assert not hasattr(policy, "env")


def test_posterior_matches_bayes_rule_by_hand():
    env = TriageEnv(SCENARIO)
    env.reset(seed=11)
    for i in (1, 4, 7):
        env.step(i)
    b = posterior(SCENARIO, env.reported_theta, env.status, env.symptoms)
    by_hand = []
    for j in range(env.n_causes):
        p = SCENARIO.prior[j]
        for i in range(env.n_symptoms):
            p *= SCENARIO.symptom_theta[i, j] if env.symptoms[i] else 1 - SCENARIO.symptom_theta[i, j]
        for i in (1, 4, 7):
            p *= env.reported_theta[i, j] if env.reported[i] else 1 - env.reported_theta[i, j]
        by_hand.append(p)
    assert np.allclose(b, np.array(by_hand) / sum(by_hand))


def test_information_gain_is_zero_for_a_useless_check_and_positive_otherwise():
    belief = np.full(4, 0.25)
    theta = np.array([[0.5, 0.5, 0.5, 0.5], [0.9, 0.9, 0.1, 0.1]])
    gain = information_gain(belief, theta)
    assert gain[0] == pytest.approx(0.0) and gain[1] > 0.4


def test_symptoms_only_never_runs_a_check():
    env = make(p_miss=0.2)
    m = summarise(run_episodes(SymptomsOnly(env), env, N))
    assert m["mean_checks"] == 0 and m["coverage"] + m["forced_escalation_rate"] == pytest.approx(1.0)


def test_threshold_zero_acts_like_symptoms_only():
    env = make()
    a = run_episodes(Threshold(env, 0.0), env, 500)
    b = run_episodes(SymptomsOnly(env), env, 500)
    assert a == b


def test_threshold_above_one_runs_every_check_then_escalates():
    env = make()
    m = summarise(run_episodes(Threshold(env, 1.01), env, 300))
    assert m["mean_checks"] == 10 and m["escalation_rate"] == 1.0


def test_scripted_zero_checks_acts_like_symptoms_only():
    env = make()
    assert run_episodes(Scripted(env, 0), env, 500) == run_episodes(SymptomsOnly(env), env, 500)


def test_scripted_with_every_check_reaches_the_ceiling():
    env = make()
    m = summarise(run_episodes(Scripted(env, 10), env, 5000))
    assert m["proposed_violation_rate"] == 0.0           # every named check has been observed
    assert m["resolution_accuracy"] == pytest.approx(m["ceiling"], abs=0.005)


def test_after_a_block_baselines_choose_a_different_action():
    env = make()
    for policy in (SymptomsOnly(env), Scripted(env, 0), Threshold(env, 0.0)):
        for k in range(200):
            obs, _ = env.reset(seed=k)
            mask = env.action_masks()
            first = policy(obs, mask)
            mask[first] = False
            assert policy(obs, mask) != first, policy.name


def test_baselines_do_not_know_the_rules():
    """A blocked baseline chooses again from what remains, so it can be blocked and forced."""
    env = make()
    m = summarise(run_episodes(SymptomsOnly(env), env, N))
    assert m["proposed_violation_rate"] > 0.2 and m["forced_escalation_rate"] > 0


# ----- Metrics ---------------------------------------------------------------
def row(outcome, should, ret=0.0, blocked=0, executed=0, proposals=1, n_checks=0):
    return {"return": ret, "outcome": outcome, "should_escalate": should, "n_checks": n_checks,
            "check_cost": 0.0, "proposals": proposals, "blocked": blocked, "executed_violations": executed}


def test_metrics_on_a_hand_worked_example():
    rows = [row("correct", False, 5, proposals=2, n_checks=1),
            row("correct", False, 5, executed=1),
            row("wrong", False, -10),
            row("wrong", True, -10),
            row("escalated", True, -2),
            row("forced_escalation", True, -2, blocked=2, proposals=2),
            row("escalated", False, -2),
            row("step_limit", False, -2)]
    m = summarise(rows)
    assert m["resolution_accuracy"] == 2 / 8 and m["wrong_rate"] == 2 / 8
    assert m["coverage"] == 4 / 8 and m["selective_accuracy"] == 2 / 4
    assert m["escalation_rate"] == 4 / 8 and m["forced_escalation_rate"] == 1 / 8
    # escalated & should: 2, escalated & not: 2, not escalated & should: 1, neither: 3
    assert m["escalation_precision"] == 2 / 4 and m["escalation_recall"] == 2 / 3
    assert m["escalation_f1"] == pytest.approx(2 * 0.5 * (2 / 3) / (0.5 + 2 / 3))
    assert m["escalation_mcc"] == pytest.approx((2 * 3 - 2 * 1) / np.sqrt(4 * 3 * 5 * 4))
    assert m["proposed_violation_rate"] == 3 / 10
    assert m["executed_violation_rate"] == 1 / 8 and m["compliant_success_rate"] == 1 / 8
    assert m["mean_return"] == pytest.approx(-18 / 8) and m["mean_checks"] == 1 / 8
    assert m["ceiling"] == 5 / 8


def test_undefined_ratios_are_not_numbers():
    m = summarise([row("escalated", False, -2)])
    assert np.isnan(m["selective_accuracy"]) and np.isnan(m["escalation_recall"])


def test_monitor_reports_executed_violations_as_proposed_violations():
    env = RuleMonitor(TriageEnv(SCENARIO))
    m = summarise(run_episodes(SymptomsOnly(env), env, N))
    assert m["executed_violation_rate"] > 0.2
    assert m["proposed_violation_rate"] == pytest.approx(m["executed_violation_rate"])
    assert m["compliant_success_rate"] < m["resolution_accuracy"]


def test_same_incidents_for_every_policy():
    env = make()
    causes = []
    for policy in (AlwaysEscalate(env), SymptomsOnly(env)):
        causes.append([run_episodes(policy, env, 1, first_seed=1_000_000 + k) and env.unwrapped.cause
                       for k in range(50)])
    assert causes[0] == causes[1]
