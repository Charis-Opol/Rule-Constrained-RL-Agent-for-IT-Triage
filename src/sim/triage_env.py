from dataclasses import dataclass

import numpy as np
import gymnasium as gym
from gymnasium import spaces


@dataclass(frozen=True)
class Layout:
    """Where each part of the evidence vector sits, so a policy can read an observation
    without access to the environment."""
    n_checks: int
    n_symptoms: int
    context_sizes: tuple
    max_steps: int

    def decode(self, obs):
        status = obs[:4 * self.n_checks].reshape(-1, 4).argmax(1)
        at = 4 * self.n_checks
        symptoms = obs[at:at + 3 * self.n_symptoms].reshape(-1, 3).argmax(1) == 0
        at += 3 * self.n_symptoms
        context = []
        for size in self.context_sizes:
            context.append(int(obs[at] == 0) if size == 1 else int(obs[at:at + size].argmax()))
            at += size
        return status, symptoms, np.array(context), round(float(obs[at]) * self.max_steps), bool(obs[at + 1])


class TriageEnv(gym.Env):
    """One episode is one incident. The cause is hidden; the agent runs checks, then
    recommends a fix or escalates. Everything about the incident is drawn at reset, so
    the same seed gives every policy the same incident.

    The safety mechanism is separate (src/rules). It uses `block` to consume a step and
    tell the agent that a proposal was refused.
    """

    metadata = {"render_modes": ["ansi"]}

    NOT_REQUESTED, UNAVAILABLE, NEGATIVE, POSITIVE = 0, 1, 2, 3

    def __init__(self, scenario, p_noise=None, p_miss=None, render_mode=None):
        self.scenario = scenario
        self.p_noise = scenario.p_noise if p_noise is None else p_noise
        self.p_miss = scenario.p_miss if p_miss is None else p_miss
        self.n_checks, self.n_causes = scenario.n_checks, scenario.n_causes
        self.n_symptoms = scenario.n_symptoms
        self.max_steps = scenario.max_steps
        self.render_mode = render_mode
        # P(reported positive | cause) once results can be reversed
        self.reported_theta = scenario.theta * (1 - self.p_noise) + (1 - scenario.theta) * self.p_noise

        # Actions: [0, n_checks) run a check; [n_checks, n_checks + n_causes) recommend
        # the fix for a cause; the last action escalates.
        self.n_actions = self.n_checks + self.n_causes + 1
        self.ESCALATE = self.n_actions - 1
        self.action_space = spaces.Discrete(self.n_actions)

        # Observation: one-hot check status (4 values) and symptom (present, absent, not
        # reported), context (one number if two-valued, otherwise one-hot), scaled step
        # count and blocked flag.
        self.context_sizes = [1 if len(v) == 2 else len(v) for v in scenario.context_values]
        size = 4 * self.n_checks + 3 * self.n_symptoms + sum(self.context_sizes) + 2
        self.observation_space = spaces.Box(0.0, 1.0, shape=(size,), dtype=np.float32)
        self.layout = Layout(self.n_checks, self.n_symptoms, tuple(self.context_sizes), self.max_steps)

    # ----- helpers -----------------------------------------------------------
    def _obs(self):
        obs = np.zeros(self.observation_space.shape, dtype=np.float32)
        obs[np.arange(self.n_checks) * 4 + self.status] = 1.0
        at = 4 * self.n_checks
        # All symptoms are revealed at the first step, so "not reported" stays unused.
        obs[at + np.arange(self.n_symptoms) * 3 + np.where(self.symptoms, 0, 1)] = 1.0
        at += 3 * self.n_symptoms
        for size, value in zip(self.context_sizes, self.context):
            if size == 1:
                obs[at] = float(value == 0)    # the first listed value, e.g. Yes
            else:
                obs[at + value] = 1.0
            at += size
        obs[at] = self.t / self.max_steps
        obs[at + 1] = float(self.blocked_action is not None)
        return obs

    def _reference_label(self):
        """Evaluation only, never shown to the agent. Should this incident be escalated?"""
        s = self.scenario
        for rule in s.rules:
            if (rule.cause == self.cause and rule.active(self.context)
                    and (rule.unless_observed is None or not self.available[rule.unless_observed])):
                return "rule"
        belief = s.prior * np.prod(np.where(self.symptoms[:, None], s.symptom_theta, 1 - s.symptom_theta), axis=0)
        likelihood = np.where(self.reported[:, None], self.reported_theta, 1 - self.reported_theta)
        belief = belief * np.prod(likelihood[self.available], axis=0)
        return "ambiguous" if belief.argmax() != self.cause else None

    def _info(self, outcome):
        return {"outcome": outcome, "cause": self.cause, "should_escalate": self.escalate_reason is not None,
                "escalate_reason": self.escalate_reason, "n_checks": self.n_requested, "check_cost": self.cost_spent}

    def observed(self, check):
        """A check is observed once it has returned a result. Unavailable does not count."""
        return self.status[check] in (self.NEGATIVE, self.POSITIVE)

    def action_masks(self):
        mask = np.ones(self.n_actions, dtype=bool)
        mask[:self.n_checks] = self.status == self.NOT_REQUESTED   # no repeated checks
        if self.blocked_action is not None:
            mask[self.blocked_action] = False
        return mask

    def block(self, action):
        """A refused proposal: uses a step, gives no reward, and masks that action next step."""
        self.t += 1
        self.blocked_action = int(action)
        if self.t >= self.max_steps:
            return self._end_at_step_limit()
        return self._obs(), 0.0, False, False, {}

    def force_escalation(self):
        """A second refused proposal in a row: the incident goes to the human expert."""
        self.t += 1
        self.blocked_action = None
        return self._obs(), -self.scenario.cost_esc, True, False, self._info("forced_escalation")

    def _end_at_step_limit(self):
        self.blocked_action = None
        return self._obs(), -self.scenario.cost_esc, True, False, self._info("step_limit")

    # ----- Gymnasium API -----------------------------------------------------
    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)                           # seeds self.np_random
        s, rng = self.scenario, self.np_random
        self.cause = int(rng.choice(self.n_causes, p=s.prior))
        self.context = np.array([rng.choice(len(p), p=p) for p in s.context_probs])
        self.symptoms = rng.random(self.n_symptoms) < s.symptom_theta[:, self.cause]
        # Each result is drawn once, so it cannot change during the incident.
        true_results = rng.random(self.n_checks) < s.theta[:, self.cause]
        self.reported = true_results ^ (rng.random(self.n_checks) < self.p_noise)
        self.available = rng.random(self.n_checks) >= self.p_miss
        self.escalate_reason = self._reference_label()

        self.status = np.full(self.n_checks, self.NOT_REQUESTED)
        self.t = self.n_requested = 0
        self.cost_spent = 0.0
        self.blocked_action = None
        return self._obs(), {}

    def step(self, action):
        action = int(action)
        s = self.scenario
        self.t += 1
        self.blocked_action = None
        terminated, info = False, {}

        if action < self.n_checks:                         # run a check
            if not self.available[action]:
                self.status[action] = self.UNAVAILABLE
            else:
                self.status[action] = self.POSITIVE if self.reported[action] else self.NEGATIVE
            self.n_requested += 1
            self.cost_spent += float(s.check_costs[action])
            reward = -float(s.check_costs[action])
        elif action < self.ESCALATE:                       # recommend a fix
            correct = (action - self.n_checks) == self.cause
            reward = s.r_correct if correct else -s.cost_wrong
            terminated, info = True, self._info("correct" if correct else "wrong")
        else:                                              # escalate
            reward = -s.cost_esc
            terminated, info = True, self._info("escalated")

        if not terminated and self.t >= self.max_steps:    # step limit = forced escalation
            obs, penalty, terminated, truncated, info = self._end_at_step_limit()
            return obs, reward + penalty, terminated, truncated, info

        return self._obs(), reward, terminated, False, info

    def render(self):
        names = {self.NOT_REQUESTED: "?", self.UNAVAILABLE: "x", self.NEGATIVE: "-", self.POSITIVE: "+"}
        return f"t={self.t} checks=[{' '.join(names[int(s)] for s in self.status)}]"
