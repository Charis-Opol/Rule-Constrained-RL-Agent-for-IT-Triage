"""Assemble the Artificial Intelligence Review submission from the IEEE-style source.

Run:  python -I build_manuscript.py <slr_dir> <out_dir>

Reads research/slr/sections, tables and figures, expands every row file, replaces the count
macros of tables/counts.tex with their values, and applies the formatting and compliance edits
defined in edits.py. Every text edit is a literal (old, new) pair so that the change log can be
checked against edits.py; the script stops if any edit does not apply exactly once.
"""
import re
import sys
from pathlib import Path

SLR = Path(sys.argv[1])
OUT = Path(sys.argv[2])
BS = chr(92)


def read(rel):
    return (SLR / rel).read_text(encoding='utf-8')


# --------------------------------------------------------------------------- count macros

counts = dict(re.findall(r'\\newcommand\{\\(N[A-Za-z]+)\}\{([^}]*)\}', read('tables/counts.tex')))


def subst_counts(t):
    t = t.replace(BS + 'the' + BS + 'numexpr' + BS + 'NIncluded-' + BS + 'NSetITOPS' + BS + 'relax{}',
                  str(int(counts['NIncluded']) - int(counts['NSetITOPS'])))
    for k in sorted(counts, key=len, reverse=True):
        t = t.replace(BS + k + '{}', counts[k])
        t = re.sub(re.escape(BS + k) + r'(?![A-Za-z])', lambda m, v=counts[k]: v, t)
    return t


def expand_rows(t):
    return re.sub(r'\\inputrows\{([^}]*)\}', lambda m: read(m.group(1)).strip(), t)


def strip_comments(t):
    return '\n'.join(l for l in t.splitlines() if not l.lstrip().startswith('%'))


# --------------------------------------------------------------------------- citations

bib = (OUT / 'source' / 'references.bib').read_text(encoding='utf-8')
ACCENT = re.compile(r'\\[\'"`^~cv]\{?(\w)\}?')
AUTH = {}
for m in re.finditer(r'@\w+\{(\w+),(.*?)\n\}', bib, re.S):
    a = re.search(r'author\s*=\s*\{(.*)\},?\s*\n', m.group(2))
    if a:
        surs = []
        for n in a.group(1).split(' and '):
            s = ACCENT.sub(lambda x: x.group(1), n.split(',')[0].strip())
            surs.append(s.replace('{', '').replace('}', ''))
        AUTH[m.group(1)] = surs


def mention_forms(key):
    s = AUTH[key]
    if len(s) >= 3 or 'others' in s:
        return [s[0] + ' et al.' + BS + ' ', s[0] + ' et al.']
    if len(s) == 2:
        return [s[0] + ' and ' + s[1]]
    return [s[0]]


CITE = re.compile(r'~?\\cite\{([^}]*)\}')
SENTENCE_END = re.compile(r'(?<!al)(?<!e\.g)(?<!i\.e)\.\s+[A-Z]')
CITET_LOG = []


def convert_citations(text, in_table=False):
    """Numbered \\cite -> natbib author-year.

    A single-key citation whose authors are named earlier in the same clause becomes \\citet
    (or \\citeauthor's \\citeyearpar for a possessive) and the trailing citation is removed;
    every other citation becomes \\citep (\\citealp inside table cells).
    """
    out, pos = [], 0
    for m in CITE.finditer(text):
        keys = [k.strip() for k in m.group(1).split(',')]
        seg = text[pos:m.start()]
        if len(keys) == 1 and keys[0] in AUTH and not in_table:
            key, best = keys[0], None
            for form in mention_forms(key):
                base = form[:-2] if form.endswith(BS + ' ') else form
                for poss, pat in ((False, re.escape(form)), (True, re.escape(base) + "'s ")):
                    for mm in re.finditer(pat, seg):
                        if not poss and len(AUTH[key]) == 1 and seg[mm.end():].startswith(' et al'):
                            continue
                        if not poss and seg[mm.end():].startswith("'s"):
                            continue
                        if best is None or mm.start() > best[0]:
                            best = (mm.start(), mm.end(), poss)
            if best is not None and not SENTENCE_END.search(seg[best[1]:]):
                b0, b1, poss = best
                if poss:
                    rep = BS + 'citeauthor{' + key + "}'s " + BS + 'citeyearpar{' + key + '} '
                else:
                    rep = BS + 'citet{' + key + '}' + (' ' if seg[b0:b1].endswith(' ') else '')
                out.append(seg[:b0] + rep + seg[b1:].rstrip(' ~'))
                CITET_LOG.append((key, seg[b0:b1].strip()))
                pos = m.end()
                continue
        cmd = 'citealp' if in_table else 'citep'
        out.append(seg.rstrip(' ~') + ' ' + BS + cmd + '{' + ','.join(keys) + '}')
        pos = m.end()
    out.append(text[pos:])
    return ''.join(out)


# --------------------------------------------------------------------------- literal edits

EDITS = []  # (section, old, new, reason)


def edit(sec, old, new, reason):
    EDITS.append((sec, old, new, reason))


def apply(sec, text):
    for s, old, new, _ in EDITS:
        if s != sec:
            continue
        n = text.count(old)
        if n != 1:
            sys.exit(f'EDIT FAILED ({n} matches) in {sec}: {old[:100]!r}')
        text = text.replace(old, new)
    return text


def themes_to_subsubsections(t):
    """'\\emph{1) Theme sentence.} Text' -> '\\subsubsection{Theme sentence}' + Text."""
    def rep(m):
        title = m.group(1).strip().rstrip('.')
        return BS + 'subsubsection{' + title + '}\n\n'
    return re.sub(r'\\emph\{\d\) ((?:[^{}]|\{[^{}]*\})*)\}\s*', rep, t)


# --------------------------------------------------------------------------- floats

ORDER = ['introduction', 'methodology', 'results', 'discussion', 'limitations', 'future_work', 'conclusion']
ORIG_TABLES, ORIG_FIGS, raw = {}, {}, {}
FLOAT = re.compile(r'\\begin\{(table\*?|figure\*?)\}.*?\\end\{\1\}', re.S)


def pull_floats(t):
    def rep(m):
        block = m.group(0)
        lab = re.search(r'\\label\{((?:tab|fig):\w+)\}', block).group(1)
        kind, name = lab.split(':')
        (ORIG_TABLES if kind == 'tab' else ORIG_FIGS)[name] = block
        return '%%' + ('TABLE' if kind == 'tab' else 'FIGURE') + ':' + name + '%%'
    return FLOAT.sub(rep, t)


def table_body(name):
    """Rows between \\midrule and \\bottomrule of an original table."""
    b = ORIG_TABLES[name]
    return b[b.index(BS + 'midrule') + len(BS + 'midrule'):b.rindex(BS + 'bottomrule')].strip()


# --------------------------------------------------------------------------- assemble

for name in ORDER:
    t = subst_counts(expand_rows(strip_comments(read(f'sections/{name}.tex'))))
    raw[name] = pull_floats(t)
for rel in ['tables/tab_abbreviations.tex', 'figures/prisma_flow.tex', 'figures/fig_coverage.tex']:
    pull_floats(subst_counts(strip_comments(read(rel))))

TABLES, FIGURES = {}, {}
POSTPROCESS = lambda s: s
exec((OUT / '_build' / 'edits.py').read_text(encoding='utf-8'))

parts = {}
for name in ORDER:
    t = apply(name, raw[name])
    t = themes_to_subsubsections(t)
    parts[name] = convert_citations(t)
for k in TABLES:
    TABLES[k] = convert_citations(TABLES[k], in_table=True)
for k in FIGURES:
    FIGURES[k] = convert_citations(FIGURES[k])

body = '\n\n'.join(parts[n] for n in ORDER)
for k, v in TABLES.items():
    body = body.replace('%%TABLE:' + k + '%%', v)
for k, v in FIGURES.items():
    body = body.replace('%%FIGURE:' + k + '%%', v)
body = POSTPROCESS(body)
body = re.sub(r'\n{3,}', '\n\n', body)

left = re.findall(r'%%(?:TABLE|FIGURE):\w+%%', body)
if left:
    sys.exit(f'unplaced fragments: {left}')

(OUT / 'source' / 'manuscript.tex').write_text(PREAMBLE + FRONT + body + BACK, encoding='utf-8')
def cell(s, n=220):
    s = ' '.join(s.split()).replace('|', '\\|')
    return s if len(s) <= n else s[:n] + ' ...'


log = ['| # | Section | Before | After | Reason (guideline) |', '|---|---|---|---|---|']
for i, (sec, old, new, reason) in enumerate(EDITS, 1):
    log.append(f'| E{i} | {sec} | `{cell(old)}` | `{cell(new)}` | {reason} |')
(OUT / '_build' / 'edits_log.md').write_text('\n'.join(log) + '\n', encoding='utf-8')
(OUT / '_build' / 'citet_log.txt').write_text(
    '\n'.join(f'{k}\t{m}' for k, m in CITET_LOG), encoding='utf-8')
print('wrote manuscript.tex;', len(EDITS), 'literal edits;', len(CITET_LOG), 'textual citations')
