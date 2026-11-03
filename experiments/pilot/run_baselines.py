"""Phase 3: tune the baselines on tuning incidents, solve the exact policy, and evaluate every
policy on the same 5,000 evaluation incidents at the base ambiguity level.

    python -m experiments.pilot.run_baselines
"""
import json
import time
from pathlib import Path

from src.agents.baselines import AlwaysEscalate, Scripted, SymptomsOnly, Threshold
from src.agents.exact import ExactPolicy, solve
from src.evaluation import TUNE_SEED, run_episodes, summarise
from src.rules.safety import SafetyMechanism
from src.sim.scenario import load_scenario
from src.sim.triage_env import TriageEnv

PILOT = Path(__file__).resolve().parent
RESULTS = PILOT.parents[1] / "results" / "pilot"
N_EVAL, N_TUNE = 5000, 5000
TAUS = [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]


def make_env():
    return SafetyMechanism(TriageEnv(load_scenario(PILOT / "pilot_model.json", PILOT / "pilot_settings.json")))


def tune(label, candidates):
    """Picks the setting with the highest mean return on the tuning incidents."""
    rows = []
    for setting, policy in candidates:
        m = summarise(run_episodes(policy, make_env(), N_TUNE, first_seed=TUNE_SEED))
        rows.append({"setting": setting, **{k: m[k] for k in ("mean_return", "resolution_accuracy", "wrong_rate",
                                                              "escalation_rate", "mean_checks", "mean_check_cost")}})
        print(f"  tune {label} {setting}: return {m['mean_return']:.3f}, checks {m['mean_checks']:.2f}")
    return max(rows, key=lambda r: r["mean_return"])["setting"], rows


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)
    env = make_env()
    started = time.time()
    solution = solve(env)
    print(f"Exact solution: value {solution.value:.4f} ({time.time() - started:.0f} s)", solution.stats)

    tau, tau_rows = tune("threshold", [(t, Threshold(env, t)) for t in TAUS])
    k, k_rows = tune("scripted", [(k, Scripted(env, k)) for k in range(env.unwrapped.n_checks + 1)])

    policies = [AlwaysEscalate(env), SymptomsOnly(env), Scripted(env, k), Threshold(env, tau),
                ExactPolicy(env, solution)]
    results = {}
    for policy in policies:
        label = policy.name + (f" (k={k})" if isinstance(policy, Scripted) else
                               f" (tau={tau})" if isinstance(policy, Threshold) else "")
        results[label] = summarise(run_episodes(policy, make_env(), N_EVAL))
        print(f"{label}: return {results[label]['mean_return']:.3f}")

    out = {"note": "Pilot data, base ambiguity level (noise 0.1, no missing checks), with the safety mechanism.",
           "n_eval": N_EVAL, "n_tune": N_TUNE,
           "exact": {"value": solution.value, **solution.stats},
           "tuning": {"threshold": tau_rows, "scripted": k_rows},
           "results": results}
    (RESULTS / "baselines.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    (RESULTS / "baselines.md").write_text(table(out), encoding="utf-8")
    print(table(out))


def table(out):
    cols = [("Return", "mean_return", "{:.2f}"), ("95% CI", "return_ci", "[{:.2f}, {:.2f}]"),
            ("Correct", "resolution_accuracy", "{:.1%}"), ("Wrong", "wrong_rate", "{:.1%}"),
            ("Escalated", "escalation_rate", "{:.1%}"), ("Checks", "mean_checks", "{:.2f}"),
            ("Esc. F1", "escalation_f1", "{:.2f}"), ("Esc. MCC", "escalation_mcc", "{:.2f}"),
            ("Blocked proposals", "proposed_violation_rate", "{:.1%}"),
            ("Forced esc.", "forced_escalation_rate", "{:.1%}")]
    lines = ["# Pilot baselines (base level)", "",
             f"Evaluation: {out['n_eval']} incidents, the same for every policy. Exact expected return "
             f"{out['exact']['value']:.3f}. Ceiling (share resolvable): "
             f"{next(iter(out['results'].values()))['ceiling']:.1%}. Pilot data, not Directorate data. "
             "n/a: the measure is undefined (for example, F1 for a policy that never escalates).", "",
             "| Policy | " + " | ".join(c[0] for c in cols) + " |", "|---" * (len(cols) + 1) + "|"]
    def cell(value, fmt):
        if isinstance(value, (list, tuple)):
            return fmt.format(*value)
        return "n/a" if value != value else fmt.format(value)    # nan: ratio undefined

    for label, m in out["results"].items():
        cells = [cell(m[key], fmt) for _, key, fmt in cols]
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
