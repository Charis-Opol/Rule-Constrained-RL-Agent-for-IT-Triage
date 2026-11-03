"""Exact optimal policy by dynamic programming over every evidence state.

Feasible for the pilot only: 3^10 check states x 16 symptom patterns x 6 contexts. Missing
checks would add a fourth state per check, so the solver refuses p_miss > 0. The optimal
policy never proposes a prohibited fix (a block gains nothing), so prohibited fixes are
simply unavailable to it.
"""
import itertools
from dataclasses import dataclass

import numpy as np

from src.agents.baselines import Policy
from src.sim.triage_env import TriageEnv

STAT_NAMES = ("correct", "wrong", "escalated", "n_checks", "check_cost")


@dataclass
class ExactSolution:
    value: float                # expected return of an incident
    stats: dict                 # expected outcome shares, checks and cost
    actions: np.ndarray         # [check state, context, symptom pattern] -> action
    context_shape: tuple
    V: np.ndarray               # optimal value in joint-probability units, same index
    likelihood: np.ndarray      # [check state, cause]
    base: np.ndarray            # [symptom pattern, cause] = P(cause) P(symptoms | cause)
    env: object                 # the unwrapped environment it was solved for

    def index(self, status, symptoms, context):
        """State, context and symptom indices for an observation decoded by Layout."""
        digits = np.select([status == TriageEnv.NEGATIVE, status == TriageEnv.POSITIVE], [1, 2], 0)
        return (int(digits @ 3 ** np.arange(len(status))),
                int(np.ravel_multi_index(context, self.context_shape)),
                int(symptoms @ 2 ** np.arange(len(symptoms))))

    def q_values(self, status, symptoms, context):
        """Expected return from here of every action under optimal play afterwards, in reward
        units. NaN for an action that is not available: a check already run or a prohibited fix."""
        if (status == TriageEnv.UNAVAILABLE).any():
            raise ValueError("The exact solution does not handle unavailable checks")
        env, s = self.env, self.env.scenario
        idx, ctx, pat = self.index(status, symptoms, context)
        joint = self.base[pat] * self.likelihood[idx]
        total = joint.sum()
        q = np.full(env.n_actions, np.nan)
        for i in np.flatnonzero(status == TriageEnv.NOT_REQUESTED):
            step = 3 ** i
            q[i] = (-s.check_costs[i] * total + self.V[idx + step, ctx, pat] + self.V[idx + 2 * step, ctx, pat]) / total
        posterior = joint / total
        fix = posterior * s.r_correct - (1 - posterior) * s.cost_wrong
        for rule in s.rules:
            if rule.active(context) and (rule.unless_observed is None
                                         or status[rule.unless_observed] == TriageEnv.NOT_REQUESTED):
                fix[rule.cause] = np.nan
        q[env.n_checks:env.ESCALATE] = fix
        q[env.ESCALATE] = -s.cost_esc
        return q


def solve(env):
    env = env.unwrapped
    if env.p_miss > 0:
        raise ValueError("The exact solver does not model missing checks (p_miss must be 0)")
    s, theta = env.scenario, env.reported_theta
    n_checks, n_causes, n_symptoms = env.n_checks, env.n_causes, env.n_symptoms
    check_action, escalate = np.arange(n_checks), env.ESCALATE

    # Digit i of a state index is the status of check i: 0 not requested, 1 negative, 2 positive.
    digits = np.array(list(itertools.product((0, 1, 2), repeat=n_checks)), dtype=np.int8)[:, ::-1]
    pow3 = 3 ** np.arange(n_checks)
    n_states = 3 ** n_checks
    likelihood = np.ones((n_states, n_causes))
    for i in range(n_checks):
        d = digits[:, i, None]
        likelihood *= np.where(d == 2, theta[i], np.where(d == 1, 1 - theta[i], 1.0))

    patterns = np.array([[(p >> i) & 1 for i in range(n_symptoms)] for p in range(2 ** n_symptoms)], bool)
    base = s.prior * np.array([np.prod(np.where(p[:, None], s.symptom_theta, 1 - s.symptom_theta), axis=0)
                               for p in patterns])                                  # [patterns, causes]

    shape = tuple(len(v) for v in s.context_values)
    contexts = list(itertools.product(*[range(n) for n in shape]))
    p_context = np.array([np.prod([s.context_probs[a][v] for a, v in enumerate(c)]) for c in contexts])
    active = np.array([[rule.active(c) for c in contexts] for rule in s.rules], bool)   # [rules, contexts]

    n_ctx, n_pat = len(contexts), len(patterns)
    V = np.zeros((n_states, n_ctx, n_pat))
    stats = np.zeros((n_states, n_ctx, n_pat, len(STAT_NAMES)), dtype=np.float32)
    actions = np.zeros((n_states, n_ctx, n_pat), dtype=np.int8)

    for idx in range(n_states - 1, -1, -1):                 # children have larger indices
        d = digits[idx]
        joint = base * likelihood[idx]                      # P(evidence, cause) in joint units
        total = joint.sum(1)
        recommend = joint * s.r_correct - (total[:, None] - joint) * s.cost_wrong

        forbidden = np.zeros((n_ctx, n_causes), bool)
        for r, rule in enumerate(s.rules):
            if rule.unless_observed is None or d[rule.unless_observed] == 0:
                forbidden[active[r], rule.cause] = True
        q = np.where(forbidden[:, None, :], -np.inf, recommend[None])
        cause = q.argmax(2)
        q_fix = np.take_along_axis(q, cause[..., None], 2)[..., 0]
        q_esc = np.broadcast_to(-s.cost_esc * total, (n_ctx, n_pat))
        fix_better = q_fix > q_esc
        best = np.where(fix_better, q_fix, q_esc)
        act = np.where(fix_better, n_checks + cause, escalate)
        correct = np.take_along_axis(np.broadcast_to(joint, (n_ctx, n_pat, n_causes)), cause[..., None], 2)[..., 0]
        st = np.zeros((n_ctx, n_pat, len(STAT_NAMES)))
        st[..., 0] = np.where(fix_better, correct, 0)
        st[..., 1] = np.where(fix_better, total - correct, 0)
        st[..., 2] = np.where(fix_better, 0, total)

        for i in check_action[d == 0]:
            negative, positive = idx + pow3[i], idx + 2 * pow3[i]
            q_check = -s.check_costs[i] * total + V[negative] + V[positive]
            better = q_check > best + 1e-12                 # ties go to deciding now
            if better.any():
                best = np.where(better, q_check, best)
                act = np.where(better, i, act)
                child = stats[negative].astype(float) + stats[positive]
                child[..., 3] += total
                child[..., 4] += s.check_costs[i] * total
                st = np.where(better[..., None], child, st)
        V[idx], stats[idx], actions[idx] = best, st, act

    value = float(p_context @ V[0].sum(1))
    expected = p_context @ stats[0].astype(float).sum(1)
    return ExactSolution(value, dict(zip(STAT_NAMES, map(float, expected))), actions, shape,
                         V, likelihood, base, env)


class ExactPolicy(Policy):
    name = "Exact optimal"

    def __init__(self, env, solution=None):
        super().__init__(env)
        self.solution = solution or solve(env)

    def __call__(self, obs, mask):
        status, symptoms, context, *_ = self.layout.decode(obs)
        if (status == TriageEnv.UNAVAILABLE).any():
            raise ValueError("The exact policy does not handle unavailable checks")
        action = int(self.solution.actions[self.solution.index(status, symptoms, context)])
        return action if mask[action] else self.escalate
