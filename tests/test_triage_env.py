"""Phase 1 gate: the environment follows Chapter 3 and reproduces the pre-training checks."""
import itertools
from pathlib import Path

import numpy as np
import pytest
from gymnasium.utils.env_checker import check_env

from src.sim.scenario import load_scenario
from src.sim.triage_env import TriageEnv

PILOT = Path(__file__).resolve().parents[1] / "experiments" / "pilot"
SCENARIO = load_scenario(PILOT / "pilot_model.json", PILOT / "pilot_settings.json")
N = 20_000


def make(**kwargs):
    return TriageEnv(SCENARIO, **kwargs)


def decode(env, obs):
    """Reads check results and symptoms from the observation alone."""
    status = obs[:4 * env.n_checks].reshape(-1, 4).argmax(1)
    at = 4 * env.n_checks
    symptoms = obs[at:at + 3 * env.n_symptoms].reshape(-1, 3).argmax(1)
    return status, symptoms


def most_probable_from_obs(env, obs):
    """The Bayes decision, using nothing but the observation and the likelihood model."""
    s = env.scenario
    status, symptoms = decode(env, obs)
    belief = s.prior * np.prod(np.where((symptoms == 0)[:, None], s.symptom_theta, 1 - s.symptom_theta), axis=0)
    for i, value in enumerate(status):
        if value == env.POSITIVE:
            belief = belief * env.reported_theta[i]
        elif value == env.NEGATIVE:
            belief = belief * (1 - env.reported_theta[i])
    return int(belief.argmax())


def run_all_checks_then_fix(env, n=N):
    outcomes, labelled, agree = [], [], 0
    for k in range(n):
        obs, _ = env.reset(seed=k)
        for i in range(env.n_checks):
            obs, *_ = env.step(i)
        obs, _, done, _, info = env.step(env.n_checks + most_probable_from_obs(env, obs))
        assert done
        outcomes.append(info["outcome"])
        labelled.append(info["should_escalate"])
        agree += (info["outcome"] == "correct") != info["should_escalate"]
    return np.mean(np.array(outcomes) == "correct"), np.mean(labelled), agree / n


def exact_ceiling(noise):
    s = SCENARIO
    theta = s.theta * (1 - noise) + (1 - s.theta) * noise
    both = np.vstack([s.symptom_theta, theta])
    total = 0.0
    for bits in itertools.product((False, True), repeat=both.shape[0]):
        total += (s.prior * np.prod(np.where(np.array(bits)[:, None], both, 1 - both), axis=0)).max()
    return total


# ----- Gate ------------------------------------------------------------------
def test_gymnasium_api():
    check_env(make(), skip_render_check=True)


def test_same_seed_same_incident():
    a, b = make(p_miss=0.3), make(p_miss=0.3)
    assert np.array_equal(a.reset(seed=7)[0], b.reset(seed=7)[0])
    assert a.cause == b.cause
    for name in ("context", "symptoms", "reported", "available"):
        assert np.array_equal(getattr(a, name), getattr(b, name))


def test_incident_does_not_depend_on_what_the_policy_does():
    a, b = make(), make()
    a.reset(seed=3), b.reset(seed=3)
    a.step(0), a.step(1)
    reported = a.reported.copy()
    a.reset(seed=4), b.reset(seed=4)
    assert np.array_equal(a.reported, b.reported)
    b.reset(seed=3)
    assert np.array_equal(b.reported, reported)


@pytest.mark.parametrize("noise,expected", [(0.0, 0.818), (0.1, 0.717)])
def test_most_probable_cause_after_all_checks_reaches_the_ceiling(noise, expected):
    assert exact_ceiling(noise) == pytest.approx(expected, abs=0.001)
    accuracy, labelled, agree = run_all_checks_then_fix(make(p_noise=noise))
    assert accuracy == pytest.approx(expected, abs=0.012)
    assert labelled == pytest.approx(1 - expected, abs=0.012)
    assert agree > 0.995             # with no missing checks the label is exactly this mistake


def test_simulated_rates_match_the_ratings():
    env = make(p_noise=0.0)
    s = env.scenario
    counts = np.zeros(env.n_causes)
    checks, symptoms = np.zeros_like(s.theta), np.zeros_like(s.symptom_theta)
    context = [np.zeros(len(p)) for p in s.context_probs]
    for k in range(N):
        env.reset(seed=k)
        counts[env.cause] += 1
        checks[:, env.cause] += env.reported
        symptoms[:, env.cause] += env.symptoms
        for a, value in enumerate(env.context):
            context[a][value] += 1
    assert np.allclose(counts / N, s.prior, atol=0.012)
    # The rarest causes have about 900 incidents, so allow about three standard errors.
    assert np.allclose(checks / counts, s.theta, atol=0.05)
    assert np.allclose(symptoms / counts, s.symptom_theta, atol=0.05)
    for tally, p in zip(context, s.context_probs):
        assert np.allclose(tally / N, p, atol=0.012)


def test_noise_reverses_results_at_the_set_rate():
    env = make(p_noise=0.2)
    positive = np.zeros((N, env.n_checks))
    causes = np.zeros(N, dtype=int)
    for k in range(N):
        env.reset(seed=k)
        positive[k], causes[k] = env.reported, env.cause
    for j in range(env.n_causes):
        assert np.allclose(positive[causes == j].mean(0), env.reported_theta[:, j], atol=0.06)


def test_missing_checks_at_the_set_rate():
    env = make(p_miss=0.4)
    share = np.mean([~env.available for k in range(5000) if env.reset(seed=k)], axis=0)
    assert np.allclose(share, 0.4, atol=0.03)


def test_labels_with_missing_checks_match_the_earlier_estimate():
    accuracy, labelled, _ = run_all_checks_then_fix(make(p_noise=0.1, p_miss=0.2))
    assert accuracy == pytest.approx(0.684, abs=0.015)
    assert labelled == pytest.approx(0.371, abs=0.015)


# ----- Observation -----------------------------------------------------------
def test_observation_has_58_inputs_and_starts_clean():
    env = make()
    obs, info = env.reset(seed=0)
    assert env.observation_space.shape == (58,) and env.n_actions == 19
    status, _ = decode(env, obs)
    assert (status == env.NOT_REQUESTED).all()
    assert obs[-1] == 0 and obs[-2] == 0
    assert info == {}                # nothing about the cause at reset


def test_observation_does_not_reveal_the_cause():
    """Incidents with the same symptoms and context look identical, whatever their cause."""
    env = make()
    seen = {}
    for k in range(3000):
        obs, _ = env.reset(seed=k)
        key = (tuple(env.symptoms), tuple(env.context))
        seen.setdefault(key, (obs, set()))
        assert np.array_equal(seen[key][0], obs)
        seen[key][1].add(env.cause)
    assert max(len(causes) for _, causes in seen.values()) > 1


def test_context_is_encoded_as_in_chapter_3():
    env = make()
    production, priority = [], []
    for k in range(200):
        obs, _ = env.reset(seed=k)
        at = 4 * env.n_checks + 3 * env.n_symptoms
        assert obs[at] == float(env.context[0] == 0)
        assert obs[at + 1:at + 4].sum() == 1 and obs[at + 1 + env.context[1]] == 1
        production.append(env.context[0]), priority.append(env.context[1])
    assert set(production) == {0, 1} and set(priority) == {0, 1, 2}


# ----- Actions and rewards ---------------------------------------------------
def test_check_returns_its_result_and_cost():
    env = make(p_noise=0.0)
    env.reset(seed=1)
    obs, reward, done, truncated, info = env.step(5)     # D06 is High effort
    assert reward == pytest.approx(-0.5) and not done and not truncated and info == {}
    expected = env.POSITIVE if env.reported[5] else env.NEGATIVE
    assert decode(env, obs)[0][5] == expected and env.observed(5)
    assert not env.action_masks()[5] and env.action_masks()[6]


def test_repeating_a_check_cannot_change_its_result():
    env = make(p_noise=0.3)
    env.reset(seed=2)
    first = env.step(0)[0][:4]
    assert np.array_equal(env.step(0)[0][:4], first)


def test_unavailable_check_is_charged_and_not_observed():
    env = make(p_miss=1.0)
    env.reset(seed=1)
    obs, reward, *_ = env.step(0)
    assert decode(env, obs)[0][0] == env.UNAVAILABLE
    assert reward == pytest.approx(-5 / 60)
    assert not env.observed(0) and not env.action_masks()[0]


def test_outcomes_and_rewards():
    env = make()
    env.reset(seed=0)
    correct = env.n_checks + env.cause
    *_, reward, done, _, info = env.step(correct)
    assert (reward, done, info["outcome"]) == (5.0, True, "correct")

    env.reset(seed=0)
    wrong = env.n_checks + (env.cause + 1) % env.n_causes
    *_, reward, done, _, info = env.step(wrong)
    assert (reward, done, info["outcome"]) == (-10.0, True, "wrong")

    env.reset(seed=0)
    *_, reward, done, _, info = env.step(env.ESCALATE)
    assert (reward, done, info["outcome"]) == (-2.0, True, "escalated")


def test_outcome_log_counts_checks_and_cost():
    env = make()
    env.reset(seed=0)
    env.step(0), env.step(4)                             # Low and Medium effort
    info = env.step(env.ESCALATE)[-1]
    assert info["n_checks"] == 2 and info["check_cost"] == pytest.approx(20 / 60)
    assert info["cause"] == env.cause


def test_all_checks_fit_within_the_step_limit():
    env = make()
    env.reset(seed=0)
    for i in range(env.n_checks):
        assert not env.step(i)[2]
    assert not env.block(env.n_checks)[2]                # one block still leaves room to decide
    assert env.step(env.ESCALATE)[-1]["outcome"] == "escalated"


def test_step_limit_ends_as_an_escalation():
    env = make()
    env.reset(seed=0)
    for k in range(env.max_steps - 1):
        assert not env.step(0)[2]
    _, reward, done, truncated, info = env.step(0)
    assert done and not truncated and info["outcome"] == "step_limit"
    assert reward == pytest.approx(-5 / 60 - 2.0)


# ----- Hooks for the safety mechanism ----------------------------------------
def test_block_uses_a_step_gives_no_reward_and_masks_the_action():
    env = make()
    env.reset(seed=0)
    proposal = env.n_checks
    obs, reward, done, *_ = env.block(proposal)
    assert reward == 0.0 and not done and env.t == 1
    assert obs[-1] == 1 and not env.action_masks()[proposal]
    obs = env.step(0)[0]                                 # the block lasts for one step only
    assert obs[-1] == 0 and env.action_masks()[proposal]


def test_escalation_is_never_masked():
    env = make()
    env.reset(seed=0)
    for i in range(env.n_checks):
        assert env.action_masks()[env.ESCALATE]
        env.step(i)
    assert env.action_masks()[env.ESCALATE]


# ----- Reference labels ------------------------------------------------------
def test_rule_label_needs_the_rule_active_and_its_check_unavailable():
    env = make(p_miss=1.0)
    rule_cases, other_cases = 0, 0
    for k in range(3000):
        env.reset(seed=k)
        active = [r for r in env.scenario.rules
                  if r.cause == env.cause and env.context[r.attribute] == r.value]
        if active:
            assert env.escalate_reason == "rule"
            rule_cases += 1
        else:
            assert env.escalate_reason != "rule"
            other_cases += 1
    assert rule_cases and other_cases


def test_no_rule_label_when_no_check_is_missing():
    env = make(p_miss=0.0)
    reasons = set()
    for k in range(3000):
        env.reset(seed=k)
        reasons.add(env.escalate_reason)
    assert reasons == {None, "ambiguous"}


# ----- Sanity runs -----------------------------------------------------------
def test_oracle_that_knows_the_cause_always_scores_the_correct_reward():
    env = make(p_miss=0.2)
    for k in range(500):
        env.reset(seed=k)
        _, reward, done, _, info = env.step(env.n_checks + env.cause)
        assert done and reward == 5.0 and info["outcome"] == "correct"


def test_random_policy_runs_cleanly_and_scores_poorly():
    env = make(p_miss=0.2)
    env.action_space.seed(0)
    returns, outcomes = [], set()
    for k in range(3000):
        env.reset(seed=k)
        total, done = 0.0, False
        while not done:
            action = env.action_space.sample(mask=env.action_masks().astype(np.int8))
            _, reward, done, truncated, info = env.step(action)
            assert not truncated
            total += reward
        returns.append(total)
        outcomes.add(info["outcome"])
    assert outcomes == {"correct", "wrong", "escalated"}
    assert np.mean(returns) < -2.0                       # worse than always escalating


def test_settings_reach_the_environment():
    s = SCENARIO
    assert (s.r_correct, s.cost_esc, s.cost_wrong) == (5.0, 2.0, 10.0)
    assert (s.p_noise, s.p_miss, s.max_steps) == (0.1, 0.0, 12)
    assert np.allclose(s.prior, np.array([2, 4, 1, 4, 1, 2, 4, 4]) / 22)
    assert np.allclose(s.check_costs * 60, [5, 5, 5, 5, 15, 30, 15, 5, 5, 15])
    assert (s.prior.sum(), s.theta.shape, s.symptom_theta.shape) == (pytest.approx(1.0), (10, 8), (4, 8))
