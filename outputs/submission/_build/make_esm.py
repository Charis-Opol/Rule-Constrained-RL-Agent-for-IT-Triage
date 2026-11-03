"""Build the Supplementary Information files for the submission.

Run:  python -I make_esm.py <slr_dir> <out_dir>

ESM_1.tex -> ESM_1.pdf (Online Resource 1): Tables S1-S4, formerly Appendices A-D, rows unchanged.
ESM_2.xlsx (Online Resource 2): the audit CSV files, one worksheet each, plus a README sheet.
Each file carries the article title, journal, author, and the corresponding author's affiliation
and e-mail, as the journal requires for supplementary material.
"""
import csv
import re
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

SLR, OUT = Path(sys.argv[1]), Path(sys.argv[2])
ESM = OUT / 'ESM'
ESM.mkdir(exist_ok=True)
BS = chr(92)

TITLE = ('Reinforcement Learning for Investigating, Acting and Escalating in IT Incident Triage and '
         'Response: A Systematic Literature Review')
JOURNAL = 'Artificial Intelligence Review'
AUTHOR = 'Charis Opol'
AFFIL = ('Department of Computing and Technology, Faculty of Engineering, Design and Technology, '
         'Uganda Christian University, [city], Uganda')
EMAIL = 'B29654@students.ucu.ac.ug; charisopol@gmail.com'

counts = dict(re.findall(r'\\newcommand\{\\(N[A-Za-z]+)\}\{([^}]*)\}',
                         (SLR / 'tables/counts.tex').read_text(encoding='utf-8')))


def rows(name):
    t = (SLR / 'tables' / name).read_text(encoding='utf-8').strip()
    t = t.replace('\u2013', '--').replace('\u2014', '---').replace('\u2019', "'").replace('\u00a0', ' ')
    # "Name et al. \cite{k}" in the study column -> \citet{k}; any other \cite -> \citep
    # (decision-log rows start with "S006 & Title \cite{k}", so the study-column pattern never matches them)
    t = re.sub(r'^[^&\n]*?\s\\cite\{(\w+)\}\s*&', lambda m: BS + 'citet{' + m.group(1) + '} &', t, flags=re.M)
    t = t.replace(' ' + BS + 'cite{', ' ' + BS + 'citep{')
    return t.replace('Sahin and Mert', BS + 'c{S}ahin and Mert')


def longtable(num, caption, spec, head, body):
    return (BS + 'begin{longtable}{' + spec + '}\n'
            + BS + 'caption*{' + BS + 'textbf{Table ' + num + '} ' + caption + '}' + BS + BS + '\n'
            + BS + 'toprule\n' + head + ' ' + BS + BS + '\n' + BS + 'midrule\n' + BS + 'endfirsthead\n'
            + BS + 'caption*{' + BS + 'textbf{Table ' + num + '} (continued)}' + BS + BS + '\n'
            + BS + 'toprule\n' + head + ' ' + BS + BS + '\n' + BS + 'midrule\n' + BS + 'endhead\n'
            + BS + 'bottomrule\n' + BS + 'endfoot\n' + body + '\n' + BS + 'end{longtable}\n')


def P(w):
    return '>{' + BS + 'raggedright' + BS + 'arraybackslash}p{' + w + '}'


tex = r"""%% Online Resource 1 (ESM_1.pdf) for the article below. Compile: pdflatex, bibtex, pdflatex x2.
\documentclass[10pt]{article}
\usepackage[a4paper,landscape,margin=18mm]{geometry}
\usepackage{booktabs,longtable,array,caption}
\usepackage[authoryear]{natbib}
\setcitestyle{aysep={}}
\usepackage[hidelinks]{hyperref}
\providecommand{\doi}[1]{\url{https://doi.org/#1}}
\providecommand{\bibcommenthead}{}% defined by sn-jnl.cls; sn-basic.bst calls it
\captionsetup{justification=raggedright,singlelinecheck=false}
\setlength{\parindent}{0pt}
\begin{document}
{\large\textbf{Online Resource 1}}\par\medskip
\textbf{Article:} """ + TITLE + r"""\par
\textbf{Journal:} """ + JOURNAL + r"""\par
\textbf{Author:} """ + AUTHOR + r"""\par
\textbf{Corresponding author:} """ + AUTHOR + ', ' + AFFIL.replace('[city]', r'\textbf{[city]}') + r"""\par
\textbf{E-mail:} """ + EMAIL + r"""\par\medskip
\textbf{Contents.} Table S1: outcome of every report sought for retrieval. Table S2: task, formulation, environment and main result of each included study. Table S3: coding of the review-question elements for each included study. Table S4: quality rating of each included study. These tables were Appendices A to D of the manuscript; their rows are unchanged. The decisions for all """ + counts['NScreened'] + r""" screened records are in Online Resource 2.
\bigskip

\footnotesize
"""
tex += longtable('S1', 'Outcome of every report sought for retrieval, with its identifier in the screening '
                 'record (ID), title, publication year, priority group from title and abstract screening '
                 '(Prio., 1 or 2) and outcome',
                 '@{}' + P('1.2cm') + P('13.6cm') + P('1.0cm') + P('0.9cm') + P('7.0cm') + '@{}',
                 'ID & Report & Year & Prio. & Outcome', rows('tab_decisionlog_long.tex'))
tex += BS + 'clearpage\n'
tex += longtable('S2', 'Task, formulation and method, environment or data, and main reported result of each '
                 'included study',
                 '@{}' + P('3.4cm') + P('0.9cm') + P('4.0cm') + P('4.6cm') + P('4.2cm') + P('6.2cm') + '@{}',
                 'Study & Year & Task & Formulation; method & Environment or data & Main reported result',
                 rows('tab_characteristics_long.tex'))
tex += BS + 'clearpage\nA dash means the element is absent or not reported.\n\n'
tex += longtable('S3', 'Coding of the review-question elements for each included study: information '
                 'gathering, response action or disposition, escalation, constraint (with the handling of '
                 'a blocked action) and robustness test',
                 '@{}' + P('3.4cm') + P('4.0cm') + P('4.0cm') + P('3.4cm') + P('5.0cm') + P('4.0cm') + '@{}',
                 'Study & Information gathering & Response action or disposition & Escalation & '
                 'Constraint (and blocked-action handling) & Robustness test',
                 rows('tab_coverage_long.tex'))
tex += (BS + 'clearpage\nItems Q1--Q8 are defined in Table~7 of the article. ``Items met\'\' counts only the '
        'items rated Yes; items rated Part are not counted.\n\n')
center = '>{' + BS + 'centering' + BS + 'arraybackslash}p{1.3cm}'
tex += longtable('S4', 'Quality rating of each included study on checklist items Q1--Q8 (Yes, met; Part, '
                 'partly met; No, not met) and the number of items met',
                 '@{}' + P('5.6cm') + center * 8 + '>{' + BS + 'centering' + BS + 'arraybackslash}p{1.6cm}@{}',
                 'Study & Q1 & Q2 & Q3 & Q4 & Q5 & Q6 & Q7 & Q8 & Items met', rows('tab_quality_long.tex'))
tex += r"""
\normalsize
\bibliographystyle{sn-basic}
\bibliography{references}
\end{document}
"""
(ESM / 'ESM_1.tex').write_text(tex, encoding='utf-8')

# --------------------------------------------------------------------------- ESM_2.xlsx

SHEETS = [
    ('exclusion_traceability', 'Decision and reason at title and abstract screening, and full-text outcome, for each of the '
     + counts['NScreened'] + ' screened records'),
    ('fulltext_decisions', 'Outcome, reason and assessor for each of the ' + counts['NSought'] + ' reports sought for retrieval'),
    ('data_extraction', 'Data extraction form for each of the ' + counts['NIncluded'] + ' included studies'),
    ('quality_appraisal', 'Quality ratings (Y, met; P, partly met; N, not met) on items Q1-Q8 for each included study'),
    ('study_traceability', 'For each included study, the themes and appendix tables in which it is used'),
    ('thematic_traceability', 'For each review question, the themes, supporting studies, evidence and interpretation'),
    ('prisma_reconciliation', 'Each PRISMA count with its source file and derivation'),
]
wb = Workbook()
ws = wb.active
ws.title = 'README'
info = [('Online Resource 2', ''), ('Article', TITLE), ('Journal', JOURNAL), ('Author', AUTHOR),
        ('Corresponding author', AUTHOR + ', ' + AFFIL), ('E-mail', EMAIL), ('', ''),
        ('Worksheet', 'Contents')] + SHEETS + [
        ('', ''), ('Note', 'The worksheets reproduce the audit CSV files of the review without change. '
                           'Raw database exports and full texts are not included (licence and copyright).')]
for r in info:
    ws.append(list(r))
ws['A1'].font = Font(bold=True, size=12)
ws['A8'].font = ws['B8'].font = Font(bold=True)
ws.column_dimensions['A'].width = 24
ws.column_dimensions['B'].width = 120
for row in ws.iter_rows():
    for cell in row:
        cell.alignment = Alignment(wrap_text=True, vertical='top')

for name, _ in SHEETS:
    sh = wb.create_sheet(name[:31])
    with open(SLR / 'audit' / f'{name}.csv', encoding='utf-8', newline='') as f:
        data = list(csv.reader(f))
    for r in data:
        sh.append(r)
    for cell in sh[1]:
        cell.font = Font(bold=True)
    sh.freeze_panes = 'A2'
wb.save(ESM / 'ESM_2.xlsx')
print('wrote ESM_1.tex and ESM_2.xlsx')
