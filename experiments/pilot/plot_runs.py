"""Compares training runs on the essential measures, as a static figure for the write-up.

    python -m experiments.pilot.plot_runs RUN [RUN ...] --out results/pilot/figures/phase4_runs.png

Each panel shows the monitoring evaluations (thin) and a three-evaluation rolling mean (thick).
Dashed grey lines are references measured on the same monitoring incidents.
"""
import argparse
import json
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                              # noqa: E402
import pandas as pd                                          # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "results" / "pilot" / "runs"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]                  # categorical slots 1-3, validated all-pairs
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e1"

PANELS = [
    ("mean_return", "Return", "Mean return", {"Exact optimal": ("Exact optimal", "mean_return"),
                                              "Threshold": ("Threshold (0.65)", "mean_return"),
                                              "Always escalate": ("Always escalate", "mean_return")}, False),
    ("resolution_accuracy", "Resolved correctly", "Share of incidents",
     {"Exact optimal": ("Exact optimal", "resolution_accuracy")}, True),
    ("escalation_rate", "Escalated", "Share of incidents", {"Exact optimal": ("Exact optimal", "escalation_rate")}, True),
    ("mean_checks", "Checks per incident", "Checks", {"Exact optimal": ("Exact optimal", "mean_checks")}, False),
    ("learned_start_value", "Value at the start of an incident (learned)", "Expected return",
     {"Exact": (None, "exact_value")}, False),
    ("proposed_violation_rate", "Proposals blocked by the safety mechanism", "Share of proposals", {}, True),
]


def load(run):
    folder = RUNS / run
    config = json.loads((folder / "config.json").read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in (folder / "metrics.jsonl").read_text(encoding="utf-8").splitlines() if line]
    return config, pd.DataFrame(rows)


def label_for(config, run):
    hp = config["hyperparameters"]
    kind = "Double DQN" if hp.get("double_q") else "DQN"
    return f"{kind}, {config['steps'] // 1000:,}k steps"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("runs", nargs="+")
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "pilot" / "figures" / "phase4_runs.png")
    parser.add_argument("--footnote", default="", help="extra text for the note under the figure")
    args = parser.parse_args()
    if len(args.runs) > len(SERIES):
        raise SystemExit(f"At most {len(SERIES)} runs per figure; facet the rest.")

    runs = [(run, *load(run)) for run in args.runs]
    refs = runs[0][1]["references"]
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": MUTED,
                         "xtick.color": MUTED, "ytick.color": MUTED, "axes.titlecolor": INK})
    fig, axes = plt.subplots(3, 2, figsize=(11, 10.5), sharex=True)

    for ax, (key, title, y_label, references, percent) in zip(axes.flat, PANELS):
        # Later runs are drawn first, so a shorter run stays visible where a longer one repeats it.
        for order, ((run, config, df), colour) in enumerate(reversed(list(zip(runs, SERIES)))):
            ax.plot(df["step"], df[key], color=colour, linewidth=0.8, alpha=0.35, zorder=2 + order)
            ax.plot(df["step"], df[key].rolling(3, min_periods=1).mean(), color=colour, linewidth=2,
                    label=label_for(config, run), zorder=2 + order)
        for n, (name, (ref_key, field)) in enumerate(references.items()):
            value = refs[ref_key][field] if ref_key else runs[0][1].get(field)
            if value is None:
                continue
            ax.axhline(value, color=MUTED, linewidth=1, linestyle=(0, (4, 3)), zorder=1)
            left = name == "Threshold"                        # clear of the exact label and the late curves
            ax.annotate(f"{name} {value:.0%}" if percent else f"{name} {value:.2f}", xy=(0 if left else 1, value),
                        xycoords=("axes fraction", "data"), xytext=(4 if left else -4, 3),
                        textcoords="offset points", ha="left" if left else "right", va="bottom",
                        fontsize=8, color=MUTED)
        ax.set_title(title, loc="left", fontsize=10, fontweight="bold")
        ax.set_ylabel(y_label)
        ax.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        if percent:
            ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    for ax in axes[-1]:
        ax.set_xlabel("Training step")
        ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{x / 1000:,.0f}k"))
    axes[0, 0].set_ylim(-3, 1)                                # the first evaluations (about -8) are off scale
    axes[0, 1].set_ylim(0, 1)
    axes[1, 0].set_ylim(0, 1)
    axes[2, 1].set_ylim(0, None)

    handles, labels = axes[0, 0].get_legend_handles_labels()
    handles, labels = handles[::-1], labels[::-1]             # back to the order the runs were given
    fig.legend(handles, labels, loc="upper center", ncol=len(runs), frameon=False, bbox_to_anchor=(0.5, 0.955))
    fig.suptitle("Pilot training runs: shielded agent, tuning seed 100, base level (noise 0.1)",
                 x=0.02, y=0.99, ha="left", fontsize=12, fontweight="bold", color=INK)
    note = (f"Each point: {runs[0][1]['incidents']:,} monitoring incidents, no exploration. Thin lines: each "
            "evaluation; thick: rolling mean of three. Return panel starts at -3; the first evaluations "
            "(about -8) are off scale. Pilot data (one developer's ratings), not Directorate data.")
    if args.footnote:
        note += " " + args.footnote
    note = "\n".join(textwrap.wrap(note, 175))
    fig.text(0.02, 0.008, note, fontsize=8, color=MUTED, va="bottom")
    fig.tight_layout(rect=(0, 0.012 + 0.014 * note.count("\n") + 0.014, 1, 0.93))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=150)
    fig.savefig(args.out.with_suffix(".pdf"))
    print(f"Saved {args.out} and {args.out.with_suffix('.pdf').name}")


if __name__ == "__main__":
    main()
