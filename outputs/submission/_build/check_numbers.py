"""Compare every number in the original review text with the submission manuscript.

Run:  python -I check_numbers.py <slr_dir> <out_dir>

Numbers are taken from the original sections and in-text tables (count macros substituted, as in
the original PDF) and from the body of manuscript.tex (title page and back matter excluded).
Citation keys, labels and LaTeX lengths are stripped first, so only printed numbers are compared.
"""
import re
import sys
from collections import Counter
from pathlib import Path

SLR, OUT = Path(sys.argv[1]), Path(sys.argv[2])
counts = dict(re.findall(r'\\newcommand\{\\(N[A-Za-z]+)\}\{([^}]*)\}',
                         (SLR / 'tables/counts.tex').read_text(encoding='utf-8')))


def subst(t):
    t = re.sub(r'\\the\\numexpr\\NIncluded-\\NSetITOPS\\relax\{\}',
               str(int(counts['NIncluded']) - int(counts['NSetITOPS'])), t)
    for k in sorted(counts, key=len, reverse=True):
        t = re.sub(re.escape('\\' + k) + r'(\{\})?(?![A-Za-z])', lambda m, v=counts[k]: v, t)
    return t


def expand(t):
    return re.sub(r'\\inputrows\{([^}]*)\}', lambda m: (SLR / m.group(1)).read_text(encoding='utf-8'), t)


def numbers(t):
    t = '\n'.join(l for l in t.splitlines() if not l.lstrip().startswith('%'))
    t = re.sub(r'\\(cite\w*|label|ref|input|includegraphics|begin|end|newcolumntype)\*?(\[[^]]*\])?\{[^}]*\}', ' ', t)
    t = re.sub(r'\{@\{\}[^\n]*?@\{\}\}', ' ', t)               # column specs
    t = re.sub(r'p\{[\d.]+cm\}|P\{[\d.]+cm\}|[\d.]+(cm|mm|pt|em)', ' ', t)
    t = re.sub(r'\\[a-zA-Z]+', ' ', t)
    return Counter(re.findall(r'\d+(?:\.\d+)?', t))


orig = ''
for name in ['introduction', 'methodology', 'results', 'discussion', 'limitations', 'future_work', 'conclusion']:
    orig += expand((SLR / f'sections/{name}.tex').read_text(encoding='utf-8')) + '\n'
# the PRISMA diagram's text (the TikZ drawing parameters are not printed numbers)
prisma = (SLR / 'figures/prisma_flow.tex').read_text(encoding='utf-8')
orig += '\n'.join(re.findall(r'\\node\[[^]]*\][^{]*\{(.*?)\};', prisma, re.S)) + '\n'
orig += (SLR / 'tables/tab_abbreviations.tex').read_text(encoding='utf-8') + '\n'
orig = subst(orig)
orig = re.sub(r'\\emph\{\d\) ', r'\\emph{', orig)            # run-in theme numbers become headings
orig = orig.replace('\\NIdentified', counts['NIdentified'])

new = (OUT / 'source' / 'manuscript.tex').read_text(encoding='utf-8')
new = new[new.index('\\section{Introduction}'):new.index('\\backmatter')]
new = re.sub(r'Online Resource~\d|Table~S\d|S038', ' ', new)   # pointers to the ESM
# the printed text of the new Fig. 1 (numbers drawn into the EPS) and Fig. 2 bar labels
import pymupdf
for fig in ('Fig1', 'Fig2'):
    new += '\n' + ''.join(p.get_text() for p in pymupdf.open(OUT / 'source' / f'{fig}.pdf'))
orig += '\n' + (SLR / 'tables/fig_coverage_coords.tex').read_text(encoding='utf-8')
orig += '\n0 5 10 15 20 25 30 34\n'   # Fig. 2 axis ticks and "Studies (of 34)" are new artwork labels

a, b = numbers(orig), numbers(new)
lost = a - b
added = b - a
print('numbers in original body:', sum(a.values()), '| in new body:', sum(b.values()))
print('present in original but missing from new:', dict(lost) or 'none')
print('added in new:', dict(added) or 'none')
