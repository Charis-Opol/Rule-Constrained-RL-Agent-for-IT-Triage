"""Build the pilot-results poster (A0 landscape) from the proposal poster's header and style.

Layout follows the sample template (Uganda_MFI_Credit_Risk_Poster.pptx): Introduction,
Problem Statement & Objectives, Conclusions & Next Steps | System Architecture,
Implementation, stat callouts, Alignment | Results, Challenges | Areas of Improvement,
Other information (contacts and references). Content is from pilot_report.tex.

Run from the repository root:  python documentation/pilot-report/build_poster.py
"""
import copy
from pathlib import Path

from lxml import etree
from PIL import Image, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "research/proposal/Opol_Charis_Research_Poster.pptx"
OUT = ROOT / "documentation/pilot-report/Opol_Charis_Pilot_Poster.pptx"
FIG = ROOT / "results/pilot/figures"
CROP = {  # name: (top, bottom) in pixels; drops the figure title and footnote
    "comparison_outcomes.png": (55, 800),
    "v3_training_compliance.png": (115, 640),
    "comparison_sensitivity.png": (50, 570),
}
TMP = ROOT / "documentation/pilot-report/poster_figs"

RED, BLUE = "C0392B", "0070C0"
INK, GREY, GREEN = "1A1A1A", "555555", "1E8449"
FONT = "Trebuchet MS"
F_REG = ImageFont.truetype("C:/Windows/Fonts/trebuc.ttf", 100)
F_BOLD = ImageFont.truetype("C:/Windows/Fonts/trebucbd.ttf", 100)

COL_X = [0.45, 12.03, 23.61, 35.18]
COL_W, PAD, TOP, BOTTOM, GAP = 11.18, 0.25, 3.75, 32.72, 0.4
INNER_W = COL_W - 2 * PAD
BODY, SMALL, CAP = 28, 24, 22
LINE = 1.2            # line height factor
SPACE_AFTER = 10      # pt after each paragraph
BUL_IND = 0.38        # inches

prs = Presentation(SRC)
slide = prs.slides[0]

# ---------------------------------------------------------------- keep header only
KEEP = {3, 5, 6, 7, 8}
for sh in list(slide.shapes):
    if sh.shape_id in KEEP:
        continue
    el = sh._element
    for blip in el.iter(qn("a:blip")):
        rid = blip.get(qn("r:embed"))
        if rid:
            slide.part.drop_rel(rid)
    el.getparent().remove(el)


def set_runs(shape, text_lines):
    """Replace the text of a header text box, keeping the first run's formatting."""
    p = shape.text_frame.paragraphs[0]
    r0 = p.runs[0]._r
    for child in list(p._p):
        if child.tag in (qn("a:r"), qn("a:br")):
            p._p.remove(child)
    end = p._p.find(qn("a:endParaRPr"))
    for i, line in enumerate(text_lines):
        if i:
            br = etree.SubElement(p._p, qn("a:br"))
            br.append(copy.deepcopy(r0.find(qn("a:rPr"))))
            end.addprevious(br)
        r = copy.deepcopy(r0)
        r.find(qn("a:t")).text = line
        end.addprevious(r)


for sh in slide.shapes:
    if sh.shape_id == 6:
        set_runs(sh, ["Investigate, Fix or Escalate: A Rule-Constrained Reinforcement",
                      "Learning Agent for IT Incident Triage under Ambiguous Evidence"])
    if sh.shape_id == 7:
        set_runs(sh, ["OPOL CHARIS   |   S24B23/003   |   B29654   |   BSc Computer Science   |   Pilot Experiment Results"])


# ---------------------------------------------------------------- text measurement
def measure(paras, width_in):
    """Height in inches of paragraphs [(runs, bullet, size)] wrapped to width_in."""
    total = 0.0
    for runs, bullet, size in paras:
        w = (width_in - (BUL_IND if bullet else 0)) * 72
        words = []
        for text, bold, _ in runs:
            f = F_BOLD if bold else F_REG
            for i, word in enumerate(text.split(" ")):
                words.append((word, f, i > 0 or (text.startswith(" "))))
        lines, cur = 1, 0.0
        space = F_REG.getlength(" ") * size / 100
        for word, f, _ in words:
            if not word:
                continue
            wl = f.getlength(word) * size / 100
            if cur and cur + space + wl > w:
                lines += 1
                cur = wl
            else:
                cur += (space if cur else 0) + wl
        total += lines * size * LINE + SPACE_AFTER
    return total / 72


def P(*runs, bullet=False, size=BODY):
    """Paragraph from runs; a run is a str (regular) or a tuple (text, bold[, colour])."""
    out = []
    for r in runs:
        if isinstance(r, str):
            out.append((r, False, INK))
        else:
            out.append((r[0], r[1], r[2] if len(r) > 2 else INK))
    return (out, bullet, size)


def B(label, text, size=BODY, colour=INK):
    return P((label, True, colour), (" " + text, False), bullet=True, size=size)


def add_text(x, y, w, paras, align=None):
    h = measure(paras, w)
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, side, 0)
    for i, (runs, bullet, size) in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(SPACE_AFTER)
        if align:
            p.alignment = align
        if bullet:
            pPr = p._p.get_or_add_pPr()
            pPr.set("marL", str(int(Inches(BUL_IND))))
            pPr.set("indent", str(-int(Inches(BUL_IND))))
            bf = etree.SubElement(pPr, qn("a:buFont"))
            bf.set("typeface", "Arial")
            bc = etree.SubElement(pPr, qn("a:buChar"))
            bc.set("char", "\u2022")
        for text, bold, colour in runs:
            r = p.add_run()
            r.text = text
            r.font.size = Pt(size)
            r.font.bold = bold
            r.font.name = FONT
            r.font.color.rgb = RGBColor.from_string(colour)
    return h


def rect(x, y, w, h, fill, line=None, shape=MSO_SHAPE.RECTANGLE, lw=1.5):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.shadow.inherit = False
    if fill:
        s.fill.solid()
        s.fill.fore_color.rgb = RGBColor.from_string(fill)
    else:
        s.fill.background()
    if line:
        s.line.color.rgb = RGBColor.from_string(line)
        s.line.width = Pt(lw)
    else:
        s.line.fill.background()
    return s


def picture(path, x, y, w):
    if path.name in CROP:
        TMP.mkdir(exist_ok=True)
        im = Image.open(path)
        t, b = CROP[path.name]
        im = im.crop((0, t, im.width, b))
        path = TMP / path.name
        im.save(path)
    iw, ih = Image.open(path).size
    h = w * ih / iw
    slide.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w), Inches(h))
    return h


def caption(x, y, w, text):
    return add_text(x, y, w, [P((text, False, GREY), size=CAP)], align=PP_ALIGN.CENTER)


# ---------------------------------------------------------------- sections
class Column:
    def __init__(self, i):
        self.x = COL_X[i]
        self.y = TOP

    def section(self, title, colour, body_fn, fill_to_bottom=False):
        rect(self.x, self.y, COL_W, 0.95, colour)
        add_text(self.x + PAD, self.y + 0.11, INNER_W,
                 [P((title, True, "FFFFFF"), size=44)])
        top = self.y + 0.95
        body = rect(self.x, top, COL_W, 1, "FFFFFF", "D9D9D9")
        h = body_fn(self.x + PAD, top + PAD) + 2 * PAD - SPACE_AFTER / 72
        if fill_to_bottom:
            h = max(h, BOTTOM - top)
        body.height = Inches(h)
        self.y = top + h + GAP
        return top + h


def text_body(paras):
    return lambda x, y: add_text(x, y, INNER_W, paras)


def stack(*items):
    """Body built from a sequence of callables f(x, y) -> height."""
    def fn(x, y):
        y0 = y
        for item in items:
            y += item(x, y)
        return y - y0
    return fn


def T(paras):
    return lambda x, y: add_text(x, y, INNER_W, paras)


def FIGURE(name, cap, w=INNER_W):
    def fn(x, y):
        h = picture(FIG / name, x + (INNER_W - w) / 2, y, w)
        return h + 0.08 + caption(x, y + h + 0.08, INNER_W, cap) + 0.15
    return fn


def table(rows, col_w, size=20, bold_cells=(), highlight_rows=(), row_h=0.5):
    def fn(x, y):
        n, m = len(rows), len(rows[0])
        gt = slide.shapes.add_table(n, m, Inches(x), Inches(y), Inches(sum(col_w)),
                                    Inches(row_h * n))
        tbl = gt.table
        tbl.first_row = True
        for j, cw in enumerate(col_w):
            tbl.columns[j].width = Inches(cw)
        for i in range(n):
            tbl.rows[i].height = Inches(row_h)
            for j in range(m):
                c = tbl.cell(i, j)
                c.margin_left = c.margin_right = Inches(0.06)
                c.margin_top = c.margin_bottom = Inches(0.03)
                c.vertical_anchor = MSO_ANCHOR.MIDDLE
                c.fill.solid()
                if i == 0:
                    c.fill.fore_color.rgb = RGBColor.from_string(BLUE)
                elif i in highlight_rows:
                    c.fill.fore_color.rgb = RGBColor.from_string("EAF2FA")
                else:
                    c.fill.fore_color.rgb = RGBColor.from_string("FFFFFF" if i % 2 else "F5F5F5")
                tf = c.text_frame
                tf.word_wrap = True
                p = tf.paragraphs[0]
                p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
                r = p.add_run()
                r.text = rows[i][j]
                r.font.size = Pt(size)
                r.font.name = FONT
                r.font.bold = i == 0 or (i, j) in bold_cells
                r.font.color.rgb = RGBColor.from_string("FFFFFF" if i == 0 else INK)
        return row_h * n + 0.3
    return fn


# ================================================================ column 1
c1 = Column(0)
c1.section("Introduction", RED, T([
    P("When an IT incident is reported, staff must act before they know its cause: "
      "investigate further, apply a fix, or hand the incident to someone better placed. "
      "The first evidence, an error in the logs or a user's ticket, is often incomplete, "
      "unreliable or consistent with several causes."),
    P("Most AI tools for IT operations treat triage as a single prediction from the ticket. "
      "They cannot ask for more evidence, cannot say that they are unsure, and do not check "
      "their actions against the organisation's operating rules."),
    P("This pilot tests the full method end to end, from a practitioner's ratings to a trained "
      "agent and a working prototype, before the main study with the Directorate of University "
      "ICT Services (UIS)."),
]))

ACH = ("ACHIEVED", True, GREEN)
NOT = ("NOT SUPPORTED", True, RED)
c1.section("Problem Statement and Objectives", RED, T([
    P(("Problem Statement:", True, RED),
      " in the reviewed literature (34 studies, PRISMA 2020), no evaluated agent for IT "
      "incidents learns when to investigate, when to apply a fix that the operational rules "
      "permit, and when to hand the incident to a person. Triage of one incident is a partially "
      "observable decision problem: the cause is hidden, and every action carried out must be "
      "permitted by the rules."),
    P(("Pilot objectives", True, RED)),
    P("Build a scenario model and simulator from a UIS developer's workbooks: ", ACH,
      ".", bullet=True),
    P("Train agents that learn to check, fix or escalate under a rule mechanism: ", ACH,
      " (all three agents learn the three-way decision).", bullet=True),
    P("Zero executed rule violations with the safety mechanism: ", ACH,
      " (0 of 15,000 agent incidents).", bullet=True),
    P("Beat the baselines (H1) and the unconstrained and penalty-only agents on compliant "
      "success (H2): ", NOT, " in this pilot, each for an identifiable cause.", bullet=True),
    P("A prototype that reads a ticket and logs and acts on a repository: ", ACH,
      " (6 of 8 example cases end as intended).", bullet=True),
]))

c1.section("Conclusions & Next Steps", BLUE, T([
    B("A qualified yes.", "The method works end to end: the agent learns a sensible three-way "
      "policy, reaches the strongest baseline on return, responds to the cost of escalation in "
      "the expected direction, and never executes a forbidden action behind the mechanism."),
    B("Two design choices decide the hypotheses:", "judging on resolution alone "
      "rewards repeated fixes (H1); a free block lets the agent lean on the mechanism (H2)."),
    B("Next:", "take the results to UIS and request a Part 3 workbook (remedy times and harms); "
      "charge a block as an ablation; revisit the H1 criterion; run Experiment 4 (missing "
      "checks, noise); score the reader on 20 sample tickets."),
]), fill_to_bottom=True)


# ================================================================ column 2
def architecture(x, y):
    """Native pipeline diagram: ticket to decision, with the rule mechanism in the loop."""
    LB, PK, YL, GR = ("C9DAF8", "6D8FC7"), ("EBC6F3", "A35DB5"), ("FFE699", "BF9000"), ("C6E0B4", "548235")
    xl, wl, xr, wr, bh = x + 0.1, 3.9, x + 5.55, 4.95, 1.25
    rows = [y + 0.15 + i * 2.0 for i in range(4)]

    def box(bx, by, bw, colours, title, sub):
        s = rect(bx, by, bw, bh, colours[0], colours[1], MSO_SHAPE.ROUNDED_RECTANGLE, 2)
        s.adjustments[0] = 0.15
        tf = s.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = Inches(0.08)
        tf.margin_top = tf.margin_bottom = Inches(0.02)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        for i, (t, sz, b) in enumerate([(title, 24, True), (sub, 19, False)]):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = PP_ALIGN.CENTER
            r = p.add_run()
            r.text = t
            r.font.size, r.font.bold, r.font.name = Pt(sz), b, FONT
            r.font.color.rgb = RGBColor.from_string(INK)
        return s

    def arrow(x1, y1, x2, y2, dashed=False):
        c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1),
                                       Inches(x2), Inches(y2))
        c.line.color.rgb = RGBColor.from_string("404040")
        c.line.width = Pt(2.5)
        ln = c.line._get_or_add_ln()
        if dashed:
            d = etree.SubElement(ln, qn("a:prstDash"))
            d.set("val", "dash")
        tail = etree.SubElement(ln, qn("a:tailEnd"))
        tail.set("type", "triangle")
        tail.set("w", "med")
        tail.set("len", "med")

    def label(lx, ly, lw, text, align=PP_ALIGN.CENTER):
        add_text(lx, ly, lw, [P((text, False, GREY), size=18)], align=align)

    box(xl, rows[0], wl, LB, "Ticket + logs", "the incident as reported")
    box(xr, rows[0], wr, LB, "Reader", "LLM or keywords \u2192 fixed evidence form")
    box(xl, rows[1], wl, PK, "Simulator", "Gymnasium, training only")
    box(xr, rows[1], wr, PK, "DQN agent", "proposes: run a check, fix, or escalate")
    box(xl, rows[2], wl, GR, "Routed escalation", "to the owner of the likely cause")
    box(xr, rows[2], wr, YL, "Safety mechanism", "permit, return once, or escalate")
    box(xl, rows[3], wl, GR, "Draft PR or fix order", "never merged, never sent")
    box(xr, rows[3], wr, YL, "Verification on staging", "reproduction test passes, nothing breaks")

    mid_r = xr + wr / 2
    arrow(xl + wl, rows[0] + bh / 2, xr, rows[0] + bh / 2)                     # ticket -> reader
    arrow(mid_r, rows[0] + bh, mid_r, rows[1])                                 # reader -> agent
    arrow(xl + wl, rows[1] + bh / 2, xr, rows[1] + bh / 2, dashed=True)        # env -> agent
    label(xl + wl, rows[1] + bh / 2 - 0.42, xr - xl - wl, "trains")
    arrow(mid_r - 0.6, rows[1] + bh, mid_r - 0.6, rows[2])                     # agent -> mechanism
    arrow(mid_r + 0.6, rows[2], mid_r + 0.6, rows[1] + bh)                     # blocked -> agent
    label(xr, rows[1] + bh + 0.2, wr / 2 - 0.7, "proposal", PP_ALIGN.RIGHT)
    label(mid_r + 0.75, rows[1] + bh + 0.2, wr / 2 - 0.75, "returned once", PP_ALIGN.LEFT)
    arrow(xr, rows[2] + bh / 2, xl + wl, rows[2] + bh / 2)                     # mechanism -> escalation
    label(xl + wl, rows[2] + bh / 2 - 0.62, xr - xl - wl, "escalate or 2nd block")
    arrow(mid_r, rows[2] + bh, mid_r, rows[3])                                 # mechanism -> verify
    label(mid_r + 0.15, rows[2] + bh + 0.2, wr / 2 - 0.15, "permitted fix", PP_ALIGN.LEFT)
    arrow(xr, rows[3] + bh / 2, xl + wl, rows[3] + bh / 2)                     # verify -> PR
    label(xl + wl, rows[3] + bh / 2 + 0.05, xr - xl - wl, "verified")
    arrow(xr, rows[3] + 0.2, xl + wl, rows[2] + bh - 0.2)                      # 2 failed -> escalation
    label(xl + wl + 0.05, rows[3] + 0.28, 1.3, "2 failed", PP_ALIGN.LEFT)

    ky = rows[3] + bh + 0.3
    key = [P(("KEY:  ", True, GREY), ("BLUE \u2013 input   PINK \u2013 learning   "
              "YELLOW \u2013 rules and verification   GREEN \u2013 actions", False, GREY), size=18)]
    kh = add_text(x, ky, INNER_W, key)
    return ky + kh - y


c2 = Column(1)
c2.section("System Architecture", BLUE, architecture)

c2.section("Implementation", BLUE, T([
    B("Scenario model:", "8 causes, 11 checks (one, D11, delegated to a language model), "
      "4 symptoms and 5 rules, from a UIS developer's Part 1 and Part 2 workbooks.", size=26),
    B("Environment:", "Gymnasium, one incident per episode, with noise, missing-check and "
      "overlap controls. Fix with verification: a failed fix costs its harm and is flagged; "
      "after two failed fixes a person takes over.", size=26),
    B("Safety mechanism:", "checks every proposal against the rules; a blocked proposal is "
      "returned once, a second block in a row escalates.", size=26),
    B("Agents:", "masked Double DQN (2 \u00d7 128 units, 500k steps) with the mechanism, "
      "unconstrained, and penalty-only (\u221210 per violation).", size=26),
    B("Evaluation:", "four baselines (always escalate, initial-symptom, scripted checklist, "
      "confidence threshold) on the same 5,000 unseen incidents; escalation 120 min, wrong fix "
      "5\u00d7 escalation; 95% bootstrap intervals.", size=26),
]))


def stats(x, y):
    items = [("0", "Rule violations executed behind the mechanism (of 15,000)", BLUE, "EAF2FA"),
             ("15", "Training runs, 500k steps, 3 seeds each", RED, "FBEAEA"),
             ("6 of 8", "Prototype cases that end as intended", BLUE, "EAF2FA")]
    w, g, h = (INNER_W - 2 * 0.3) / 3, 0.3, 2.1
    for i, (num, lab, col, fill) in enumerate(items):
        bx = x + i * (w + g)
        s = rect(bx, y, w, h, fill, col, MSO_SHAPE.ROUNDED_RECTANGLE, 1.5)
        s.adjustments[0] = 0.08
        add_text(bx + 0.1, y + 0.2, w - 0.2, [P((num, True, col), size=54)], align=PP_ALIGN.CENTER)
        add_text(bx + 0.15, y + 1.15, w - 0.3, [P((lab, False, INK), size=18)], align=PP_ALIGN.CENTER)
    return h + 0.1


# stat callouts sit inside the Implementation panel in the template; here they get their own strip
c2.y -= GAP - 0.05
stat_h = stats(c2.x + PAD, c2.y)
c2.y += stat_h + GAP

c2.section("National & Global Alignment", RED, T([
    B("AI & Robotics Specialisation:", "deep reinforcement learning, decision-making under "
      "uncertainty and safe RL."),
    B("SDG 9 \u2013 Industry, Innovation & Infrastructure:", "reliable, rule-governed automation "
      "of the digital services that infrastructure depends on (Target 9.5)."),
    B("NDP IV:", "supports the Digital Transformation Programme through reliable digital "
      "services and local AI skills."),
    B("Uganda Vision 2040:", "locally developed AI expertise, with ICT as a foundation of "
      "national transformation."),
]), fill_to_bottom=True)


# ================================================================ column 3
c3 = Column(2)
res_rows = [
    ["Policy", "Return (h)", "Resolved", "Wrong fix", "Escal.", "Checks", "Rule broken"],
    ["Always escalate", "\u22122.00", "0%", "0%", "100%", "0.0", "0%"],
    ["Initial-symptom", "\u22122.33", "41.3%", "28.6%", "58.7%", "0.0", "0%"],
    ["Scripted (9 checks)", "\u22121.38", "88.3%", "29.7%", "11.7%", "9.0", "0%"],
    ["Threshold (0.65)", "\u22120.38", "74.1%", "21.4%", "25.9%", "4.7", "0%"],
    ["DQN + safety mech.", "\u22120.41", "67.6%", "22.5%", "32.4%", "5.7", "0%"],
    ["DQN unconstrained", "\u22120.28", "74.7%", "24.9%", "25.3%", "6.0", "7.6%"],
    ["DQN penalty-only", "\u22120.24", "74.7%", "25.4%", "25.3%", "5.0", "0%"],
]
c3.section("Results", BLUE, stack(
    T([P("Experiments 1 and 2: every policy on the same 5,000 incidents, escalation 120 min "
         "(agents: mean of 3 seeds):", size=26)]),
    table(res_rows, [3.0, 1.35, 1.25, 1.3, 1.1, 1.05, 1.63], size=19,
          bold_cells={(7, 1), (3, 2), (4, 3), (6, 6), (5, 6)}, highlight_rows=(5, 6, 7), row_h=0.52),
    FIGURE("comparison_outcomes.png", "How each incident ended, by policy"),
    T([
        B("The agents reach the strongest baseline.", "Penalty-only (\u22120.24 h) and "
          "unconstrained (\u22120.28 h) edge past the threshold policy (\u22120.38 h), which is "
          "given the likelihood model; the agent behind the mechanism is level (\u22120.41 h). "
          "Intervals overlap.", size=26),
        B("Every agent is far ahead", "of the scripted, initial-symptom and always-escalate "
          "baselines on return, at every escalation cost tested.", size=26),
        B("Behaviour follows cost:", "at 60, 120 and 240 min escalation rises 22% \u2192 32% "
          "\u2192 48% and wrong fixes fall 31% \u2192 23% \u2192 15%.", size=26),
    ]),
))

c3.section("Challenges", RED, stack(
    T([P("The safety mechanism guarantees compliance but does not teach it. In the pilot a "
         "blocked proposal costs only a step, so the agent behind the mechanism keeps proposing "
         "rule-breaking fixes and lets the mechanism send them back.", size=26)]),
    FIGURE("v3_training_compliance.png", "Rule compliance over training (3 seeds per agent)"),
    T([
        B("Blocked proposals rise to ~35%", "early in training and settle at 20\u201325%; 4% of "
          "the agent's incidents end in a forced escalation.", size=26),
        B("Unconstrained:", "proposes few violations (~1%), but each one executes \u2013 a rule "
          "broken in 7.6% of incidents.", size=26),
        B("Verification changes what \u201cgood\u201d means:", "the scripted checklist resolves "
          "the most (88%) by retrying fixes, at 9 checks and a wrong fix in 30% of incidents.",
          size=26),
    ]),
), fill_to_bottom=True)


# ================================================================ column 4
c4 = Column(3)
hyp_rows = [
    ["Hypothesis", "Pilot result", "Reading"],
    ["H1: beats simple baselines", "67.6% vs 88.3% (scripted)", "Not supported"],
    ["H2: best compliant success", "67.6% vs 74.7% (penalty)", "Not supported"],
    ["Zero executed violations", "0 of 15,000", "Holds"],
    ["Blocked proposals fall", "35% \u2192 20\u201325%", "Partly"],
    ["H3: ambiguity (Exp. 4)", "Not run in pilot", "\u2013"],
]
c4.section("Areas of Improvement: Hypotheses", RED, stack(
    table(hyp_rows, [4.0, 3.9, 2.78], size=19, bold_cells={(1, 2), (2, 2), (3, 2), (4, 2)},
          row_h=0.52),
    T([
        B("Charge a block", "(its cost is zero in the pilot) so that the agent learns to check "
          "before proposing; report it as an ablation of the mechanism.", size=26),
        B("Judge H1 on return and wrong-fix rate,", "not resolution alone: a checklist that "
          "retries fix after fix resolves a lot at a high cost.", size=26),
        B("The penalty only teaches where it was trained:", "in Phase 5 it broke rules in "
          "4\u20137% of incidents once checks went missing; the mechanism stayed at zero.",
          size=26),
    ]),
    FIGURE("comparison_sensitivity.png", "Sensitivity to the cost of escalation (60, 120, 240 min)"),
    T([P(("Prototype:", True), " six of eight example cases end as intended (four with the "
         "earlier agent). In the ambiguous vague_slow case the agent's wrong guess failed on "
         "staging and was escalated, not shipped. The language model only reads the ticket; the "
         "trained agent decides; the rule checker stays independent.", size=26)]),
    table([["Example case", "Agent decision", "Example case", "Agent decision"],
           ["results_approval", "Fix, verified", "fees_release", "Escalate ✗"],
           ["sign_in", "Fix, verified", "payment_gateway", "Escalate ✗"],
           ["transcript_dup.", "Fix, verified", "vague_slow", "Fix failed, escalate"],
           ["class_results_slow", "Fix, verified", "profile_cache", "Fix, verified"]],
          [2.75, 2.15, 2.65, 3.13], size=18, row_h=0.46),
    T([P(("✗ = not the intended decision (fix C06 / fix C01). Cases written by the researcher: "
          "they show the pipeline works, not its accuracy.", False, GREY), size=20)]),
))


def other(x, y):
    paras = [
        P(("Contacts", True)),
        P(("Email: ", True), "charisopol@gmail.com      ", ("Phone: ", True), "0765821211", size=26),
        P(("Key References", True)),
        P(("1. Z. Chen et al., \u201cTowards intelligent incident management: Why we need it and "
           "how we make it,\u201d ESEC/FSE, 2020.", False, GREY), size=22),
        P(("2. M. Alshiekh et al., \u201cSafe reinforcement learning via shielding,\u201d AAAI, 2018.",
           False, GREY), size=22),
        P(("3. H. van Hasselt, A. Guez and D. Silver, \u201cDeep reinforcement learning with "
           "double Q-learning,\u201d AAAI, 2016.", False, GREY), size=22),
        P(("Limits of the pilot", True)),
        P("One UIS developer, not the Directorate; several researcher-set values.", bullet=True, size=24),
        P("Three seeds (ten planned); base ambiguity level only.", bullet=True, size=24),
        P("Block cost of zero; verification assumed reliable.", bullet=True, size=24),
        P(("These are pilot readings, not thesis findings.", False, GREY), size=22),
    ]
    return add_text(x, y, INNER_W, paras)


c4.section("Other information", BLUE, other, fill_to_bottom=True)

for i, c in enumerate([c1, c2, c3, c4], 1):
    print(f"column {i}: bottom {c.y - GAP:.2f} in (limit {BOTTOM})")

prs.save(OUT)
print("saved", OUT)
