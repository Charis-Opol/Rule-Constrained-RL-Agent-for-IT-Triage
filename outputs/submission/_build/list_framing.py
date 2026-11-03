"""List sentences that depend on the author's project (for the standalone-framing proposal).

Run:  python -I list_framing.py <out_dir>
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
BS = chr(92)
t = (Path(sys.argv[1]) / 'source' / 'manuscript.tex').read_text(encoding='utf-8')
b = t[t.index(BS + 'section{Introduction}'):t.index(BS + 'backmatter')]
sec = '?'
pat = re.compile(r'[^.]*\b(project|Chapter Two|planned|thematic review|particular study|prepare)\w*\b[^.]*\.?')
for line in b.splitlines():
    m = re.match(r'\\(?:sub)*section\{([^}]*)\}', line)
    if m:
        sec = m.group(1)[:45]
    for mm in pat.finditer(line):
        s = ' '.join(mm.group(0).split())
        s = re.sub(r'\\cite\w*\{[^}]*\}', '(cit.)', s)
        print(f'[{sec}] {s[:240]}')
