"""Training curves for the v3 comparison runs (fix with verification).

    python -m experiments.pilot.plot_v3_training

Reads results/pilot/runs/v3_*/metrics.jsonl (the training monitor: 1,000 fixed monitoring
incidents every 25k steps, greedy policy, never the evaluation incidents) and writes
results/pilot/figures/v3_training_*.{png,pdf}:
  - v3_training_agents: the three agents (Experiment 2), six measures over training;
  - v3_training_compliance: rule-breaking proposals and executed violations over training;
  - v3_training_sensitivity: the shielded agent at escalation 60 / 120 / 240 min;
  - v3_training_seeds: every seed of every run on return, to show the spread.
Lines are the mean over seeds; bands run from the lowest to the highest seed.
"""
import json
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                              # noqa: E402
import pandas as pd                                          # noqa: E402

from experiments.pilot.run_comparison import AGENTS, BASE_ESCALATION, RUNS, SEEDS, SENSITIVITY_ESCALATION, run_name  # noqa: E402

FIGURES = RUNS.parent / "figures"
INK, MUTED, GRID, REF = "#0b0b0b", "#52514e", "#e6e5e1", "#8a8985"
AGENT_COLOURS = {"shielded": "#2a78d6", "unconstrained": "#eb6834", "penalty": "#1baf7a"}
AGENT_LABELS = {"shielded": "With safety mechanism", "unconstrained": "Unconstrained", "penalty": "Penalty-only"}
ESC_COLOURS = {60.0: "#86b6ef", 120.0: "#2a78d6", 240.0: "#104281"}     # one hue, light -> dark = cheap -> costly
PANELS = [("mean_return", "Return per incident (hours)", False),
          ("resolution_accuracy", "Resolved correctly", True),
          ("wrong_fix_rate", "Incidents with a wrong fix applied", True),
          ("escalation_rate", "Escalated", True),
          ("mean_checks", "Checks per incident", False),
          ("proposed_violation_rate", "Proposals that break a rule", True)]
NOTE = ("Training monitor: 1,000 fixed monitoring incidents every 25k steps, greedy policy (not the evaluation "
        "incidents). Line = mean over seeds; band = lowest to highest seed. Model v2 (pilot developer, Part 2) with "
        "fix-with-verification settings; the verification values are researcher-provisional. Pilot data, not "
        "Directorate data.")


def load(name):
    path = RUNS / name / "metrics.jsonl"
    if not path.exists():
        return None
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return pd.DataFrame(rows)


def references(name):
    return json.loads((RUNS / name / "config.json").read_text(encoding="utf-8")).get("references", {})


def group(agent, escalation=None):
    frames = [df.assign(seed=s) for s in SEEDS if (df := load(run_name(agent, s, escalation))) is not None]
    return pd.concat(frames) if frames else None


def style(ax, title, percent):
    ax.set_title(title, loc="left", fontsize=10.5, fontweight="bold", color=INK)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{x / 1000:,.0f}k"))
    if percent:
        ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))


def band(ax, df, key, colour, label):
    g = df.groupby("step")[key]
    mean = g.mean()
    ax.fill_between(mean.index, g.min(), g.max(), color=colour, alpha=0.15, linewidth=0)
    ax.plot(mean.index, mean, color=colour, linewidth=2, label=label)


def reference_lines(ax, refs, key):
    for label, ls in (("Threshold (0.65)", (0, (4, 3))), ("Always escalate", (0, (1, 2)))):
        value = refs.get(label, {}).get(key)
        if value is not None:
            ax.axhline(value, color=REF, linestyle=ls, linewidth=1.3, label=label.replace(" (0.65)", " baseline")
                       if "Thr" in label else "Always-escalate baseline")


def finish(fig, name, note, top=0.9, width=200):
    wrapped = "\n".join(textwrap.wrap(note, width))
    fig.text(0.01, 0.01, wrapped, fontsize=8, color=MUTED, va="bottom")
    bottom = (wrapped.count("\n") + 1) * 0.03 + 0.025
    fig.tight_layout(rect=(0, bottom, 1, top))
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / f"{name}.png", dpi=170)
    fig.savefig(FIGURES / f"{name}.pdf")
    plt.close(fig)
    print("wrote", FIGURES / f"{name}.png")


def agents_figure(data, refs):
    fig, axes = plt.subplots(2, 3, figsize=(14, 7.6))
    for ax, (key, title, percent) in zip(axes.flat, PANELS):
        for agent, df in data.items():
            band(ax, df, key, AGENT_COLOURS[agent], AGENT_LABELS[agent])
        if key != "proposed_violation_rate":
            reference_lines(ax, refs, key)
        style(ax, title, percent)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=len(labels), frameon=False, bbox_to_anchor=(0.5, 0.945),
               fontsize=9.5)
    fig.suptitle("Training the three agents with fix-and-verify (Experiment 2 runs, 3 seeds each)", x=0.01,
                 ha="left", fontsize=12.5, fontweight="bold", color=INK)
    finish(fig, "v3_training_agents", NOTE + " Baselines: the same monitoring incidents, with the safety mechanism.",
           top=0.9)


def compliance_figure(data):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
    for ax, (key, title) in zip(axes, (("proposed_violation_rate", "Proposals that break a rule (blocked or not)"),
                                       ("executed_violation_rate", "Incidents where a rule was actually broken"))):
        for agent, df in data.items():
            band(ax, df, key, AGENT_COLOURS[agent], AGENT_LABELS[agent])
        style(ax, title, True)
        ax.set_xlabel("Training step", color=MUTED)
    axes[0].legend(frameon=False, fontsize=9)
    fig.suptitle("Does each agent learn to act within the rules?", x=0.01, ha="left", fontsize=12.5,
                 fontweight="bold", color=INK)
    finish(fig, "v3_training_compliance", "With the safety mechanism a rule-breaking proposal is blocked, so no rule "
           "is broken by construction; without it the proposal executes. " + NOTE, top=0.92, width=170)


def sensitivity_figure(sens):
    panels = [p for p in PANELS if p[0] in ("resolution_accuracy", "wrong_fix_rate", "escalation_rate", "mean_checks")]
    fig, axes = plt.subplots(1, 4, figsize=(15, 4.4))
    for ax, (key, title, percent) in zip(axes, panels):
        for esc, df in sens.items():
            band(ax, df, key, ESC_COLOURS[esc], f"Escalation {esc:g} min" + (" (elicited)" if esc == BASE_ESCALATION
                                                                              else ""))
        style(ax, title, percent)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=len(labels), frameon=False, bbox_to_anchor=(0.5, 0.92),
               fontsize=9.5)
    fig.suptitle("Sensitivity: the agent with the safety mechanism, retrained at three costs of escalation", x=0.01,
                 ha="left", fontsize=12.5, fontweight="bold", color=INK)
    finish(fig, "v3_training_sensitivity", "A wrong fix keeps the elicited 5x escalation, so its harm scales with the "
           "cost. Return is left out because it is in different units at each cost. " + NOTE, top=0.86, width=210)


def seeds_figure(data, sens):
    runs = [(AGENT_LABELS[a], AGENT_COLOURS[a], data[a]) for a in data] +         [(f"Safety mechanism, esc. {e:g} min", ESC_COLOURS[e], df) for e, df in sens.items() if e != BASE_ESCALATION]
    styles = {0: "-", 1: (0, (5, 2)), 2: (0, (1, 1.5))}
    fig, axes = plt.subplots(1, len(runs), figsize=(3.3 * len(runs), 3.9))
    for ax, (label, colour, df) in zip(axes, runs):
        for seed, d in df.groupby("seed"):
            ax.plot(d["step"], d["mean_return"], color=colour, linewidth=1.6, linestyle=styles.get(seed, "-"),
                    label=f"seed {seed}")
        later = df[df["step"] >= 25_000]["mean_return"]       # step 0 is the untrained network
        if len(later):
            pad = 0.15 * (later.max() - later.min() or 1)
            ax.set_ylim(later.min() - pad, later.max() + pad)
        style(ax, label, False)
        ax.set_title(label, loc="left", fontsize=9.5, fontweight="bold", color=INK)
    axes[0].set_ylabel("Return per incident (hours)", color=MUTED)
    handles = [matplotlib.lines.Line2D([], [], color=MUTED, linewidth=1.6, linestyle=ls) for ls in styles.values()]
    labels = [f"seed {k}" for k in styles]
    fig.legend(handles, labels, loc="upper right", ncol=3, frameon=False, fontsize=9, bbox_to_anchor=(0.995, 0.99))
    fig.suptitle("Every seed: return over training", x=0.01, ha="left", fontsize=12.5, fontweight="bold", color=INK)
    finish(fig, "v3_training_seeds", "Return on the monitoring incidents; the axis starts after the untrained network "
           "at step 0. Returns at different escalation costs are in different units and are not comparable across "
           "panels. Pilot data, not Directorate data.", top=0.9, width=230)


def main():
    data = {a: df for a in AGENTS if (df := group(a)) is not None}
    sens = {e: df for e in sorted({BASE_ESCALATION, *SENSITIVITY_ESCALATION})
            if (df := group("shielded", None if e == BASE_ESCALATION else e)) is not None}
    if not data:
        raise SystemExit("No v3 runs found")
    refs = references(run_name("shielded", SEEDS[0]))
    agents_figure(data, refs)
    compliance_figure(data)
    sensitivity_figure(sens)
    seeds_figure(data, sens)


if __name__ == "__main__":
    main()
