"""The rule-based safety mechanism. It is separate from the agent and from the environment's
incident model, and every rule comes from the scenario configuration.

SafetyMechanism enforces the rules by review-then-escalate (Chapter 3). RuleMonitor applies
no enforcement and only records violations, for the unconstrained and penalty-only agents.
"""
import gymnasium as gym


class RuleChecker:
    def __init__(self, scenario):
        self.rules = scenario.rules
        self.n_checks, self.n_causes = scenario.n_checks, scenario.n_causes

    def forbidding(self, action, context, observed):
        """The rules that prohibit this action now. Only fixes can be prohibited, so a
        check or an escalation is always allowed."""
        cause = action - self.n_checks
        if not 0 <= cause < self.n_causes:
            return []
        return [rule for rule in self.rules
                if rule.cause == cause and rule.active(context)
                and (rule.unless_observed is None or not observed(rule.unless_observed))]


class _RuleWrapper(gym.Wrapper):
    def __init__(self, env):
        super().__init__(env)
        self.checker = RuleChecker(env.unwrapped.scenario)

    def reset(self, **kwargs):
        self.proposals = self.blocked = self.executed_violations = 0
        self.broken_rules = []
        return self.env.reset(**kwargs)

    def action_masks(self):
        return self.env.unwrapped.action_masks()

    def _forbidding(self, action):
        base = self.env.unwrapped
        return self.checker.forbidding(int(action), base.context, base.observed)

    def _log(self, result):
        obs, reward, terminated, truncated, info = result
        if terminated or truncated:
            info = {**info, "proposals": self.proposals, "blocked": self.blocked,
                    "executed_violations": self.executed_violations, "broken_rules": self.broken_rules}
        return obs, reward, terminated, truncated, info


class SafetyMechanism(_RuleWrapper):
    """A permitted proposal passes unchanged. The first refusal uses a step with no reward,
    sets the blocked flag and masks that action for the next step. A second refusal in a row
    escalates the incident. No prohibited action ever reaches the environment."""

    def step(self, action):
        self.proposals += 1
        base = self.env.unwrapped
        rules = self._forbidding(action)
        if not rules:
            return self._log(self.env.step(action))

        self.blocked += 1
        self.broken_rules += [rule.id for rule in rules]
        if base.blocked_action is not None:
            return self._log(base.force_escalation())
        return self._log(base.block(action))


class RuleMonitor(_RuleWrapper):
    """Lets every proposal through and records the violations. `penalty` is subtracted from
    the reward for each one, which gives the penalty-only agent."""

    def __init__(self, env, penalty=0.0):
        super().__init__(env)
        self.penalty = penalty

    def step(self, action):
        self.proposals += 1
        rules = self._forbidding(action)
        if rules:
            self.executed_violations += 1
            self.broken_rules += [rule.id for rule in rules]
        obs, reward, terminated, truncated, info = self.env.step(action)
        reward -= self.penalty * bool(rules)
        return self._log((obs, reward, terminated, truncated, info))
