"""Evaluate the comparison experiments (Chapter 3, Experiments 1 and 2) on v3 settings.

    python -m experiments.pilot.evaluate_comparison [--n-eval 5000] [--n-tune 2000] [--allow-missing]
    python -m experiments.pilot.evaluate_comparison --replot

Experiment 1: every baseline and the shielded agent on the same evaluation incidents; the paired
difference in return between the agent and the threshold policy (same incidents, bootstrap over
incidents); and the escalation-cost sensitivity analysis (60 / 120 / 240 min), with the
threshold and scripted baselines re-tuned at each cost on the tuning incidents.
Experiment 2: shielded vs unconstrained vs penalty-only; the unconstrained and penalty-only agents
run without enforcement and without the training penalty, so returns are comparable and their
executed violations are counted; proposals that break a rule, tracked over training.

The exact policy is not available with verification, so there is no exact reference here.
Writes results/pilot/comparison.{json,md} and figures/comparison_*.{png,pdf}.
"""
import argparse
import json
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                              # noqa: E402
import numpy as np                                           # noqa: E402
import pandas as pd                                          # noqa: E402

from experiments.pilot.evaluate_phase5 import AGENT_COLOURS, AGENT_LABELS, BASELINE, GRID, INK, MUTED, footnote, \
    style                                                    # noqa: E402
from experiments.pilot.run_comparison import (AGENTS, BASE_ESCALATION, MODEL, RUNS, SEEDS, SENSITIVITY_ESCALATION,
                                              SETTINGS, run_name)   # noqa: E402
from src.agents.baselines import AlwaysEscalate, Scripted, SymptomsOnly, Threshold   # noqa: E402
from src.agents.dqn import AgentPolicy, MaskedDQN, make_env          # noqa: E402
from src.evaluation import TUNE_SEED, bootstrap_ci, run_episodes, summarise   # noqa: E402
from src.sim.scenario import load_scenario                           # noqa: E402

OUT = RUNS.parent
FIGURES = OUT / "figures"
TAUS = [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]
KEYS = ["mean_return", "resolution_accuracy", "wrong_fix_rate", "mean_wrong_fixes", "escalation_rate",
        "mean_checks", "mean_check_cost", "escalation_precision", "escalation_recall", "escalation_mcc",
        "proposed_violation_rate", "forced_escalation_rate", "executed_violation_rate", "compliant_success_rate",
        "ceiling"]
ESCALATIONS = sorted({BASE_ESCALATION, *SENSITIVITY_ESCALATION})


def clean(m):
    return {k: (None if isinstance(m[k], float) and np.isnan(m[k]) else m[k]) for k in KEYS} | \
        {"return_ci": list(m["return_ci"])}


MIX = ("resolved first try", "resolved after a failed fix", "escalated by the agent", "after 2 failed fixes",
       "forced or step limit")


def mix(rows):
    """Share of incidents ending each way (the Experiment 1 and 2 outcome breakdown)."""
    def kind(r):
        if r["outcome"] == "correct":
            return MIX[1] if r["wrong_fixes"] else MIX[0]
        return {"escalated": MIX[2], "fix_limit": MIX[3]}.get(r["outcome"], MIX[4])
    kinds = [kind(r) for r in rows]
    return {k: kinds.count(k) / len(rows) for k in MIX}


def env_for(s, agent):
    """Shielded agents and baselines run under the mechanism; the other agents are only monitored."""
    return make_env(s, "shielded" if agent == "shielded" else "unconstrained", train=False)


def tune(s, n_tune):
    """Threshold tau and scripted k with the highest mean return on the tuning incidents."""
    env = env_for(s, "shielded")
    def best(candidates):
        scores = {k: summarise(run_episodes(p, env_for(s, "shielded"), n_tune, first_seed=TUNE_SEED))["mean_return"]
                  for k, p in candidates}
        return max(scores, key=scores.get), scores
    tau, tau_scores = best([(t, Threshold(env, t)) for t in TAUS])
    k, k_scores = best([(k, Scripted(env, k)) for k in range(env.unwrapped.n_checks + 1)])
    return tau, k, {"threshold": tau_scores, "scripted": k_scores}


def load_agents(escalation, agents, allow_missing):
    found = {}
    for agent in agents:
        for seed in SEEDS:
            path = RUNS / run_name(agent, seed, escalation) / "final.zip"
            if path.exists():
                found.setdefault(agent, {})[seed] = MaskedDQN.load(path, device="cpu")
            elif not allow_missing:
                raise SystemExit(f"Missing {path}; finish training or pass --allow-missing")
    return found


def paired(rows_a, rows_b, seed=0, n_boot=2000):
    """Mean per-incident difference in return (a - b) on the same incidents, bootstrap over incidents."""
    diff = np.array([a["return"] - b["return"] for a, b in zip(rows_a, rows_b)])
    return {"mean": float(diff.mean()), "ci": list(bootstrap_ci(diff, n_boot=n_boot, seed=seed))}


def evaluate_level(escalation, agents, n_eval, n_tune):
    s = load_scenario(MODEL, SETTINGS, escalation)
    tau, k, tuning = tune(s, n_tune)
    env = env_for(s, "shielded")
    level = {"escalation_minutes": escalation, "tau": tau, "k": k, "tuning": tuning, "baselines": {}, "agents": {},
             "paired_vs_threshold": {}}
    threshold_rows = None
    for label, policy in (("Always escalate", AlwaysEscalate(env)), ("Initial-symptom", SymptomsOnly(env)),
                          (f"Scripted (k={k})", Scripted(env, k)), (f"Threshold (tau={tau})", Threshold(env, tau))):
        rows = run_episodes(policy, env_for(s, "shielded"), n_eval)
        level["baselines"][label] = clean(summarise(rows)) | {"mix": mix(rows)}
        if label.startswith("Threshold"):
            threshold_rows = rows
    for agent, models in agents.items():
        per_seed, diffs = {}, {}
        for seed, model in models.items():
            rows = run_episodes(AgentPolicy(model), env_for(s, agent), n_eval)
            per_seed[seed] = clean(summarise(rows)) | {"mix": mix(rows)}
            diffs[seed] = paired(rows, threshold_rows, seed=seed)
        summary = {}
        for key in KEYS:
            values = [m[key] for m in per_seed.values() if m[key] is not None]
            if values:
                summary[key] = {"mean": float(np.mean(values)), "ci": list(bootstrap_ci(values)), "seeds": values}
        summary["mix"] = {k: float(np.mean([m["mix"][k] for m in per_seed.values()])) for k in MIX}
        level["agents"][agent] = {"per_seed": per_seed, "summary": summary}
        level["paired_vs_threshold"][agent] = diffs
    return level


def training_curves(agents):
    curves = {}
    for agent, seeds in agents.items():
        frames = []
        for seed in seeds:
            path = RUNS / run_name(agent, seed) / "metrics.jsonl"
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
            frames.append(pd.DataFrame(rows)[["step", "proposed_violation_rate", "mean_return"]].assign(seed=seed))
        curves[agent] = pd.concat(frames)
    return curves


# ----- Figures ---------------------------------------------------------------
def save(fig, name):
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / f"{name}.png", dpi=150)
    fig.savefig(FIGURES / f"{name}.pdf")
    plt.close(fig)


def comparison_figure(base, n_eval):
    panels = [("mean_return", "Return", False), ("resolution_accuracy", "Resolved correctly", True),
              ("wrong_fix_rate", "Any wrong fix applied", True), ("escalation_rate", "Escalated", True),
              ("mean_checks", "Checks per incident", False), ("executed_violation_rate", "Rule broken (executed)", True)]
    rows = [(label, None) for label in base["baselines"]] + [(AGENT_LABELS[a], a) for a in base["agents"]]
    fig, axes = plt.subplots(2, 3, figsize=(12, 7.2), sharey=True)
    for ax, (key, title, percent) in zip(axes.flat, panels):
        for y, (label, agent) in enumerate(rows):
            if agent is None:
                value = base["baselines"][label][key]
                if value is not None:
                    ax.plot(value, y, "o", color=BASELINE, markersize=7)
            elif key in base["agents"][agent]["summary"]:
                summary = base["agents"][agent]["summary"][key]
                ax.plot(summary["ci"], [y, y], color=AGENT_COLOURS[agent], linewidth=3, solid_capstyle="round")
                ax.plot(summary["seeds"], [y] * len(summary["seeds"]), "|", color=AGENT_COLOURS[agent],
                        markersize=9, alpha=0.6)
                ax.plot(summary["mean"], y, "o", color=AGENT_COLOURS[agent], markersize=8,
                        markeredgecolor="white", markeredgewidth=1.5)
        ax.set_yticks(range(len(rows)), [r[0] for r in rows])
        ax.invert_yaxis()
        style(ax, title, percent)
    fig.suptitle(f"Experiments 1 and 2 (fix with verification): all policies on the same {n_eval:,} incidents",
                 x=0.01, ha="left", fontsize=11, fontweight="bold", color=INK)
    bottom = footnote(fig, "Grey: baselines with the safety mechanism, tuned on separate incidents. Coloured: DQN "
                      "agents; dot = mean over seeds, bar = 95% bootstrap interval over seeds, ticks = seeds. "
                      "Unconstrained and penalty-only agents run without enforcement. Model v2 (pilot developer, "
                      "Part 2); verification settings researcher-provisional. Not Directorate data.", 190)
    fig.tight_layout(rect=(0, bottom, 1, 0.95))
    save(fig, "comparison_policies")


def sensitivity_figure(levels):
    metrics = [("mean_return", "Return", False), ("resolution_accuracy", "Resolved correctly", True),
               ("wrong_fix_rate", "Any wrong fix applied", True), ("escalation_rate", "Escalated", True)]
    xs = [lv["escalation_minutes"] for lv in levels]
    fig, axes = plt.subplots(1, 4, figsize=(14, 4.2))
    for ax, (key, title, percent) in zip(axes, metrics):
        summaries = [lv["agents"].get("shielded", {}).get("summary", {}).get(key) for lv in levels]
        if all(summaries):
            ax.fill_between(xs, [v["ci"][0] for v in summaries], [v["ci"][1] for v in summaries],
                            color=AGENT_COLOURS["shielded"], alpha=0.15, linewidth=0)
            ax.plot(xs, [v["mean"] for v in summaries], "-o", color=AGENT_COLOURS["shielded"], linewidth=2,
                    label=AGENT_LABELS["shielded"])
        for prefix, ls, colour in (("Threshold", (0, (4, 3)), MUTED), ("Scripted", (0, (1, 2)), MUTED),
                                   ("Initial-symptom", "-", BASELINE)):
            values = [next(v[key] for lab, v in lv["baselines"].items() if lab.startswith(prefix)) for lv in levels]
            ax.plot(xs, values, linestyle=ls, marker="s", markersize=4, color=colour, linewidth=1.3,
                    label=f"{prefix} (re-tuned)" if prefix != "Initial-symptom" else prefix)
        ax.set_xticks(xs, [f"{x:g} min" for x in xs])
        ax.set_xlabel("Cost of escalation", color=MUTED)
        ax.set_title(title, loc="left", fontsize=10, fontweight="bold", color=INK)
        ax.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        if percent:
            ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=len(labels), frameon=False, bbox_to_anchor=(0.5, 0.93))
    fig.suptitle("Sensitivity: Experiment 1 repeated with escalation at half and twice the elicited 120 min",
                 x=0.01, ha="left", fontsize=11, fontweight="bold", color=INK)
    bottom = footnote(fig, "The agent is retrained at each cost (3 seeds; band = 95% bootstrap interval over seeds). "
                      "A wrong fix keeps the elicited 5x escalation, so its harm scales with the cost. Returns are "
                      "in hours and are not comparable across costs; compare policies within a cost.", 220)
    fig.tight_layout(rect=(0, bottom + 0.03, 1, 0.86))
    save(fig, "comparison_sensitivity")


MIX_COLOURS = {MIX[0]: "#2a78d6", MIX[1]: "#86b6ef", MIX[2]: "#a3a29d", MIX[3]: "#eb6834", MIX[4]: "#eda100"}


def mix_figure(base):
    rows = [(label, m["mix"]) for label, m in base["baselines"].items()] +         [(AGENT_LABELS[a], d["summary"]["mix"]) for a, d in base["agents"].items()]
    fig, ax = plt.subplots(figsize=(11, 0.55 * len(rows) + 1.9))
    for y, (label, mix_) in enumerate(rows):
        left = 0.0
        for kind in MIX:
            width = mix_.get(kind, 0.0)
            if width > 0:
                ax.barh(y, width, left=left, height=0.62, color=MIX_COLOURS[kind], edgecolor="#fcfcfb", linewidth=2,
                        label=kind if y == 0 or kind not in ax.get_legend_handles_labels()[1] else None)
                if width >= 0.06:
                    ax.text(left + width / 2, y, f"{width:.0%}", ha="center", va="center", fontsize=8.5,
                            color="white" if kind in (MIX[0], MIX[3]) else INK)
            left += width
    ax.set_yticks(range(len(rows)), [r[0] for r in rows])
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(left=False)
    handles, labels = ax.get_legend_handles_labels()
    order = [labels.index(k) for k in MIX if k in labels]
    fig.legend([handles[i] for i in order], [labels[i] for i in order], loc="upper left", ncol=5, frameon=False,
               bbox_to_anchor=(0.005, 0.93), fontsize=9)
    fig.suptitle("How each incident ended (escalation 120 min)", x=0.01, ha="left", fontsize=11, fontweight="bold",
                 color=INK)
    bottom = footnote(fig, "Same 5,000 evaluation incidents for every policy; agents averaged over 3 seeds. 'After 2 "
                      "failed fixes': a person takes over (counted as an escalation). 'Forced or step limit': the "
                      "safety mechanism refused two proposals in a row, or the step limit was reached. Pilot data, "
                      "not Directorate data.", 170)
    fig.tight_layout(rect=(0, bottom, 1, 0.87))
    save(fig, "comparison_outcomes")


def blocked_figure(curves):
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for agent, df in curves.items():
        g = df.groupby("step")["proposed_violation_rate"]
        mean = g.mean()
        ax.fill_between(mean.index, g.min(), g.max(), color=AGENT_COLOURS[agent], alpha=0.15, linewidth=0)
        ax.plot(mean.index, mean, color=AGENT_COLOURS[agent], linewidth=2, label=AGENT_LABELS[agent])
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{x / 1000:,.0f}k"))
    ax.set_xlabel("Training step", color=MUTED)
    ax.set_ylabel("Proposals that break a rule", color=MUTED)
    ax.set_title("Experiment 2: does the agent learn to act within the rules?", loc="left", fontsize=11,
                 fontweight="bold")
    ax.grid(True, color=GRID, linewidth=0.8)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(frameon=False, loc="upper right")
    bottom = footnote(fig, "Fix with verification (v3). Mean over seeds; band = lowest to highest seed. With the "
                      "mechanism these proposals are blocked; without it they execute. Monitoring incidents.", 125)
    fig.tight_layout(rect=(0, bottom, 1, 1))
    save(fig, "comparison_blocked_over_training")


# ----- Tables ----------------------------------------------------------------
def fmt(value, percent):
    if value is None:
        return "n/a"
    return f"{value:.1%}" if percent else f"{value:.2f}"


COLS = [("Return", "mean_return", False), ("Correct", "resolution_accuracy", True),
        ("Any wrong fix", "wrong_fix_rate", True), ("Wrong fixes / incident", "mean_wrong_fixes", False),
        ("Escalated", "escalation_rate", True), ("Checks", "mean_checks", False), ("Esc. MCC", "escalation_mcc", False),
        ("Rule-breaking proposals", "proposed_violation_rate", True),
        ("Rule broken (executed)", "executed_violation_rate", True), ("Compliant success", "compliant_success_rate", True)]


def policy_rows(level):
    lines = ["| Policy | " + " | ".join(c[0] for c in COLS) + " |", "|---" * (len(COLS) + 1) + "|"]
    for label, m in level["baselines"].items():
        lines.append(f"| {label} | " + " | ".join(fmt(m[k], p) for _, k, p in COLS) + " |")
    for agent, data in level["agents"].items():
        s = data["summary"]
        cells = []
        for _, k, p in COLS:
            cell = fmt(s[k]["mean"], p) if k in s else "n/a"
            if k == "mean_return":
                cell += f" [{s[k]['ci'][0]:.2f}, {s[k]['ci'][1]:.2f}]"
            cells.append(cell)
        lines.append(f"| {AGENT_LABELS[agent]} ({len(data['per_seed'])} seeds) | " + " | ".join(cells) + " |")
    return lines


def paired_lines(level):
    lines = []
    for agent, diffs in level["paired_vs_threshold"].items():
        parts = [f"seed {seed}: {d['mean']:+.3f} [{d['ci'][0]:+.3f}, {d['ci'][1]:+.3f}]" for seed, d in diffs.items()]
        lines.append(f"- {AGENT_LABELS[agent]} minus threshold: " + "; ".join(parts))
    return lines


def report(out):
    base = next(lv for lv in out["levels"] if lv["escalation_minutes"] == BASE_ESCALATION)
    lines = ["# Comparison experiments (Experiments 1 and 2), fix with verification", "",
             f"Model v2 (pilot developer, Part 2) with `pilot_settings_v3.json`; {out['n_eval']:,} evaluation "
             "incidents, the same for every policy; noise 0.1, no missing checks. Baselines run with the safety "
             f"mechanism and were tuned on {out['n_tune']:,} separate incidents (threshold tau = {base['tau']}, "
             f"scripted k = {base['k']}). Agents: mean over their seeds, with the 95% bootstrap interval over seeds "
             "for the return. Unconstrained and penalty-only agents run without enforcement and without the training "
             "penalty. Returns in hours (negative = time lost). There is no exact reference with verification. The "
             "verification settings are researcher-provisional. Pilot data, not Directorate data.", "",
             "## Experiments 1 and 2: base level (escalation 120 min)", "", *policy_rows(base), "",
             "**Paired difference in return against the threshold policy** (same incidents; 95% bootstrap over "
             "incidents):", "", *paired_lines(base), "",
             "## Experiment 1, sensitivity: cost of escalation", "",
             "The shielded agent is retrained at each cost; the threshold and scripted baselines are re-tuned. The "
             "wrong-fix cost stays 5x escalation.", ""]
    for lv in out["levels"]:
        if lv["escalation_minutes"] == BASE_ESCALATION:
            continue
        lines += [f"### Escalation {lv['escalation_minutes']:g} min (tau = {lv['tau']}, k = {lv['k']})", "",
                  *policy_rows(lv), "", *paired_lines(lv), ""]
    return "\n".join(lines) + "\n"


def draw(out, curves):
    base = next(lv for lv in out["levels"] if lv["escalation_minutes"] == BASE_ESCALATION)
    comparison_figure(base, out["n_eval"])
    mix_figure(base)
    sensitivity_figure(out["levels"])
    blocked_figure(curves)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--n-eval", type=int, default=5000)
    parser.add_argument("--n-tune", type=int, default=2000)
    parser.add_argument("--allow-missing", action="store_true")
    parser.add_argument("--replot", action="store_true", help="redraw the figures from comparison.json")
    args = parser.parse_args(argv)
    started = time.time()
    if args.replot:
        out = json.loads((OUT / "comparison.json").read_text(encoding="utf-8"))
    else:
        levels = []
        for escalation in ESCALATIONS:
            agents = load_agents(escalation, AGENTS if escalation == BASE_ESCALATION else ("shielded",),
                                 args.allow_missing)
            print(f"escalation {escalation:g} min: agents {({a: sorted(m) for a, m in agents.items()})}", flush=True)
            levels.append(evaluate_level(escalation, agents, args.n_eval, args.n_tune))
            print(f"  done ({time.time() - started:.0f} s)", flush=True)
        out = {"note": "Pilot data (model v2, pilot developer), verification settings researcher-provisional; "
                       "not Directorate data.",
               "model": str(MODEL.relative_to(OUT.parents[1])), "settings": str(SETTINGS.relative_to(OUT.parents[1])),
               "n_eval": args.n_eval, "n_tune": args.n_tune, "levels": levels}
        (OUT / "comparison.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
        (OUT / "comparison.md").write_text(report(out), encoding="utf-8")
    base = next(lv for lv in out["levels"] if lv["escalation_minutes"] == BASE_ESCALATION)
    seeds = {a: [s for s in SEEDS if (RUNS / run_name(a, s) / "metrics.jsonl").exists()] for a in base["agents"]}
    draw(out, training_curves(seeds))
    print(report(out))
    print(f"Done in {time.time() - started:.0f} s")


if __name__ == "__main__":
    main()
