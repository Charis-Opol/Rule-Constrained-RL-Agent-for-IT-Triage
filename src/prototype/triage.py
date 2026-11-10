"""Runs the trained agent, with the safety mechanism, on one real incident.

LiveTriageEnv is the simulator with the random incident replaced by a Reading: the symptoms
and context come from the ticket, and a check's result is looked up only when the agent asks
for it (from the logs, or from the operator). The cause is unknown, so there is no reward and
no right or wrong outcome. The agent, its observation and the safety mechanism are exactly the
ones used in training and evaluation.

With fix-with-verification settings (pilot_settings_v3.json) a fix is followed by
verification, as in training: `verify(cause, report)` (src/prototype/verify.py) says whether
the symptoms cleared. If they did, the incident is resolved; if not, the agent sees that fix
flagged as failed and goes on, and after max_failed_fixes a person takes over. If nobody can
say yet, the incident stops with the fix awaiting verification. Verifying acts on nothing real.

triage() itself only decides. What happens after a permitted decision (a draft pull request,
a fix order to the owner, an escalation report) is in src/prototype/actions.py, which acts only on
a decision that the rule checker has confirmed a second time here ("permitted").
"""
import numpy as np

from src.agents.belief import posterior
from src.agents.dqn import MaskedDQN
from src.prototype.reading import NEGATIVE, POSITIVE, PRESENT, Finding
from src.rules.safety import RuleChecker, SafetyMechanism
from src.sim.triage_env import TriageEnv


class LiveTriageEnv(TriageEnv):
    def __init__(self, scenario, lookup, verify=None):
        """`lookup(check)` returns True (positive), False (negative) or None (unavailable).
        `verify(cause_index)` returns a Verification; required with verification settings."""
        if scenario.verify and verify is None:
            raise ValueError("These settings verify every fix (fix_with_verification): pass a verifier")
        super().__init__(scenario, p_miss=0.0)
        self.lookup, self.verify_fix = lookup, verify
        self.attempts = []

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
        self.failed = np.zeros(self.n_causes, dtype=bool)
        self.attempts = []
        return self._obs(), {}

    def step(self, action):
        action = int(action)
        fix = action - self.n_checks if self.n_checks <= action < self.ESCALATE else None
        if action < self.n_checks:
            result = self.lookup(action)
            self.available[action] = result is not None
            self.reported[action] = bool(result)
        elif fix is not None and self.verify:
            verification = self.verify_fix(fix)
            self.attempts.append((fix, verification))
            if verification.cleared is None:               # nobody can say yet: stop here
                self.t += 1
                return self._obs(), 0.0, True, False, {**self._info("unverified"), "fix": fix}
            # The training environment resolves a fix when it is for self.cause, so the
            # verifier's answer stands in for the unknown cause.
            self.cause = fix if verification.cleared else -1
        obs, reward, terminated, truncated, info = super().step(action)
        self.cause = None
        if info.get("outcome") in ("correct", "wrong"):      # the cause is unknown here
            info = {**info, "outcome": "fix", "fix": fix}
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
        return f"Fix {cause['id']}: {cause['remedy']}"
    return "Escalate to a human expert"


def triage(reading, scenario, model, agent, ask=None, delegate=None, ticket="", logs="", verify=None):
    """Plays the incident with the agent's greedy policy. `ask(check)` is called for a check the
    logs do not show and returns a Finding, or None to mark it unavailable. `delegate` answers
    the checks marked "delegated" from the ticket and logs (src/prototype/delegate.py); without
    one, a delegated check is unavailable. `verify(cause, report)` (src/prototype/verify.py) is
    needed with verification settings; it receives the cause and the steps so far."""
    check_ids = [c["id"] for c in model["checks"]]
    delegations = {}
    symptoms = [reading.symptoms[s["id"]].value == PRESENT for s in model["symptoms"]]
    context = [a["values"].index(reading.context[a["id"]].value) for a in model["context"]]
    used = {}                                          # check id -> the finding the agent received

    def lookup(i):
        finding = reading.checks[check_ids[i]]
        if model["checks"][i].get("delegated"):
            if delegate is not None:
                delegations[check_ids[i]] = delegate.analyse(model["checks"][i], ticket, logs)
                finding = delegations[check_ids[i]].finding
            used[check_ids[i]] = finding
            return {POSITIVE: True, NEGATIVE: False}.get(finding.value)
        if finding.value not in (POSITIVE, NEGATIVE) and ask is not None:
            finding = ask(model["checks"][i]) or finding
        used[check_ids[i]] = finding
        return {POSITIVE: True, NEGATIVE: False}.get(finding.value)

    steps = []

    def verify_fix(j):
        return verify(model["causes"][j], {"reading": reading.to_dict(), "steps": steps})

    env = SafetyMechanism(LiveTriageEnv(scenario, lookup, verify_fix if verify is not None else None))
    obs, _ = env.reset(options={"symptoms": symptoms, "context": context})
    base, checker = env.unwrapped, RuleChecker(scenario)

    done, info = False, {}
    while not done:
        mask = env.action_masks()
        q = agent.q_values(np.concatenate([obs, mask.astype(np.float32)]))
        action = int(np.argmax(q))
        finite = np.sort(q[np.isfinite(q)])
        rules = checker.forbidding(action, base.context, base.observed)
        step = {"action": action_label(model, base, action), "value": float(q[action]),
                "margin": float(finite[-1] - finite[-2]) if len(finite) > 1 else None,
                "escalate_value": float(q[base.ESCALATE])}
        ranked = [a for a in np.argsort(q)[::-1] if np.isfinite(q[a])][:3]
        step["alternatives"] = [{"action": action_label(model, base, int(a)), "value": float(q[a])} for a in ranked]
        obs, _, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        # Reference only, for the person watching: the agent never sees this belief.
        step["belief"] = posterior(scenario, base.reported_theta, base.status, base.symptoms,
                                   base.failed if scenario.verify else None).tolist()
        if action < base.n_checks:
            finding = used[check_ids[action]]
            step["result"] = finding.value if base.observed(action) else "unavailable"
            step["evidence"], step["source"] = finding.evidence, finding.source
            if check_ids[action] in delegations:
                step["delegation"] = delegations[check_ids[action]].to_dict()
        elif len(base.attempts) > sum("verification" in x for x in steps):
            step["verification"] = base.attempts[-1][1].to_dict()
        elif rules:
            step["blocked_by"] = [{"rule": r.id, "needs": check_ids[r.unless_observed]
                                   if r.unless_observed is not None else None,
                                   "reason": next(x["reason"] for x in model["rules"] if x["id"] == r.id)}
                                  for r in rules]
        steps.append(step)

    belief = posterior(scenario, base.reported_theta, base.status, base.symptoms)
    top = np.argsort(belief)[::-1][:3]
    start = posterior(scenario, base.reported_theta, np.full(base.n_checks, TriageEnv.NOT_REQUESTED), base.symptoms)
    decision = {"outcome": info["outcome"], "checks_run": int(base.n_requested), "check_minutes":
                round(base.cost_spent * 60), "blocked_proposals": int(env.blocked)}
    if scenario.verify:
        decision["attempts"] = [{"cause": model["causes"][j]["id"], "cause_name": model["causes"][j]["name"],
                                 "remedy": model["causes"][j]["remedy"], **v.to_dict()} for j, v in base.attempts]
    if info["outcome"] in ("fix", "unverified"):
        cause = model["causes"][info["fix"]]
        # Second, independent check of the final decision against the rules, on the final
        # evidence. actions.py refuses to act unless this is True.
        permitted = not checker.forbidding(base.n_checks + info["fix"], base.context, base.observed)
        decision.update(cause=cause["id"], cause_name=cause["name"], remedy=cause["remedy"], permitted=permitted)
        if scenario.verify:
            decision["verified"] = info["outcome"] == "fix"
        if info["outcome"] == "unverified":
            decision.update(outcome="awaiting_verification",
                            reason="The fix is chosen; it waits for someone to confirm whether the symptoms clear.")
    else:
        failed = len(decision.get("attempts", []))
        decision["reason"] = {"escalated": "The agent judged the evidence too weak or too risky to act on.",
                              "forced_escalation": "The safety mechanism refused two proposals in a row.",
                              "step_limit": "The step limit was reached.",
                              "fix_limit": f"{failed} fixes were applied and did not clear the symptoms; "
                                           "a person takes over."}[info["outcome"]]
    return {"reading": reading.to_dict(), "steps": steps, "decision": decision,
            "warnings": [d.warning for d in delegations.values() if d.warning],
            "start_belief": start.tolist(),
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


def run_settings(run_dir, default):
    """The settings a run was trained with (its config.json), so that the prototype plays the
    incident in the environment the agent learned; `default` if the run does not record them."""
    import json
    from pathlib import Path
    config = Path(run_dir) / "config.json"
    if not config.exists():
        return default
    root = Path(__file__).resolve().parents[2]
    return root / json.loads(config.read_text(encoding="utf-8"))["settings"]
