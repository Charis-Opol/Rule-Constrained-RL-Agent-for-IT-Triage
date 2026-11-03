"""Runs a policy on a fixed set of incidents and computes the Chapter 3 measures.

Seed ranges are kept apart: training uses seeds below 1,000,000, evaluation starts at
EVAL_SEED and tuning at TUNE_SEED, so no policy is tuned or trained on its test incidents.
"""
import numpy as np

EVAL_SEED = 1_000_000
TUNE_SEED = 2_000_000
ESCALATED = ("escalated", "forced_escalation", "step_limit")


def run_episodes(policy, env, n, first_seed=EVAL_SEED):
    """One row per incident. `env` should already carry the safety mechanism or the monitor."""
    rows = []
    for k in range(n):
        obs, _ = env.reset(seed=first_seed + k)
        total, done = 0.0, False
        while not done:
            obs, reward, terminated, truncated, info = env.step(policy(obs, env.action_masks()))
            total += reward
            done = terminated or truncated
        rows.append({"return": total, "outcome": info["outcome"], "should_escalate": info["should_escalate"],
                     "n_checks": info["n_checks"], "check_cost": info["check_cost"],
                     "proposals": info["proposals"], "blocked": info["blocked"],
                     "executed_violations": info["executed_violations"]})
    return rows


def _ratio(a, b):
    return a / b if b else float("nan")


def bootstrap_ci(values, n_boot=2000, seed=0):
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    means = values[rng.integers(0, len(values), size=(n_boot, len(values)))].mean(1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def summarise(rows):
    n = len(rows)
    outcome = np.array([r["outcome"] for r in rows])
    correct, wrong = outcome == "correct", outcome == "wrong"
    escalated = np.isin(outcome, ESCALATED)
    should = np.array([r["should_escalate"] for r in rows])
    returns = np.array([r["return"] for r in rows])
    executed = np.array([r["executed_violations"] for r in rows])
    proposals = sum(r["proposals"] for r in rows)
    proposed_violations = sum(r["blocked"] + r["executed_violations"] for r in rows)

    tp, fp = int((escalated & should).sum()), int((escalated & ~should).sum())
    fn, tn = int((~escalated & should).sum()), int((~escalated & ~should).sum())
    precision, recall = _ratio(tp, tp + fp), _ratio(tp, tp + fn)
    mcc_den = np.sqrt(float(tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))

    return {
        "n": n,
        # Decision quality
        "mean_return": float(returns.mean()),
        "return_ci": bootstrap_ci(returns),
        "resolution_accuracy": float(correct.mean()),
        "resolution_ci": bootstrap_ci(correct),
        "coverage": float((correct | wrong).mean()),
        "selective_accuracy": _ratio(correct.sum(), (correct | wrong).sum()),
        "wrong_rate": float(wrong.mean()),
        # Investigation efficiency
        "mean_checks": float(np.mean([r["n_checks"] for r in rows])),
        "mean_check_cost": float(np.mean([r["check_cost"] for r in rows])),
        # Escalation behaviour
        "escalation_rate": float(escalated.mean()),
        "escalation_precision": precision,
        "escalation_recall": recall,
        "escalation_f1": _ratio(2 * precision * recall, precision + recall),
        "escalation_mcc": _ratio(tp * tn - fp * fn, mcc_den),
        # Constraint compliance
        "proposed_violation_rate": _ratio(proposed_violations, proposals),
        "forced_escalation_rate": float((outcome == "forced_escalation").mean()),
        "executed_violation_rate": float((executed > 0).mean()),
        "compliant_success_rate": float((correct & (executed == 0)).mean()),
        # Reference: no policy can resolve more incidents than are labelled resolvable
        "ceiling": float(1 - should.mean()),
    }
