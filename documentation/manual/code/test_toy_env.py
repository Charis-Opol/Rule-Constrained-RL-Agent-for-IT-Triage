import numpy as np
from gymnasium.utils.env_checker import check_env
from toy_triage_env import ToyTriageEnv


def test_api():
    check_env(ToyTriageEnv())                  # spaces, dtypes, reset/step signatures, seeding


def test_same_seed_same_episode():
    a, b = ToyTriageEnv(), ToyTriageEnv()
    assert np.array_equal(a.reset(seed=7)[0], b.reset(seed=7)[0])
    assert a.cause == b.cause and np.array_equal(a.results, b.results)


def test_likelihoods_match_theta():
    env, n = ToyTriageEnv(), 20_000
    hits = np.zeros_like(env.theta)
    counts = np.zeros(env.n_causes)
    for k in range(n):
        env.reset(seed=k)
        hits[:, env.cause] += env.results
        counts[env.cause] += 1
    assert np.allclose(hits / counts, env.theta, atol=0.03)
    assert np.allclose(counts / n, env.prior, atol=0.02)


def test_reward_ordering():
    env = ToyTriageEnv()
    assert env.r_correct > -env.cost_esc > -env.cost_wrong


def test_episode_always_ends():
    env = ToyTriageEnv()
    env.reset(seed=0)
    for _ in range(env.max_steps):
        _, _, terminated, truncated, _ = env.step(0)   # keep running the same check
        if terminated or truncated:
            return
    raise AssertionError("episode did not end at the step limit")
