"""Baseline policies of Chapter 3 (Table 3.x). Each one is called with the observation and the
action mask only, plus the likelihood model where Chapter 3 gives it one. None can see the
hidden cause or an unrequested result.

Under the safety mechanism a blocked fix is masked for one step, and each policy simply
applies its own rule to the actions that remain. None of them knows the rules.
"""
import numpy as np

from src.agents.belief import information_gain, posterior


class Policy:
    name = "policy"

    def __init__(self, env):
        env = env.unwrapped
        self.layout = env.layout
        self.scenario = env.scenario
        self.reported_theta = env.reported_theta
        self.n_checks, self.n_causes, self.escalate = env.n_checks, env.n_causes, env.ESCALATE

    def belief(self, obs):
        status, symptoms, *_ = self.layout.decode(obs)
        return posterior(self.scenario, self.reported_theta, status, symptoms, self.layout.failed_fixes(obs))

    def best_fix(self, belief, mask):
        """The most probable cause whose fix is not masked, and its probability."""
        allowed = np.where(mask[self.n_checks:self.escalate], belief, -1.0)
        cause = int(allowed.argmax())
        return self.n_checks + cause, allowed[cause]


class AlwaysEscalate(Policy):
    name = "Always escalate"

    def __call__(self, obs, mask):
        return self.escalate


class SymptomsOnly(Policy):
    """Fixes the most probable cause from the initial symptoms, with no checks."""
    name = "Initial-symptom"

    def __call__(self, obs, mask):
        return self.best_fix(self.belief(obs), mask)[0]


class Scripted(Policy):
    """Runs a fixed sequence of checks, then fixes the most probable cause. No check
    order by category was elicited for the pilot, so the order is by expected information at
    the start of an incident, averaged over symptoms (Chapter 3 fallback)."""
    name = "Scripted"

    def __init__(self, env, n_checks_to_run):
        super().__init__(env)
        self.n_run = n_checks_to_run
        self.order = information_order(env.unwrapped)[:n_checks_to_run]

    def __call__(self, obs, mask):
        for check in self.order:
            if mask[check]:
                return int(check)
        return self.best_fix(self.belief(obs), mask)[0]


class Threshold(Policy):
    """Requests the most informative check while no permitted cause reaches the threshold,
    fixes when one does, and escalates when the checks run out."""
    name = "Threshold"

    def __init__(self, env, tau):
        super().__init__(env)
        self.tau = tau

    def __call__(self, obs, mask):
        belief = self.belief(obs)
        fix, probability = self.best_fix(belief, mask)
        if probability >= self.tau:
            return fix
        remaining = np.flatnonzero(mask[:self.n_checks])
        if len(remaining) == 0:
            return self.escalate
        return int(remaining[information_gain(belief, self.reported_theta)[remaining].argmax()])


def information_order(env):
    """Checks ordered by expected information about the cause, averaged over the initial symptoms."""
    s = env.scenario
    patterns = np.array([[(p >> i) & 1 for i in range(env.n_symptoms)] for p in range(2 ** env.n_symptoms)], bool)
    gain = np.zeros(env.n_checks)
    for symptoms in patterns:
        joint = s.prior * np.prod(np.where(symptoms[:, None], s.symptom_theta, 1 - s.symptom_theta), axis=0)
        gain += joint.sum() * information_gain(joint / joint.sum(), env.reported_theta)
    return np.argsort(-gain, kind="stable")
