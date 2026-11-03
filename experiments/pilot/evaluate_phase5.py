"""Phase 5 evaluation: every policy on the same evaluation incidents, agents summarised over
their five seeds, and an ambiguity sweep on the saved agents (no retraining).

    python -m experiments.pilot.evaluate_phase5 [--n-eval 5000] [--n-sweep 2000] [--allow-missing]

The unconstrained and penalty-only agents are evaluated without enforcement and without the
training penalty, so their returns are comparable and their executed violations are counted.
"""
import argparse
import json
import textwrap
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                              # noqa: E402
import numpy as np                                           # noqa: E402
import pandas as pd                                          # noqa: E402

from experiments.pilot.run_phase5 import AGENTS, SEEDS, run_name     # noqa: E402
from src.agents.baselines import AlwaysEscalate, Scripted, SymptomsOnly, Threshold   # noqa: E402
from src.agents.dqn import AgentPolicy, MaskedDQN, make_env          # noqa: E402
from src.agents.exact import ExactPolicy, solve                      # noqa: E402
from src.evaluation import bootstrap_ci, run_episodes, summarise     # noqa: E402
from src.sim.scenario import load_scenario                           # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PILOT = ROOT / "experiments" / "pilot"
RUNS = ROOT / "results" / "pilot" / "runs"
OUT = ROOT / "results" / "pilot"
FIGURES = OUT / "figures"
SCRIPTED_K, THRESHOLD_TAU = 9, 0.65                                  # tuned in Phase 3
LEVELS = [(0.0, 0.0), (0.1, 0.0), (0.2, 0.0), (0.1, 0.2), (0.1, 0.4)]   # (noise, missing), one at a time
BASE = (0.1, 0.0)
KEYS = ["mean_return", "resolution_accuracy", "wrong_rate", "escalation_rate", "coverage", "selective_accuracy",
        "mean_checks", "mean_check_cost", "escalation_precision", "escalation_recall", "escalation_f1",
        "escalation_mcc", "proposed_violation_rate", "forced_escalation_rate", "executed_violation_rate",
        "compliant_success_rate", "ceiling"]
AGENT_LABELS = {"shielded": "DQN with safety mechanism", "unconstrained": "DQN unconstrained",
                "penalty": "DQN penalty-only"}
AGENT_COLOURS = {"shielded": "#2a78d6", "unconstrained": "#eb6834", "penalty": "#1baf7a"}
INK, MUTED, GRID, BASELINE = "#0b0b0b", "#52514e", "#e6e5e1", "#8a8985"


def scenario():
    return load_scenario(PILOT / "pilot_model.json", PILOT / "pilot_settings.json")


def evaluation_env(s, agent, noise, miss):
    """Shielded agents and baselines run under the mechanism; the other agents are only monitored."""
    kind = "shielded" if agent == "shielded" else "unconstrained"
    return make_env(s, kind, train=False, p_noise=noise, p_miss=miss)


def score(policy, env, n):
    m = summarise(run_episodes(policy, env, n))
    return {k: (None if isinstance(m[k], float) and np.isnan(m[k]) else m[k]) for k in KEYS} | \
        {"return_ci": list(m["return_ci"])}


def available_agents(allow_missing):
    found = {}
    for agent in AGENTS:
        for seed in SEEDS:
            path = RUNS / run_name(agent, seed) / "final.zip"
            if path.exists():
                found.setdefault(agent, {})[seed] = MaskedDQN.load(path, device="cpu")
            elif not allow_missing:
                raise SystemExit(f"Missing {path}; finish training or pass --allow-missing")
    return found


def evaluate_level(s, agents, noise, miss, n):
    level = {"baselines": {}, "agents": {}}
    env = evaluation_env(s, "shielded", noise, miss)
    baselines = [("Always escalate", AlwaysEscalate(env)), ("Initial-symptom", SymptomsOnly(env)),
                 (f"Scripted (k={SCRIPTED_K})", Scripted(env, SCRIPTED_K)),
                 (f"Threshold (tau={THRESHOLD_TAU})", Threshold(env, THRESHOLD_TAU))]
    if miss == 0:
        baselines.append(("Exact optimal", ExactPolicy(env, solve(env))))
    for label, policy in baselines:
        level["baselines"][label] = score(policy, evaluation_env(s, "shielded", noise, miss), n)
    for agent, models in agents.items():
        per_seed = {seed: score(AgentPolicy(model), evaluation_env(s, agent, noise, miss), n)
                    for seed, model in models.items()}
        summary = {}
        for key in KEYS:
            values = [m[key] for m in per_seed.values() if m[key] is not None]
            if values:
                summary[key] = {"mean": float(np.mean(values)), "ci": list(bootstrap_ci(values)),
                                "seeds": values}
        level["agents"][agent] = {"per_seed": per_seed, "summary": summary}
    return level


def training_curves(agents):
    curves = {}
    for agent, models in agents.items():
        frames = []
        for seed in models:
            rows = [json.loads(line) for line in
                    (RUNS / run_name(agent, seed) / "metrics.jsonl").read_text(encoding="utf-8").splitlines() if line]
            frames.append(pd.DataFrame(rows)[["step", "proposed_violation_rate", "mean_return"]].assign(seed=seed))
        curves[agent] = pd.concat(frames)
    return curves


# ----- Figures ---------------------------------------------------------------
def footnote(fig, text, width):
    """Wrapped note under the figure; returns the bottom margin it needs."""
    wrapped = "\n".join(textwrap.wrap(text, width))
    fig.text(0.01, 0.008, wrapped, fontsize=8, color=MUTED, va="bottom")
    return (wrapped.count("\n") + 1) * 0.022 + 0.01


def style(ax, title, percent=False):
    ax.set_title(title, loc="left", fontsize=10, fontweight="bold", color=INK)
    ax.grid(True, axis="x" if ax.get_ylabel() == "" else "both", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    if percent:
        ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins=5))
        ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v * 100:g}%"))


def comparison_figure(base, path, n_eval):
    panels = [("mean_return", "Return", False), ("resolution_accuracy", "Resolved correctly", True),
              ("wrong_rate", "Wrong fix", True), ("escalation_rate", "Escalated", True),
              ("mean_checks", "Checks per incident", False), ("executed_violation_rate", "Rule broken (executed)", True)]
    rows = [(label, None) for label in base["baselines"]] + [(AGENT_LABELS[a], a) for a in base["agents"]]
    fig, axes = plt.subplots(2, 3, figsize=(12, 7.2), sharey=True)
    for ax, (key, title, percent) in zip(axes.flat, panels):
        for y, (label, agent) in enumerate(rows):
            if agent is None:
                value = base["baselines"][label][key]
                if value is not None:
                    ax.plot(value, y, "o", color=BASELINE, markersize=7)
            else:
                summary = base["agents"][agent]["summary"][key]
                low, high = summary["ci"]
                ax.plot([low, high], [y, y], color=AGENT_COLOURS[agent], linewidth=3, solid_capstyle="round")
                ax.plot(summary["seeds"], [y] * len(summary["seeds"]), "|", color=AGENT_COLOURS[agent],
                        markersize=9, alpha=0.6)
                ax.plot(summary["mean"], y, "o", color=AGENT_COLOURS[agent], markersize=8,
                        markeredgecolor="white", markeredgewidth=1.5)
        ax.set_yticks(range(len(rows)), [r[0] for r in rows])
        ax.invert_yaxis()
        style(ax, title, percent)
    fig.suptitle(f"Phase 5: all policies on the same {n_eval:,} evaluation incidents "
                 "(base level: noise 0.1, no missing checks)", x=0.01, ha="left", fontsize=11, fontweight="bold",
                 color=INK)
    seeds = sorted({len(d["per_seed"]) for d in base["agents"].values()})
    bottom = footnote(fig, "Grey: baselines (with the safety mechanism). Coloured: DQN agents; dot = mean over "
                      f"{' or '.join(map(str, seeds))} seeds, bar = 95% bootstrap interval over seeds, ticks = "
                      "individual seeds. Unconstrained and penalty-only agents run without enforcement. Pilot data "
                      "(one developer's ratings), not Directorate data.", 190)
    fig.tight_layout(rect=(0, bottom, 1, 0.95))
    fig.savefig(path, dpi=150)
    fig.savefig(path.with_suffix(".pdf"))
    plt.close(fig)


def sweep_figure(levels, path):
    sweeps = [("Noise (reversed results)", [(n, 0.0) for n in (0.0, 0.1, 0.2)], 0),
              ("Missing checks (noise 0.1)", [(0.1, m) for m in (0.0, 0.2, 0.4)], 1)]
    metrics = [("mean_return", "Return", False), ("wrong_rate", "Wrong fix", True),
               ("escalation_rate", "Escalated", True), ("mean_checks", "Checks per incident", False)]
    fig, axes = plt.subplots(2, 4, figsize=(14, 6.8))
    for row, (name, keys, which) in enumerate(sweeps):
        xs = [k[which] for k in keys]
        for col, (key, title, percent) in enumerate(metrics):
            ax = axes[row, col]
            for agent, colour in AGENT_COLOURS.items():
                summaries = [levels[k]["agents"].get(agent, {}).get("summary", {}).get(key) for k in keys]
                if any(v is None for v in summaries):
                    continue
                means = [v["mean"] for v in summaries]
                ax.fill_between(xs, [v["ci"][0] for v in summaries], [v["ci"][1] for v in summaries],
                                color=colour, alpha=0.15, linewidth=0)
                ax.plot(xs, means, "-o", color=colour, linewidth=2, markersize=6, label=AGENT_LABELS[agent])
            for label, ls in ((f"Threshold (tau={THRESHOLD_TAU})", (0, (4, 3))), ("Exact optimal", (0, (1, 2)))):
                values = [levels[k]["baselines"].get(label, {}).get(key) for k in keys]
                pts = [(x, v) for x, v in zip(xs, values) if v is not None]
                if pts:
                    ax.plot(*zip(*pts), linestyle=ls, marker="s", markersize=4, color=MUTED if "Thr" in label else INK,
                            linewidth=1.3, label=label.split(" (")[0])
            ax.set_xticks(xs, [f"{x:.0%}" for x in xs])
            ax.set_xlabel(name, color=MUTED)
            ax.set_title(title, loc="left", fontsize=10, fontweight="bold", color=INK)
            ax.grid(True, color=GRID, linewidth=0.8)
            ax.set_axisbelow(True)
            for side in ("top", "right"):
                ax.spines[side].set_visible(False)
            if percent:
                ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=len(labels), frameon=False, bbox_to_anchor=(0.5, 0.95))
    fig.suptitle("Robustness: saved agents scored at other ambiguity levels without retraining",
                 x=0.01, ha="left", fontsize=11, fontweight="bold", color=INK)
    bottom = footnote(fig, "Agents: mean over seeds with a 95% bootstrap band. The exact policy exists only without "
                      "missing checks. Pilot data, not Directorate data.", 220)
    fig.tight_layout(rect=(0, bottom, 1, 0.92))
    fig.savefig(path, dpi=150)
    fig.savefig(path.with_suffix(".pdf"))
    plt.close(fig)


def blocked_figure(curves, path):
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for agent, df in curves.items():
        g = df.groupby("step")["proposed_violation_rate"]
        mean, low, high = g.mean(), g.min(), g.max()
        ax.fill_between(mean.index, low, high, color=AGENT_COLOURS[agent], alpha=0.15, linewidth=0)
        ax.plot(mean.index, mean, color=AGENT_COLOURS[agent], linewidth=2, label=AGENT_LABELS[agent])
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{x / 1000:,.0f}k"))
    ax.set_xlabel("Training step", color=MUTED)
    ax.set_ylabel("Proposals that break a rule", color=MUTED)
    ax.set_title("Does the agent learn to act within the rules?", loc="left", fontsize=11, fontweight="bold")
    ax.grid(True, color=GRID, linewidth=0.8)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(frameon=False, loc="upper right")
    bottom = footnote(fig, "Mean over seeds; band = lowest to highest seed. With the mechanism these proposals are "
                      "blocked; without it they execute. Monitoring incidents, not the evaluation incidents. "
                      "Pilot data, not Directorate data.", 125)
    fig.tight_layout(rect=(0, bottom, 1, 1))
    fig.savefig(path, dpi=150)
    fig.savefig(path.with_suffix(".pdf"))
    plt.close(fig)


# ----- Tables ----------------------------------------------------------------
def fmt(value, percent):
    if value is None:
        return "n/a"
    return f"{value:.1%}" if percent else f"{value:.2f}"


def table(base, n_eval):
    cols = [("Return", "mean_return", False), ("Correct", "resolution_accuracy", True),
            ("Wrong", "wrong_rate", True), ("Escalated", "escalation_rate", True), ("Checks", "mean_checks", False),
            ("Esc. MCC", "escalation_mcc", False), ("Blocked or broken proposals", "proposed_violation_rate", True),
            ("Forced esc.", "forced_escalation_rate", True), ("Rule broken (executed)", "executed_violation_rate", True),
            ("Compliant success", "compliant_success_rate", True)]
    lines = [f"# Phase 5 results (base level)", "",
             f"{n_eval:,} evaluation incidents, the same for every policy; noise 0.1, no missing checks. Agents: "
             "mean over their seeds, with the 95% bootstrap interval over seeds for the return. Unconstrained and "
             "penalty-only agents run without enforcement and without the training penalty. Pilot data, not "
             "Directorate data.", "",
             "| Policy | " + " | ".join(c[0] for c in cols) + " |", "|---" * (len(cols) + 1) + "|"]
    for label, m in base["baselines"].items():
        lines.append(f"| {label} | " + " | ".join(fmt(m[k], p) for _, k, p in cols) + " |")
    for agent, data in base["agents"].items():
        s = data["summary"]
        cells = []
        for _, k, p in cols:
            cell = fmt(s[k]["mean"], p) if k in s else "n/a"
            if k == "mean_return":
                cell += f" [{s[k]['ci'][0]:.2f}, {s[k]['ci'][1]:.2f}]"
            cells.append(cell)
        lines.append(f"| {AGENT_LABELS[agent]} ({len(data['per_seed'])} seeds) | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def draw_figures(levels, agents, n_eval, prefix):
    FIGURES.mkdir(parents=True, exist_ok=True)
    comparison_figure(levels[BASE], FIGURES / f"{prefix}_comparison.png", n_eval)
    sweep_figure(levels, FIGURES / f"{prefix}_sweep.png")
    blocked_figure(training_curves(agents), FIGURES / f"{prefix}_blocked_over_training.png")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--n-eval", type=int, default=5000)
    parser.add_argument("--n-sweep", type=int, default=2000)
    parser.add_argument("--allow-missing", action="store_true")
    parser.add_argument("--out-prefix", default="phase5")
    parser.add_argument("--replot", action="store_true", help="redraw the figures from the saved results only")
    args = parser.parse_args()
    started = time.time()
    if args.replot:
        saved = json.loads((OUT / f"{args.out_prefix}.json").read_text(encoding="utf-8"))
        levels = {tuple(float(part.split("=")[1]) for part in key.split(",")): value
                  for key, value in saved["levels"].items()}
        agents = {a: dict.fromkeys(seeds) for a, seeds in saved["seeds"].items()}
        draw_figures(levels, agents, saved["n_eval"], args.out_prefix)
        print("Figures redrawn from", OUT / f"{args.out_prefix}.json")
        return
    s = scenario()
    agents = available_agents(args.allow_missing)
    print("Agents:", {a: sorted(m) for a, m in agents.items()})

    levels = {}
    for noise, miss in LEVELS:
        n = args.n_eval if (noise, miss) == BASE else args.n_sweep
        levels[(noise, miss)] = evaluate_level(s, agents, noise, miss, n)
        print(f"  level noise={noise} missing={miss} done ({time.time() - started:.0f} s)", flush=True)
    base = levels[BASE]
    draw_figures(levels, agents, args.n_eval, args.out_prefix)
    out = {"note": "Pilot data, not Directorate data.", "n_eval": args.n_eval, "n_sweep": args.n_sweep,
           "seeds": {a: sorted(m) for a, m in agents.items()},
           "levels": {f"noise={k[0]},missing={k[1]}": v for k, v in levels.items()}}
    (OUT / f"{args.out_prefix}.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    (OUT / f"{args.out_prefix}.md").write_text(table(base, args.n_eval), encoding="utf-8")
    print(table(base, args.n_eval))
    print(f"Done in {time.time() - started:.0f} s")


if __name__ == "__main__":
    main()
