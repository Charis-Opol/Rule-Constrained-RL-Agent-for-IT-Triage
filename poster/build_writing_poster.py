"""Build the scientific-writing poster (A0 landscape, PowerPoint) on the pilot poster's template.

Course requirement (slide "What Next??? (Writing, Reporting & Publishing)"): a poster about the
status of the research, with emphasis on the literature review and how the review informed the
research pipeline, methodology and dataset. Content comes from the proposal
(research/proposal/) and the systematic review (research/slr/); every number is listed in
poster/SOURCES.md.

Template: same header (logos, title, student line) and the same four-column red/blue panel
style as documentation/pilot-report/build_poster.py. The workflow section uses the same five
steps as poster/figures/make_simple_flow.py, drawn as native shapes so it stays editable.

Run from the repository root:  python poster/build_writing_poster.py
"""
import copy
import os
from pathlib import Path

from lxml import etree
from PIL import Image, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "research/proposal/Opol_Charis_Research_Poster.pptx"
OUT = Path(os.environ.get("POSTER_OUT", ROOT / "poster/Opol_Charis_Scientific_Writing_Poster.pptx"))
GAP_BARS = ROOT / "research/proposal/poster_figs/gap_bars.png"          # from the proposal poster
FRAMEWORK = ROOT / "research/thesis/images/Figure_1_1_Conceptual_Framework.png"
OBJECTIVE = ROOT / "research/proposal/poster_figs/objective_mechanism.png"   # from the proposal poster

RED, BLUE = "C0392B", "0070C0"
INK, GREY, GREEN = "1A1A1A", "555555", "1E8449"
FONT = "Trebuchet MS"
F_REG = ImageFont.truetype("C:/Windows/Fonts/trebuc.ttf", 100)
F_BOLD = ImageFont.truetype("C:/Windows/Fonts/trebucbd.ttf", 100)

COL_X = [0.45, 12.03, 23.61, 35.18]
COL_W, PAD, TOP, BOTTOM, GAP = 11.18, 0.25, 3.75, 32.72, 0.4
INNER_W = COL_W - 2 * PAD
BODY, CAP = 28, 22
LINE = 1.2
SPACE_AFTER = 10
BUL_IND = 0.38

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
        set_runs(sh, ["OPOL CHARIS   |   S24B23/003   |   B29654   |   BSc Computer Science   |   "
                      "Research Status, November 2026"])


# ---------------------------------------------------------------- text measurement
def measure(paras, width_in):
    """Height in inches of paragraphs [(runs, bullet, size)] wrapped to width_in."""
    total = 0.0
    for runs, bullet, size in paras:
        w = (width_in - (BUL_IND if bullet else 0)) * 72
        words = []
        for text, bold, _ in runs:
            f = F_BOLD if bold else F_REG
            for word in text.split(" "):
                words.append((word, f))
        lines, cur = 1, 0.0
        space = F_REG.getlength(" ") * size / 100
        for word, f in words:
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


def box_text(s, text, size, colour="FFFFFF", bold=True):
    tf = s.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE  # keep the box size in every viewer
    tf.margin_left = tf.margin_right = Inches(0.08)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = text
    r.font.size, r.font.bold, r.font.name = Pt(size), bold, FONT
    r.font.color.rgb = RGBColor.from_string(colour)


def arrow(x1, y1, x2, y2, width=3):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1),
                                   Inches(x2), Inches(y2))
    c.line.color.rgb = RGBColor.from_string("404040")
    c.line.width = Pt(width)
    tail = etree.SubElement(c.line._get_or_add_ln(), qn("a:tailEnd"))
    tail.set("type", "triangle")


def picture(path, x, y, w):
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
        add_text(self.x + PAD, self.y + 0.11, INNER_W, [P((title, True, "FFFFFF"), size=44)])
        top = self.y + 0.95
        body = rect(self.x, top, COL_W, 1, "FFFFFF", "D9D9D9")
        h = body_fn(self.x + PAD, top + PAD) + 2 * PAD - SPACE_AFTER / 72
        if fill_to_bottom:
            h = max(h, BOTTOM - top)
        body.height = Inches(h)
        self.y = top + h + GAP
        return top + h


def stack(*items):
    def fn(x, y):
        y0 = y
        for item in items:
            y += item(x, y)
        return y - y0
    return fn


def T(paras):
    return lambda x, y: add_text(x, y, INNER_W, paras)


def FIGURE(path, cap, w=INNER_W):
    def fn(x, y):
        h = picture(path, x + (INNER_W - w) / 2, y, w)
        return h + 0.08 + caption(x, y + h + 0.08, INNER_W, cap) + 0.15
    return fn


def table(rows, col_w, size=20, row_h=0.5, align_left=False):
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
                c.margin_left = c.margin_right = Inches(0.08)
                c.margin_top = c.margin_bottom = Inches(0.03)
                c.vertical_anchor = MSO_ANCHOR.MIDDLE
                c.fill.solid()
                c.fill.fore_color.rgb = RGBColor.from_string(
                    BLUE if i == 0 else ("FFFFFF" if i % 2 else "F5F5F5"))
                tf = c.text_frame
                tf.word_wrap = True
                p = tf.paragraphs[0]
                p.alignment = PP_ALIGN.LEFT if (j == 0 or align_left) else PP_ALIGN.CENTER
                r = p.add_run()
                r.text = rows[i][j]
                r.font.size = Pt(size)
                r.font.name = FONT
                r.font.bold = i == 0
                r.font.color.rgb = RGBColor.from_string("FFFFFF" if i == 0 else INK)
        return row_h * n + 0.3
    return fn


def callout(title, text, colour=RED, fill="FBEAEA"):
    def fn(x, y):
        paras = [P((title, True, colour), size=30), P(text, size=BODY)]
        h = measure(paras, INNER_W - 0.5) + 0.35
        s = rect(x, y, INNER_W, h, fill, colour, MSO_SHAPE.ROUNDED_RECTANGLE, 2)
        s.adjustments[0] = 0.06
        add_text(x + 0.25, y + 0.2, INNER_W - 0.5, paras)
        return h + 0.3
    return fn


# ---------------------------------------------------------------- native diagrams
def prisma(x, y):
    """PRISMA 2020 flow: one box per stage, with the records removed at each stage beside it."""
    stages = [("4,399 records found", "73 duplicates and 4,195 removed by filters"),
              ("131 screened", "84 excluded on title and abstract"),
              ("47 sought in full", "7 not retrieved"),
              ("40 read in full", "6 excluded"),
              ("34 included", "published 2020\u20132026")]
    bw, bh, g = 5.0, 0.95, 0.45
    for i, (label, note) in enumerate(stages):
        by = y + i * (bh + g)
        last = i == len(stages) - 1
        s = rect(x, by, bw, bh, BLUE if last else "EAF2FA", BLUE, MSO_SHAPE.ROUNDED_RECTANGLE, 2)
        s.adjustments[0] = 0.15
        box_text(s, label, 28, "FFFFFF" if last else INK)
        add_text(x + bw + 0.25, by + bh / 2 - 0.42, INNER_W - bw - 0.25,
                 [P((note, False, GREY), size=23)])
        if not last:
            arrow(x + bw / 2, by + bh, x + bw / 2, by + bh + g)
    h = len(stages) * (bh + g) - g
    return h + 0.1 + caption(x, y + h + 0.1, INNER_W,
                             "Study selection (PRISMA 2020), searched 23 Oct 2026") + 0.1


FLOW = [  # same wording as poster/figures/make_simple_flow.py
    ("A problem report comes in", BLUE, "Someone reports a fault; the system's log is attached."),
    ("Key facts are picked out", BLUE, "Each fact is copied word for word from the report or log, "
                                       "so a person can check it."),
    ("The assistant chooses a step", BLUE, "Look into it further, try a fix, or hand it to a person."),
    ("Rulebook check", RED, "Steps the team's rules forbid are blocked; blocked twice, a person "
                            "takes over."),
    ("Action is taken and recorded", BLUE, "Fixes are tested first and wait for a person's "
                                           "approval; every outcome is written down."),
]


def workflow(x, y):
    """Plain-language workflow: five boxes left to right, then one sentence per step."""
    n, gap, bh = len(FLOW), 0.3, 1.85
    bw = (INNER_W - (n - 1) * gap) / n
    for i, (label, colour, _) in enumerate(FLOW):
        bx = x + i * (bw + gap)
        s = rect(bx, y, bw, bh, colour, None, MSO_SHAPE.ROUNDED_RECTANGLE)
        s.adjustments[0] = 0.12
        box_text(s, f"{i + 1}. {label}", 24)
        if i < n - 1:
            arrow(bx + bw + 0.04, y + bh / 2, bx + bw + gap - 0.04, y + bh / 2)
    paras = [P((f"{i + 1}. ", True, col), text, size=28) for i, (_, col, text) in enumerate(FLOW)]
    th = add_text(x, y + bh + 0.25, INNER_W, paras)
    ey = y + bh + 0.25 + th + 0.05
    eh = example(x, ey)
    return ey + eh - y - 0.3


EXAMPLE = [  # fictional sign_in case: prototype/examples/sign_in, docs/PROJECT_DOCUMENTATION.md 3.4
    ("Report:", "“Students cannot log in to the portal” (production)."),
    ("Facts:", "the log shows a lock on the users row during a token update."),
    ("Step:", "fix C08, move the token write off the sign-in path; the rulebook permits it."),
    ("Action:", "its test passes on staging, so a draft pull request awaits a person."),
]


def example(x, y):
    """Worked example of the five steps on one fictional ticket."""
    paras = [P(("Example: a fictional sign-in ticket", True, BLUE), size=24)]
    paras += [P((lab, True), " " + text, size=22) for lab, text in EXAMPLE]
    h = measure(paras, INNER_W - 0.5) + 0.35
    s = rect(x, y, INNER_W, h, "EAF2FA", BLUE, MSO_SHAPE.ROUNDED_RECTANGLE, 2)
    s.adjustments[0] = 0.06
    add_text(x + 0.25, y + 0.2, INNER_W - 0.5, paras)
    return h + 0.3


# ================================================================ column 1
c1 = Column(0)
c1.section("1. Introduction", RED, T([
    P("When an IT incident is reported, staff must decide what to do before they know its cause: "
      "investigate further, apply a likely fix, or pass the incident to someone better placed. "
      "The first evidence is often incomplete, unreliable or consistent with several causes."),
    P("Most automated triage tools make a single prediction from the ticket. They cannot ask for "
      "more evidence, cannot say that they are unsure, and do not check their actions against an "
      "organisation's operational rules."),
    P("This research designs and evaluates a reinforcement learning agent that learns when to "
      "investigate, apply a permitted fix, or escalate, with an independent rule-based safety "
      "mechanism, for the Directorate of University ICT Services (UIS)."),
]))

c1.section("2. Objectives", RED, T([
    B("Build:", "a simulator from about 15 causes, 20 checks and 10 rules elicited from UIS, "
      "with missing, unreliable and overlapping evidence each controlled."),
    B("Train:", "a deep Q-network that requests checks, applies permitted fixes or escalates, "
      "under the safety mechanism; PPO as a robustness check."),
    B("Evaluate:", "against six baselines on decision quality, investigation cost, escalation "
      "and rule compliance, across levels of ambiguity."),
]))

c1.section("3. Literature Review: Method", BLUE, stack(
    T([
        B("Databases:", "Scopus, IEEE Xplore (open access), ACM Digital Library; 23 Oct 2026."),
        B("Method:", "PRISMA 2020 and the Kitchenham and Charters procedure."),
        B("Appraisal:", "eight-item quality checklist; synthesis around five questions."),
        B("Limits:", "one AI-assisted screener; no citation searching yet."),
    ]),
    lambda x, y: 0.1,
    prisma,
), fill_to_bottom=True)


# ================================================================ column 2
c2 = Column(1)
c2.section("4. What the 34 Studies Show", BLUE, stack(
    T([P("Reinforcement learning for IT and security incidents: each part of the planned "
         "agent appears somewhere, but never all together.")]),
    FIGURE(GAP_BARS, "Studies (of 34) containing each element", w=0.65 * INNER_W),
    T([
        B("Hidden cause:", "only 4 studies track what might be wrong."),
        B("Decisions:", "17 gather information, 7 pass to a person, only 1 does all three."),
        B("Rules:", "5 use a hard block; only 3 say what happens to a blocked action, and none "
          "lets the agent propose again."),
        B("Measures:", "decision quality in 31, escalation in 5, rule-keeping in 4."),
    ]),
))

c2.section("5. Research Gap", RED, stack(
    callout("The gap", "No reviewed study learns one policy that investigates, fixes or "
            "escalates IT service incidents under explicit operational rules, or reports how "
            "such an agent behaves as the evidence becomes more ambiguous."),
    T([
        B("RQ1:", "How can ambiguous UIS incidents be simulated with controllable missing, "
          "unreliable and overlapping evidence?"),
        B("RQ2:", "How well can an agent learn when to investigate, fix or escalate?"),
        B("RQ3:", "How does the rule mechanism affect compliant success and decisions?"),
        B("RQ4:", "How does the agent compare with baselines as evidence becomes more ambiguous?"),
    ]),
))

c2.section("6. Hypotheses", BLUE, T([
    B("H1:", "the agent resolves more incidents correctly than the simple baselines, at no "
      "higher investigation cost than the scripted checklist."),
    B("H2:", "with the rule mechanism it achieves a higher compliant success rate than the "
      "unconstrained and penalty-only agents."),
    B("H3:", "missing evidence brings more escalation; unreliable evidence more checks; "
      "overlapping evidence more checks and escalation."),
]), fill_to_bottom=True)


# ================================================================ column 3
c3 = Column(2)
shaped = [
    ["The review found", "So this research"],
    ["Unclear evidence rarely varied", "Varies missing, wrong and overlapping evidence separately"],
    ["Passing on seldom learned", "Makes escalation a learned choice with a cost"],
    ["Blocked actions unreported", "Logs every block: one retry, then a person"],
    ["Escalation and rule-keeping rarely measured", "Reports four groups of measures together"],
    ["Weak baselines, single runs", "Six baselines; ten seeds; 95% intervals"],
]
c3.section("7. From Review to Pipeline", BLUE, stack(
    table(shaped, [4.7, 5.98], size=25, row_h=1.2, align_left=True),
))

c3.section("8. Research Pipeline", BLUE, stack(
    FIGURE(FRAMEWORK, "The agent proposes; the rule mechanism permits, returns once or escalates"),
))

c3.section("9. Workflow: How the System Works", BLUE, workflow, fill_to_bottom=True)


# ================================================================ column 4
c4 = Column(3)
c4.section("10. Methodology", RED, stack(T([
    B("Problem:", "triage of one incident is a partially observable decision problem, solved "
      "entirely in simulation: the cause is hidden and every executed action must be permitted."),
]), FIGURE(OBJECTIVE, "Objective under the rules, and the two-proposal mechanism", w=0.62 * INNER_W),
T([
    B("Agent:", "masked deep Q-network (two layers of 128 units); PPO as a second learner."),
    B("Safety mechanism:", "checks each proposal; a blocked proposal is returned once, a second "
      "block escalates."),
    B("Compared with:", "four fixed policies and two agents without the mechanism "
      "(unconstrained, penalty-only)."),
    B("Four experiments:", "baselines, rule mechanism, choices removed, worse evidence; ten "
      "seeds, 95% bootstrap intervals."),
])))

c4.section("11. Dataset", RED, T([
    B("No tickets or personal data in training:", "a scenario model of causes, checks, "
      "symptoms and rules, filled in by IT staff."),
    B("Pilot:", "8 causes, 11 checks, 4 symptoms and 5 rules from one UIS developer."),
    B("Planned:", "about 15 causes, 20 checks and 10 rules from the Directorate."),
    B("Tests:", "5,000 simulated incidents never seen in training."),
    B("Prototype:", "8 fictional tickets; 20 sample tickets kept private."),
]))

c4.section("12. Status and Next Steps", BLUE, T([
    B("Done:", "review; pilot simulator, rule mechanism and agents; Experiments 1\u20132 "
      "(3 seeds); working prototype."),
    B("Pilot reading:", "0 rule violations executed in 15,000 incidents behind the mechanism; "
      "the agents reach the strongest baseline."),
    B("Next:", "full scenario model with UIS; 10 seeds; Experiments 3\u20134; reader accuracy "
      "on the 20 sample tickets."),
]))


def other(x, y):
    paras = [
        P(("Email: ", True), "charisopol@gmail.com      ", ("Phone: ", True), "0765821211"),
        P(("1. M. J. Page et al., \u201cThe PRISMA 2020 statement,\u201d BMJ, 2021.", False, GREY),
          size=23),
        P(("2. B. Kitchenham and S. Charters, EBSE-2007-01, 2007.", False, GREY), size=23),
        P(("3. Z. Chen et al., \u201cTowards intelligent incident management,\u201d ESEC/FSE, "
           "2020.", False, GREY), size=23),
        P(("4. M. Alshiekh et al., \u201cSafe reinforcement learning via shielding,\u201d AAAI, "
           "2018.", False, GREY), size=23),
    ]
    return add_text(x, y, INNER_W, paras)


c4.section("13. Contacts & Key References", BLUE, other, fill_to_bottom=True)

for i, c in enumerate([c1, c2, c3, c4], 1):
    print(f"column {i}: bottom {c.y - GAP:.2f} in (limit {BOTTOM})")

prs.save(OUT)
print("saved", OUT)
