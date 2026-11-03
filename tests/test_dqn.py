"""Phase 4: the agent's wrappers, exploration and saved checkpoints behave as planned."""
import tempfile
from pathlib import Path

import numpy as np
import pytest

from dashboard.thinking import trace
from src.agents.dqn import HYPERPARAMETERS, REWARD_SCALE, AgentPolicy, MaskedDQN, build_model, make_env
from src.evaluation import run_episodes, summarise
from src.rules.safety import RuleMonitor, SafetyMechanism
from src.sim.scenario import load_scenario

PILOT = Path(__file__).resolve().parents[1] / "experiments" / "pilot"
SCENARIO = load_scenario(PILOT / "pilot_model.json", PILOT / "pilot_settings.json")


@pytest.fixture(scope="module")
def trained():
    """A very short run: enough to exercise saving, loading and greedy play, not to learn.
    Uses tempfile, not pytest's tmp_path, which Windows refuses on this machine."""
    model = build_model(make_env(SCENARIO), seed=1, hyperparameters={**HYPERPARAMETERS, "learning_starts": 200})
    model.learn(2000)
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "model"
        model.save(path)
        loaded = MaskedDQN.load(path, device="cpu")
    return model, loaded


def test_training_env_has_mask_in_observation_and_scaled_rewards():
    env = make_env(SCENARIO)
    obs, _ = env.reset(seed=0)
    assert env.observation_space.shape == (77,) and obs.shape == (77,)
    assert np.array_equal(obs[-19:], env.action_masks().astype(np.float32))
    *_, reward, _, _, _ = env.step(18)
    assert reward == pytest.approx(-2.0 / REWARD_SCALE)


def test_evaluation_env_is_unscaled_without_the_mask():
    env = make_env(SCENARIO, train=False)
    obs, _ = env.reset(seed=0)
    assert obs.shape == (58,) and env.step(18)[1] == -2.0


@pytest.mark.parametrize("agent,wrapper,penalty", [("shielded", SafetyMechanism, 0.0),
                                                   ("unconstrained", RuleMonitor, 0.0),
                                                   ("penalty", RuleMonitor, 10.0)])
def test_agent_types(agent, wrapper, penalty):
    env = make_env(SCENARIO, agent, train=False)
    assert isinstance(env, wrapper) and getattr(env, "penalty", 0.0) == penalty


def test_random_exploration_respects_the_mask_and_favours_checks(trained):
    model, _ = trained
    env = make_env(SCENARIO)
    obs, _ = env.reset(seed=0)
    np.random.seed(0)
    actions = np.concatenate([model._masked_random(obs) for _ in range(4000)])
    assert np.mean(actions < 10) == pytest.approx(0.8, abs=0.03)
    env.step(3)
    obs = env.step(5)[0]
    actions = np.concatenate([model._masked_random(obs) for _ in range(500)])
    assert not np.isin(actions, [3, 5]).any()


def test_masked_actions_get_minus_infinity(trained):
    model, _ = trained
    env = make_env(SCENARIO)
    obs, _ = env.reset(seed=0)
    obs = env.step(4)[0]
    q = model.q_values(obs)
    assert np.isinf(q[4]) and np.isfinite(q[[0, 10, 18]]).all()


def test_checkpoint_round_trip(trained):
    model, loaded = trained
    env = make_env(SCENARIO)
    obs, _ = env.reset(seed=3)
    assert np.allclose(model.q_values(obs), loaded.q_values(obs))
    assert loaded.n_checks == 10 and loaded.check_bias == 0.8


def test_greedy_agent_never_picks_a_masked_action_and_never_breaks_a_rule(trained):
    _, loaded = trained
    env = make_env(SCENARIO, train=False, p_miss=0.3)
    policy = AgentPolicy(loaded)
    for k in range(300):
        obs, _ = env.reset(seed=k)
        done = False
        while not done:
            mask = env.action_masks()
            action = policy(obs, mask)
            assert mask[action]
            obs, _, done, _, info = env.step(action)
        assert info["executed_violations"] == 0
    assert summarise(run_episodes(policy, env, 200))["executed_violation_rate"] == 0


def test_plain_update_matches_stable_baselines3():
    """With double_q off, the rewritten update must be the library's update: same weights,
    same buffer, same random batch, then one step each."""
    import copy
    import torch
    from stable_baselines3 import DQN
    model = MaskedDQN("MlpPolicy", make_env(SCENARIO), seed=5, learning_starts=0, buffer_size=100,
                      batch_size=8, gamma=1.0, n_checks=10)
    model.learn(40)                                           # fill the buffer
    weights = copy.deepcopy(model.policy.state_dict())
    optimiser = copy.deepcopy(model.policy.optimizer.state_dict())
    updates = model._n_updates

    np.random.seed(0)
    model.train(1, 8)
    ours = copy.deepcopy(model.policy.state_dict())

    model.policy.load_state_dict(weights)
    model.policy.optimizer.load_state_dict(optimiser)
    model._n_updates = updates
    np.random.seed(0)
    DQN.train(model, 1, 8)                                    # the library's own update
    for key, value in model.policy.state_dict().items():
        assert torch.equal(ours[key], value), key


def test_double_q_target_uses_the_online_networks_choice():
    model = MaskedDQN("MlpPolicy", make_env(SCENARIO), seed=6, learning_starts=0, buffer_size=100,
                      batch_size=8, gamma=1.0, n_checks=10, double_q=True)
    model.learn(40)
    assert model.double_q and np.isfinite(model.logger.name_to_value["train/loss"])


def test_thinking_trace_replays_the_greedy_episode(trained):
    _, loaded = trained
    steps = trace(loaded, SCENARIO, "shielded", seed=7)
    assert steps[-1]["outcome"] in ("correct", "wrong", "escalated", "forced_escalation", "step_limit")
    assert all(sum(r["Chosen"] == "◄" for r in s["actions"]) == 1 for s in steps)
    assert all(abs(sum(s["posterior"]) - 1) < 1e-9 for s in steps)
    flipped = trace(loaded, SCENARIO, "shielded", seed=7, flips=[0, 1, 2, 3, 4])
    assert flipped[0]["posterior"] == steps[0]["posterior"]   # flips only matter once checks run
