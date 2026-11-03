"""Check that tables and figures are first cited in numerical order, and that each abbreviation's
first use in the body is its definition.

Run:  python -I check_order.py <out_dir>
"""
import re
import sys
from pathlib import Path

OUT = Path(sys.argv[1])
tex = (OUT / 'source' / 'manuscript.tex').read_text(encoding='utf-8')
aux = (OUT / '_build' / 'logs' / 'manuscript.aux').read_text(encoding='utf-8')
num = dict(re.findall(r'\\newlabel\{((?:tab|fig):\w+)\}\{\{([^}]*)\}', aux))

body = tex[tex.index('\\section{Introduction}'):tex.index('\\backmatter')]
# text outside floats: drop table/figure environments and the longtable
text = re.sub(r'\\begin\{(table|figure|longtable)\}.*?\\end\{\1\}', ' ', body, flags=re.S)

for kind, word in (('tab', 'Table'), ('fig', 'Fig.')):
    first = []
    for m in re.finditer(r'\\ref\{(' + kind + r':\w+)\}', text):
        if m.group(1) not in [f for f, _ in first]:
            first.append((m.group(1), int(num[m.group(1)])))
    seq = [n for _, n in first]
    ok = seq == sorted(seq) and seq == list(range(1, len(seq) + 1))
    defined = sorted(int(v) for k, v in num.items() if k.startswith(kind))
    print(f'{word} first-citation order: {seq}  -> {"PASS" if ok and seq == defined else "FAIL"}'
          f' (defined: {defined})')

# abbreviations: from Table 1 rows
rows = re.search(r'\\label\{tab:abbrev\}(.*?)\\botrule', tex, re.S).group(1)
abbrs = []
for a in re.findall(r'^([A-Za-z\- /]+?) &', rows, re.M):
    abbrs += [x.strip() for x in a.split('/')]
abbrs = [a for a in abbrs if a and a != 'Abbreviation']
start = text.index('\\section{Introduction}')
plain = re.sub(r'\\(cite\w*|label|ref|texttt)\{[^}]*\}', ' ', text)
plain = re.sub(r'\\texttt\{.*?\}', ' ', plain, flags=re.S)
print('\nAbbreviation first use in body (outside floats):')
for a in sorted(set(abbrs)):
    m = re.search(r'(?<![A-Za-z])' + re.escape(a) + r'(?![A-Za-z])', plain)
    if not m:
        print(f'  {a:8} not used in body text (used only in tables, if at all)')
        continue
    ctx = plain[max(0, m.start() - 70):m.end() + 5].replace('\n', ' ')
    defined = plain[m.start() - 1] == '(' or re.search(r'\(' + re.escape(a), plain[m.start() - 1:m.end() + 2])
    print(f'  {a:8} {"defined" if defined else "CHECK  "} ...{ctx}')
