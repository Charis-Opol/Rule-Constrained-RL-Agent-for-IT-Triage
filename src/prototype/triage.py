"""Runs the trained agent, with the safety mechanism, on one real incident.

LiveTriageEnv is the simulator with the random incident replaced by a Reading: the symptoms
and context come from the ticket, and a check's result is looked up only when the agent asks
for it (from the logs, or from the operator). The cause is unknown, so there is no reward and
no right or wrong outcome. The agent, its observation and the safety mechanism are exactly the
ones used in training and evaluation.

The prototype only recommends. It never applies a fix.
"""
import numpy as np

from src.agents.belief import posterior
from src.agents.dqn import MaskedDQN
from src.prototype.reading import NEGATIVE, POSITIVE, PRESENT, Finding
from src.rules.safety import RuleChecker, SafetyMechanism
from src.sim.triage_env import TriageEnv


class LiveTriageEnv(TriageEnv):
    def __init__(self, scenario, lookup):
        """`lookup(check)` returns True (positive), False (negative) or None (unavailable)."""
        super().__init__(scenario, p_miss=0.0)
        self.lookup = lookup

    def reset(self, *, seed=None, options=None):
        super(TriageEnv, self).reset(seed=seed)
        self.cause = None
        self.context = np.asarray(options["context"])
        self.symptoms = np.asarray(options["symptoms"], dtype=bool)
        self.reported = np.zeros(self.n_checks, dtype=bool)
        self.available = np.ones(self.n_checks, dtype=bool)
        self.escalate_reason = None
        self.status = np.full(self.n_checks, self.NOT_REQUESTED)
        self.t = self.n_requested = 0
        self.cost_spent = 0.0
        self.blocked_action = None
        return self._obs(), {}

    def step(self, action):
        action = int(action)
        if action < self.n_checks:
            result = self.lookup(action)
            self.available[action] = result is not None
            self.reported[action] = bool(result)
        obs, reward, terminated, truncated, info = super().step(action)
        if info.get("outcome") in ("correct", "wrong"):      # the cause is unknown here
            info = {**info, "outcome": "recommended", "recommended": action - self.n_checks}
        return obs, 0.0, terminated, truncated, info

    def _reference_label(self):
        return None


def load_agent(run_dir):
    return MaskedDQN.load(run_dir / "final.zip", device="cpu")


def action_label(model, env, action):
    if action < env.n_checks:
        check = model["checks"][action]
        return f"Run {check['id']} {check['name']}"
    if action < env.ESCALATE:
        cause = model["causes"][action - env.n_checks]
        return f"Recommend {cause['id']}: {cause['remedy']}"
    return "Escalate to a human expert"


def triage(reading, scenario, model, agent, ask=None):
    """Plays the incident with the agent's greedy policy. `ask(check)` is called for a check the
    logs do not show and returns a Finding, or None to mark it unavailable."""
    check_ids = [c["id"] for c in model["checks"]]
    symptoms = [reading.symptoms[s["id"]].value == PRESENT for s in model["symptoms"]]
    context = [a["values"].index(reading.context[a["id"]].value) for a in model["context"]]
    used = {}                                          # check id -> the finding the agent received

    def lookup(i):
        finding = reading.checks[check_ids[i]]
        if finding.value not in (POSITIVE, NEGATIVE) and ask is not None:
            finding = ask(model["checks"][i]) or finding
        used[check_ids[i]] = finding
        return {POSITIVE: True, NEGATIVE: False}.get(finding.value)

    env = SafetyMechanism(LiveTriageEnv(scenario, lookup))
    obs, _ = env.reset(options={"symptoms": symptoms, "context": context})
    base, checker = env.unwrapped, RuleChecker(scenario)

    steps, done, info = [], False, {}
    while not done:
        mask = env.action_masks()
        q = agent.q_values(np.concatenate([obs, mask.astype(np.float32)]))
        action = int(np.argmax(q))
        finite = np.sort(q[np.isfinite(q)])
        rules = checker.forbidding(action, base.context, base.observed)
        step = {"action": action_label(model, base, action), "value": float(q[action]),
                "margin": float(finite[-1] - finite[-2]) if len(finite) > 1 else None,
                "escalate_value": float(q[base.ESCALATE])}
        obs, _, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        if action < base.n_checks:
            finding = used[check_ids[action]]
            step["result"] = finding.value if base.observed(action) else "unavailable"
            step["evidence"], step["source"] = finding.evidence, finding.source
        elif rules:
            step["blocked_by"] = [{"rule": r.id, "needs": check_ids[r.unless_observed]
                                   if r.unless_observed is not None else None,
                                   "reason": next(x["reason"] for x in model["rules"] if x["id"] == r.id)}
                                  for r in rules]
        steps.append(step)

    belief = posterior(scenario, base.reported_theta, base.status, base.symptoms)
    top = np.argsort(belief)[::-1][:3]
    decision = {"outcome": info["outcome"], "checks_run": int(base.n_requested), "check_minutes":
                round(base.cost_spent * 60), "blocked_proposals": int(env.blocked)}
    if info["outcome"] == "recommended":
        cause = model["causes"][info["recommended"]]
        decision.update(cause=cause["id"], cause_name=cause["name"], remedy=cause["remedy"])
    else:
        decision["reason"] = {"escalated": "The agent judged the evidence too weak or too risky to act on.",
                              "forced_escalation": "The safety mechanism refused two proposals in a row.",
                              "step_limit": "The step limit was reached."}[info["outcome"]]
    return {"reading": reading.to_dict(), "steps": steps, "decision": decision,
            "reference": [{"cause": model["causes"][j]["id"], "name": model["causes"][j]["name"],
                           "probability": float(belief[j])} for j in top]}


def operator_prompt(input_fn=input, output_fn=print):
    """Asks the person running the prototype for a check the logs do not show."""
    def ask(check):
        output_fn(f"\nThe agent wants {check['id']} {check['name']}: {check['tests']}.")
        output_fn(f"Positive means: {check['positive_means']}. The logs do not show it.")
        answer = input_fn("Result? [p]ositive, [n]egative, [u]navailable: ").strip().lower()[:1]
        value = {"p": POSITIVE, "n": NEGATIVE}.get(answer)
        return Finding(value, "reported by the operator", "operator") if value else None
    return ask
