import numpy as np
import gymnasium as gym
from gymnasium import spaces


class ToyTriageEnv(gym.Env):
    """Three hidden causes, two diagnostic checks, one escalate action."""

    metadata = {"render_modes": ["ansi"]}

    NOT_REQUESTED, NEGATIVE, POSITIVE = 0, 1, 2

    def __init__(self, r_correct=10.0, cost_wrong=10.0, cost_esc=3.0,
                 check_costs=(0.2, 0.5), max_steps=4, render_mode=None):
        # theta[i, j] = P(check i is positive | cause j)
        self.theta = np.array([[0.9, 0.1, 0.5],
                               [0.2, 0.8, 0.6]])
        self.prior = np.array([0.5, 0.3, 0.2])          # P(cause j)
        self.n_checks, self.n_causes = self.theta.shape
        self.r_correct, self.cost_wrong, self.cost_esc = r_correct, cost_wrong, cost_esc
        self.check_costs = np.asarray(check_costs)
        self.max_steps = max_steps
        self.render_mode = render_mode

        # Actions: [0, n_checks) run a check; [n_checks, n_checks + n_causes) recommend
        # the fix for a cause; the last action escalates.
        self.n_actions = self.n_checks + self.n_causes + 1
        self.ESCALATE = self.n_actions - 1
        self.action_space = spaces.Discrete(self.n_actions)
        # Observation: one-hot status of each check (3 values) + normalised step count.
        self.observation_space = spaces.Box(0.0, 1.0, shape=(3 * self.n_checks + 1,),
                                            dtype=np.float32)

    # ----- helpers -----------------------------------------------------------
    def _obs(self):
        obs = np.zeros(self.observation_space.shape, dtype=np.float32)
        for i, s in enumerate(self.status):
            obs[3 * i + s] = 1.0
        obs[-1] = self.t / self.max_steps
        return obs

    def action_masks(self):
        mask = np.ones(self.n_actions, dtype=bool)
        mask[:self.n_checks] = self.status == self.NOT_REQUESTED   # no repeated checks
        return mask

    # ----- Gymnasium API -----------------------------------------------------
    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)                           # seeds self.np_random
        self.cause = int(self.np_random.choice(self.n_causes, p=self.prior))
        # Draw every check result once, so a repeated check gives the same answer.
        self.results = self.np_random.random(self.n_checks) < self.theta[:, self.cause]
        self.status = np.full(self.n_checks, self.NOT_REQUESTED)
        self.t = 0
        return self._obs(), {"cause": self.cause}

    def step(self, action):
        action = int(action)
        self.t += 1
        terminated, info = False, {}

        if action < self.n_checks:                         # run a check
            self.status[action] = self.POSITIVE if self.results[action] else self.NEGATIVE
            reward = -float(self.check_costs[action])
        elif action < self.ESCALATE:                       # recommend a fix
            correct = (action - self.n_checks) == self.cause
            reward = self.r_correct if correct else -self.cost_wrong
            terminated, info["outcome"] = True, "correct" if correct else "wrong"
        else:                                              # escalate
            reward = -self.cost_esc
            terminated, info["outcome"] = True, "escalated"

        if not terminated and self.t >= self.max_steps:    # step limit = forced escalation
            reward -= self.cost_esc
            terminated, info["outcome"] = True, "step_limit"

        return self._obs(), reward, terminated, False, info

    def render(self):
        names = {0: "?", 1: "-", 2: "+"}
        return f"t={self.t} checks=[{' '.join(names[s] for s in self.status)}]"
