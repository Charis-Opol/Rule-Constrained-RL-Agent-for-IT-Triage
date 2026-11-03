"""Draw Fig1 (PRISMA flow), Fig2 (coverage bars) and Fig3 (evidence map) for the submission.

Run:  python -I make_figures.py <slr_dir> <out_dir>

Vector output drawn with matplotlib: EPS for submission and PDF for local compilation, both with
the Arial font embedded as TrueType (Type 42). All lettering is 8 pt Arial, black on white or light
grey (contrast above 4.5:1), lines 0.6 pt, and nothing is conveyed by colour alone. The counts are
read from the review's generated files, so the figures cannot drift from the tables.
"""
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

SLR, OUT = Path(sys.argv[1]), Path(sys.argv[2]) / 'source'
TABLE_REASONS = sys.argv[3] if len(sys.argv) > 3 else '9'  # number of the title/abstract reasons table

plt.rcParams.update({
    'font.family': 'Arial', 'font.size': 8, 'ps.fonttype': 42, 'pdf.fonttype': 42,
    'axes.linewidth': 0.6, 'xtick.major.width': 0.6, 'ytick.major.width': 0.6,
    'xtick.labelsize': 8, 'ytick.labelsize': 8, 'axes.labelsize': 8,
    'svg.fonttype': 'none',
})
MM = 1 / 25.4
LW = 0.6
GREY = '#e6e6e6'   # black text on this grey: contrast about 17:1
DARK = '#7f7f7f'   # bar fill; value labels sit outside the bar on white

c = dict(re.findall(r'\\newcommand\{\\(N[A-Za-z]+)\}\{([^}]*)\}',
                    (SLR / 'tables/counts.tex').read_text(encoding='utf-8')))


def save(fig, name):
    for ext in ('eps', 'pdf'):
        fig.savefig(OUT / f'{name}.{ext}', format=ext)
    plt.close(fig)


# --------------------------------------------------------------------------- Fig1: PRISMA flow

def box(ax, x, y, w, h, text, fill='white', ha='left', bold=False, rotate=False):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fill, edgecolor='black', linewidth=LW))
    if rotate:
        ax.text(x + w / 2, y + h / 2, text, rotation=90, ha='center', va='center',
                fontweight='bold' if bold else 'normal')
    elif ha == 'center':
        ax.text(x + w / 2, y + h / 2, text, ha='center', va='center', linespacing=1.3)
    else:
        ax.text(x + 1.6, y + h - 1.6, text, ha='left', va='top', linespacing=1.3)


def arrow(ax, x0, y0, x1, y1):
    ax.annotate('', xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle='-|>', linewidth=LW, color='black', mutation_scale=7,
                                shrinkA=0, shrinkB=0))


W, H = 131, 150
fig = plt.figure(figsize=(W * MM, H * MM))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis('off')

sx, sw = 1, 7          # stage label bars
lx, lw = 11, 56        # left boxes
rx, rw = 71, 59.5      # right boxes

rows = {  # name: (y, h)
    'id': (122, 27), 'scr': (95, 11), 'sought': (73, 8), 'ass': (40, 8), 'inc': (6, 15),
}
box(ax, lx, rows['id'][0], lw, rows['id'][1],
    f"Records identified from databases\n(n = {c['NIdentified']}):\n"
    f"   Scopus (n = {c['NScopus']})\n   ACM Digital Library (n = {c['NACM']})\n"
    f"   IEEE Xplore (n = {c['NIEEE']})")
box(ax, rx, 122, rw, 27,
    "Records removed before screening:\n"
    f"   Duplicates (n = {c['NDuplicates']})\n   Removed by automation (n = {c['NAuto']}):\n"
    f"      document type (n = {c['NAutoType']})\n      publication year (n = {c['NAutoYear']})\n"
    f"      string blocks not matched (n = {c['NAutoString']})")
box(ax, lx, rows['scr'][0], lw, rows['scr'][1],
    f"Records screened on title and abstract\n(n = {c['NScreened']})")
box(ax, rx, 95, rw, 11, f"Records excluded (n = {c['NExclTA']})\n(reasons in Table {TABLE_REASONS})")
box(ax, lx, rows['sought'][0], lw, rows['sought'][1], f"Reports sought for retrieval (n = {c['NSought']})")
box(ax, rx, 66, rw, 15,
    f"Reports not retrieved (n = {c['NNotRetrieved']}):\n"
    f"   closed access or abstract only (n = {c['NNotRetClosed']})\n"
    f"   no full text and no reason recorded (n = {c['NNotRetNoRecord']})")
box(ax, lx, rows['ass'][0], lw, rows['ass'][1], f"Reports assessed for eligibility (n = {c['NAssessed']})")
box(ax, rx, 28, rw, 27,
    f"Reports excluded (n = {c['NExclFT']}):\n"
    f"   classifier or detector evaluation only\n      (n = {c['NFTDetect']})\n"
    "   no measured results (n = 1)\n   out of scope, manual judgement (n = 1)\n"
    "   not in English (n = 1)")
box(ax, lx, rows['inc'][0], lw, rows['inc'][1],
    f"Studies included in the review (n = {c['NIncluded']})\n"
    f"Reports of included studies (n = {c['NIncluded']})")

box(ax, sx, 122, sw, 27, 'Identification', fill=GREY, bold=True, rotate=True)
box(ax, sx, 28, sw, 90, 'Screening', fill=GREY, bold=True, rotate=True)
box(ax, sx, 6, sw, 15, 'Included', fill=GREY, bold=True, rotate=True)

mid = lx + lw / 2
arrow(ax, mid, 122, mid, 106)
arrow(ax, mid, 95, mid, 81)
arrow(ax, mid, 73, mid, 48)
arrow(ax, mid, 40, mid, 21)
for y in (135.5, 100.5, 77, 44):
    arrow(ax, lx + lw, y, rx, y)
save(fig, 'Fig1')

# --------------------------------------------------------------------------- Fig2: coverage bars

coords = (SLR / 'tables/fig_coverage_coords.tex').read_text(encoding='utf-8')
pairs = re.findall(r'\((\d+),\{([^}]*)\}\)', coords)
values = [int(v) for v, _ in pairs]
labels = [l for _, l in pairs]
n = int(c['NIncluded'])

fig = plt.figure(figsize=(120 * MM, 78 * MM))
ax = fig.add_axes([0.33, 0.13, 0.62, 0.84])
ypos = range(len(values))
ax.barh(list(ypos), values, height=0.6, color=DARK, edgecolor='black', linewidth=LW)
for y, v in zip(ypos, values):
    ax.text(v + 0.5, y, str(v), va='center', ha='left')
ax.set_yticks(list(ypos))
ax.set_yticklabels(labels)
ax.invert_yaxis()
ax.set_xlim(0, n)
ax.set_xticks(range(0, n + 1, 5))
ax.set_xlabel(f'Studies (of {n})')
for side in ('top', 'right'):
    ax.spines[side].set_visible(False)
save(fig, 'Fig2')

# --------------------------------------------------------------------------- Fig3: evidence map

fig = plt.figure(figsize=(120 * MM, 72 * MM))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 120)
ax.set_ylim(0, 72)
ax.axis('off')

comps = [
    ('Belief over hidden\nincident cause', f"{c['NBelief']} studies, all security"),
    ('Costed investigate action', f"{c['NInfo']} studies; effort reduced"),
    ('Learned escalation', f"{c['NEsc']} studies; learned in four,\nall security"),
    ('Rule mechanism with\nblocked-action handling',
     f"{c['NShield']} hard filters; {c['NBlocked']} report\nblocked handling; no re-proposal"),
]
top, h, gap = 70, 11, 3
for i, (comp, ev) in enumerate(comps):
    y = top - (i + 1) * h - i * gap
    ax.add_patch(FancyBboxPatch((2, y), 50, h, boxstyle='round,pad=0,rounding_size=1.2',
                                facecolor=GREY, edgecolor='black', linewidth=LW))
    ax.text(27, y + h / 2, comp, ha='center', va='center', linespacing=1.2)
    arrow(ax, 52, y + h / 2, 60, y + h / 2)
    ax.text(62, y + h / 2, ev, ha='left', va='center', linespacing=1.2)
yb = top - 4 * h - 3 * gap - 12
ax.add_patch(Rectangle((10, yb), 100, 8, facecolor='white', edgecolor='black', linewidth=1.2,
                       hatch='////'))
ax.add_patch(Rectangle((22, yb + 1.5), 76, 5, facecolor='white', edgecolor='none'))
ax.text(60, yb + 4, 'All four combined for IT service incidents: no study', ha='center', va='center',
        fontweight='bold')
save(fig, 'Fig3')
print('wrote Fig1-3 (.eps, .pdf)')
