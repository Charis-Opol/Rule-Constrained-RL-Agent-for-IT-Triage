"""Builds the step-by-step record of one incident that the Thinking view shows."""
import numpy as np

from src.agents.belief import posterior
from src.agents.dqn import make_env
from src.agents.exact import solve
from src.rules.safety import RuleChecker
from src.sim.scenario import load_scenario
from src.sim.triage_env import TriageEnv

STATUS_NAMES = {TriageEnv.NOT_REQUESTED: "not run", TriageEnv.UNAVAILABLE: "unavailable",
                TriageEnv.NEGATIVE: "negative", TriageEnv.POSITIVE: "positive"}


def load_run_scenario(root, config):
    return load_scenario(root / config["model"], root / config["settings"])


def exact_for(model_path, settings_path, agent, p_noise, p_miss):
    if p_miss > 0:
        return None
    scenario = load_scenario(model_path, settings_path)
    return solve(make_env(scenario, agent, train=False, p_noise=p_noise, p_miss=p_miss))


def action_names(env, model_names=None):
    names = [f"Run D{i + 1:02d}" for i in range(env.n_checks)]
    names += [f"Fix C{j + 1:02d}" for j in range(env.n_causes)]
    return names + ["Escalate"]


def trace(model, scenario, agent, seed, flips=(), exact=None):
    """Plays one incident with the agent's greedy policy and records each decision."""
    env = make_env(scenario, agent, train=False)
    obs, _ = env.reset(seed=seed)
    base = env.unwrapped
    for i in flips:                                     # what-if: reverse these results
        base.reported[i] = not base.reported[i]
    checker = RuleChecker(scenario)
    labels = action_names(base)
    steps, total, done = [], 0.0, False
    while not done:
        mask = env.action_masks()
        status, symptoms, context, t, blocked = base.layout.decode(obs)
        q_agent = model.q_values(np.concatenate([obs, mask.astype(np.float32)]))
        action = int(np.argmax(q_agent))
        q_exact = None
        if exact is not None and not (status == TriageEnv.UNAVAILABLE).any():
            q_exact = exact.q_values(status, symptoms, context)

        prohibited = {}
        for a in range(base.n_checks, base.ESCALATE):
            for rule in checker.forbidding(a, base.context, base.observed):
                needs = f"D{rule.unless_observed + 1:02d}" if rule.unless_observed is not None else "never lifted"
                prohibited[a] = f"{rule.id} (needs {needs})"

        rows = []
        for a, label in enumerate(labels):
            if a < base.n_checks and status[a] != TriageEnv.NOT_REQUESTED:
                state = "already run"
            elif not mask[a]:
                state = "blocked last step"
            elif a in prohibited:
                state = f"prohibited: {prohibited[a]}"
            else:
                state = "available"
            rows.append({"Action": label, "Agent value": None if np.isinf(q_agent[a]) else float(q_agent[a]),
                         "Exact value": None if q_exact is None or np.isnan(q_exact[a]) else float(q_exact[a]),
                         "State": state, "Chosen": "◄" if a == action else ""})
        finite = np.sort(q_agent[np.isfinite(q_agent)])
        record = {
            "context": [scenario.context_values[i][v] for i, v in enumerate(context)],
            "symptoms": symptoms.tolist(),
            "check_status": [STATUS_NAMES[int(v)] for v in status],
            "posterior": posterior(scenario, base.reported_theta, status, symptoms).tolist(),
            "blocked_rules": [f"{labels[a]} by {why}" for a, why in prohibited.items()],
            "actions": rows,
            "chosen": labels[action],
            "margin": float(finite[-1] - finite[-2]) if len(finite) > 1 else None,
            "exact_choice": labels[int(np.nanargmax(q_exact))] if q_exact is not None else None,
            "was_blocked": blocked,
        }
        obs, reward, terminated, truncated, info = env.step(action)
        total += reward
        done = terminated or truncated
        if not done and env.unwrapped.blocked_action == action:
            record["result"] = f"The safety mechanism blocked {labels[action]}. The agent must choose again."
        steps.append(record)
    steps[-1].update(outcome=info["outcome"], total_return=total, cause=info["cause"])
    if steps[-1].get("result") is None:
        steps[-1]["result"] = f"Episode ends: {info['outcome']}."
    return steps
