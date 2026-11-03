"""Posterior over causes from what has been observed. Used by the baselines that are given
the likelihood model; the learning agent never sees it."""
import numpy as np

from src.sim.triage_env import TriageEnv


def posterior(scenario, reported_theta, status, symptoms):
    belief = scenario.prior * np.prod(
        np.where(symptoms[:, None], scenario.symptom_theta, 1 - scenario.symptom_theta), axis=0)
    belief = belief * np.prod(reported_theta[status == TriageEnv.POSITIVE], axis=0)
    belief = belief * np.prod(1 - reported_theta[status == TriageEnv.NEGATIVE], axis=0)
    return belief / belief.sum()


def entropy(p):
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def information_gain(belief, reported_theta):
    """Expected fall in entropy (bits) from the result of each check."""
    p_positive = reported_theta @ belief
    gain = np.empty(len(reported_theta))
    for i, (theta, p) in enumerate(zip(reported_theta, p_positive)):
        after_positive = belief * theta / p if p > 0 else belief
        after_negative = belief * (1 - theta) / (1 - p) if p < 1 else belief
        gain[i] = entropy(belief) - p * entropy(after_positive) - (1 - p) * entropy(after_negative)
    return gain
