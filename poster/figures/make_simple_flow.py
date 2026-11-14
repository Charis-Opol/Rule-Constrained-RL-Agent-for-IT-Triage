"""Draws the plain-language flow diagram for the poster (no jargon, five boxes, left to right).

Writes simple_flow.svg, simple_flow.png (300 dpi) and simple_flow.pdf (used by poster.tex)
next to this script. Sizes are in millimetres at print size, so the fonts below are the
printed point sizes when the figure is placed at its natural width (800 mm) on the A1 poster.

    python poster/figures/make_simple_flow.py

The wording follows what the prototype does (src/prototype/triage.py, reading.py,
rules/safety.py, verify.py, actions.py):
  1. a ticket and its logs come in;
  2. a reader picks out symptoms and evidence, quoting each line it relies on (it never decides);
  3. the trained agent chooses: run a check, apply a fix, or escalate to a person;
  4. the rule checker blocks forbidden fixes; a second block in a row escalates;
  5. a fix is verified, then carried out as a draft change for review or a note to the owner,
     or the incident is handed over; each outcome is written to a record.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt                                    # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch     # noqa: E402

HERE = Path(__file__).resolve().parent
MM = 1 / 25.4                                     # inches per millimetre

NAVY, RED, INK = "#0B2E59", "#9B1111", "#111111"  # white on each: contrast above 10:1
BOXES = [
    ("A problem\nreport comes in", NAVY,
     "Someone reports a fault. The system's log is attached."),
    ("Key facts are\npicked out", NAVY,
     "Each fact is copied word for word from the report or log, so a person can check it."),
    ("The assistant\nchooses a step", NAVY,
     "Look into it further, try a fix, or hand it to a person."),
    ("Rulebook\ncheck", RED,
     "Steps the team's rules forbid are blocked. Blocked twice, a person takes over."),
    ("Action is taken\nand recorded", NAVY,
     "Fixes are tested first and wait for a person's approval. Every outcome is written down."),
]

W, H = 800, 118                 # figure size, mm
BOX_W, BOX_H, GAP = 132, 60, 27
TOP = H - 4
LABEL_PT, TEXT_PT = 40, 27


def wrap(text, width):
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return "\n".join(lines + [line])


def main():
    plt.rcParams.update({"font.family": ["Arial", "DejaVu Sans"], "svg.fonttype": "path"})
    fig = plt.figure(figsize=(W * MM, H * MM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")

    x = (W - (5 * BOX_W + 4 * GAP)) / 2
    for i, (label, colour, sentence) in enumerate(BOXES):
        ax.add_patch(FancyBboxPatch((x, TOP - BOX_H), BOX_W, BOX_H, boxstyle="round,pad=0,rounding_size=6",
                                    facecolor=colour, edgecolor="none"))
        ax.text(x + BOX_W / 2, TOP - BOX_H / 2, label, ha="center", va="center", color="white",
                fontsize=LABEL_PT, fontweight="bold", linespacing=1.05)
        ax.text(x + BOX_W / 2, TOP - BOX_H - 6, wrap(sentence, 24), ha="center", va="top", color=INK,
                fontsize=TEXT_PT, linespacing=1.15)
        if i < len(BOXES) - 1:
            ax.add_patch(FancyArrowPatch((x + BOX_W + 3, TOP - BOX_H / 2), (x + BOX_W + GAP - 3, TOP - BOX_H / 2),
                                         arrowstyle="-|>,head_length=9,head_width=6", mutation_scale=1,
                                         linewidth=6, color=INK))
        x += BOX_W + GAP

    for ext, kwargs in (("svg", {}), ("pdf", {}), ("png", {"dpi": 300})):
        fig.savefig(HERE / f"simple_flow.{ext}", facecolor="white", **kwargs)
    print("wrote", ", ".join(f"simple_flow.{e}" for e in ("svg", "pdf", "png")))


if __name__ == "__main__":
    main()
