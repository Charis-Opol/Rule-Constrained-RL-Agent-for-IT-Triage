"""Generate the review's audit CSVs, LaTeX tables, count macros and bibliography.

Run from research/slr/:   python -I audit/generate.py
Inputs : audit/review_data.py (full-text decisions, extraction, appraisal, themes)
         ../new-slr-exports/screening/title_abstract_screening.csv (131 screening decisions)
         ../new-slr-exports/scopus export.csv (bibliographic metadata; local only, not tracked)
         ../thesis/citations/references.bib (background references shared with the thesis)
Outputs: audit/*.csv, tables/*.tex, references.bib
"""
import csv, os, re, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from review_data import FULLTEXT, AUTHOR_JUDGED, THESIS_KEYS, SETTINGS, STUDIES, THEMES  # noqa: E402

csv.field_size_limit(10 ** 9)
SCREEN = os.path.join(ROOT, '..', 'new-slr-exports', 'screening', 'title_abstract_screening.csv')
SCOPUS = os.path.join(ROOT, '..', 'new-slr-exports', 'scopus export.csv')
THESIS_BIB = os.path.join(ROOT, '..', 'thesis', 'citations', 'references.bib')

# Identification counts from the deduplication and automated filtering run of 23 October 2026
# (recorded in ../new-slr-exports/screening/PRISMA_record.md).
IDENT = dict(scopus=3394, acm=1000, ieee=5, duplicates=73, type=1462, year=32, no_a=2270, no_b=431)

CODES = {
    'IC1': 'RL or sequential decision-making is not the method under study',
    'IC2': 'Not incident handling in a computing system',
    'IC3': 'No triage-relevant decision',
    'IC4': 'No quantitative evaluation',
    'EC1': 'Not a computing incident',
    'EC2': 'Resource management only',
    'EC3': 'Detection or classification only',
    'EC4': 'Offensive security',
    'EC5': 'Language-model agent without an RL policy',
    'EC6': 'Review, position paper or workshop summary',
    'EC7': 'Earlier version of an included study',
}

def tex(s):
    """Escape text for LaTeX."""
    rep = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#',
           '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}
    s = ''.join(rep.get(c, c) for c in str(s))
    s = s.replace('"', "''")
    s = re.sub(r"''(.*?)''", r"``\1''", s)
    return s.replace('O(N\\^{}2)', '$O(N^2)$').replace('O(1)', '$O(1)$')

def write(path, text):
    with open(os.path.join(ROOT, path), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)

def write_csv(path, header, rows):
    with open(os.path.join(ROOT, path), 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)

# ---------------------------------------------------------------------------
screen = list(csv.DictReader(open(SCREEN, encoding='utf-8')))
SCR = {r['id']: r for r in screen}
assert len(screen) == 131
ta_excl = collections.Counter(r['reason_code'] for r in screen if r['decision'] == 'Exclude')
ta_incl = [r['id'] for r in screen if r['decision'] != 'Exclude']
assert sorted(ta_incl) == sorted(FULLTEXT), set(ta_incl) ^ set(FULLTEXT)
prio = {r['id']: ('1' if 'priority 1' in r['decision'] else '2') for r in screen if r['decision'] != 'Exclude'}

ft = collections.Counter(v[0] for v in FULLTEXT.values())
included = [k for k, v in FULLTEXT.items() if v[0] == 'included']
assert sorted(included) == sorted(s['id'] for s in STUDIES)
S = {s['id']: s for s in STUDIES}
for s in STUDIES:
    assert len(s['q']) == 8 and set(s['q']) <= set('YPN'), s['id']

identified = IDENT['scopus'] + IDENT['acm'] + IDENT['ieee']
auto = IDENT['type'] + IDENT['year'] + IDENT['no_a'] + IDENT['no_b']
screened = identified - IDENT['duplicates'] - auto
assert screened == len(screen)
n_excl_ta = sum(ta_excl.values())
sought = screened - n_excl_ta
assert sought == len(FULLTEXT)
not_ret = ft['not retrieved']
assessed = sought - not_ret
excl_ft = ft['excluded']
n_inc = assessed - excl_ft
assert n_inc == len(STUDIES) == ft['included']

# ---------------------------------------------------------------------------
# Bibliography
# ---------------------------------------------------------------------------
def norm(s):
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())

def bib_from_scopus(ids):
    rows = list(csv.DictReader(open(SCOPUS, encoding='utf-8-sig')))
    by_doi = {r['DOI'].lower(): r for r in rows if r['DOI']}
    by_title = {norm(r['Title']): r for r in rows}
    out = {}
    for i in ids:
        sr = SCR[i]
        r = by_doi.get(sr['doi'].lower()) if sr['doi'] else None
        r = r or by_title.get(norm(sr['title']))
        assert r is not None, i
        out[i] = r
    return out

def bib_entry(key, r):
    names = []
    for a in r['Author full names'].split(';'):
        a = re.sub(r'\(\d+\)', '', a).strip()
        if a:
            names.append(a)
    authors = ' and '.join(names) if names else r['Authors']
    f = [('author', authors), ('title', '{' + r['Title'] + '}')]
    article = r['Document Type'] == 'Article'
    f.append(('journal' if article else 'booktitle', r['Source title']))
    for fld, col in (('volume', 'Volume'), ('number', 'Issue')):
        if r[col]:
            f.append((fld, r[col]))
    if r['Page start'] and r['Page end']:
        f.append(('pages', r['Page start'] + '--' + r['Page end']))
    elif r['Art. No.']:
        f.append(('note', 'Art. no. ' + r['Art. No.']))
    f.append(('year', r['Year']))
    if r['DOI']:
        f.append(('doi', r['DOI']))
        f.append(('url', 'https://doi.org/' + r['DOI']))
    body = ',\n'.join('  %s = {%s}' % (k, v.replace('&', r'\&').replace('%', r'\%')) for k, v in f)
    return '@%s{%s,\n%s\n}\n' % ('article' if article else 'inproceedings', key, body)

EXCLUDED_CITED = {'S016': 'manojkumar2026', 'S027': 'bompally2026', 'S130': 'reddyavula2026'}
BACKGROUND = ['chen2020', 'remil2024', 'sutton2018', 'kaelbling1998', 'konighofer2025', 'madras2018',
              'turan2026', 'janisch2019', 'kim2025', 'joshi2023', 'alshiekh2018', 'hammar2026llm',
              'ren2025', 'levy2026', 'pacella2026', 'hamel2026', 'alauthman2026'] + sorted(set(THESIS_KEYS.values()) - {'alauthman2026'})

def build_bib():
    src = open(THESIS_BIB, encoding='utf-8').read()
    entries = re.split(r'(?=^@)', src, flags=re.M)
    thesis = {}
    for e in entries:
        m = re.match(r'@\w+\{([^,]+),', e)
        if m:
            thesis[m.group(1)] = e.rstrip() + '\n'
    parts = ['% Generated by audit/generate.py. Do not edit by hand.\n',
             '% Background and overlapping entries are copied from ../thesis/citations/references.bib;\n',
             '% all other entries are built from the Scopus export of the review search.\n\n']
    for k in BACKGROUND:
        parts.append(thesis[k] + '\n')
    need = [s['id'] for s in STUDIES if s['id'] not in THESIS_KEYS] + list(EXCLUDED_CITED)
    meta = bib_from_scopus(need)
    for s in STUDIES:
        if s['id'] not in THESIS_KEYS:
            parts.append(bib_entry(s['key'], meta[s['id']]) + '\n')
    for i, k in EXCLUDED_CITED.items():
        parts.append(bib_entry(k, meta[i]) + '\n')
    parts.append(open(os.path.join(HERE, 'method_refs.bib'), encoding='utf-8').read())
    write('references.bib', ''.join(parts))

if os.path.exists(SCOPUS):
    build_bib()
else:
    print('Scopus export not found: references.bib left unchanged')

# ---------------------------------------------------------------------------
# Audit CSVs
# ---------------------------------------------------------------------------
write_csv('audit/prisma_reconciliation.csv',
          ['stage', 'count', 'source', 'derivation'],
          [['Records identified: Scopus', IDENT['scopus'], 'scopus export.csv', 'rows in export'],
           ['Records identified: ACM Digital Library', IDENT['acm'], 'acm (3).bib', 'entries in export'],
           ['Records identified: IEEE Xplore', IDENT['ieee'], 'IEEE Xplore BibTeX export', 'entries in export'],
           ['Records identified (total)', identified, 'exports', 'sum of the three'],
           ['Duplicate records removed', IDENT['duplicates'], 'dedup script', 'DOI then normalised title'],
           ['Removed by automation: document type', IDENT['type'], 'dedup script', 'not article or conference paper'],
           ['Removed by automation: publication year', IDENT['year'], 'dedup script', 'outside 2015-2026'],
           ['Removed by automation: no block A term', IDENT['no_a'], 'dedup script', 'title, abstract, keywords'],
           ['Removed by automation: no block B term', IDENT['no_b'], 'dedup script', 'title, abstract, keywords'],
           ['Records screened', screened, 'title_abstract_screening.csv', '%d - %d - %d' % (identified, IDENT['duplicates'], auto)],
           ['Records excluded at title and abstract', n_excl_ta, 'title_abstract_screening.csv', 'rows with decision Exclude'],
           ['Reports sought for retrieval', sought, 'title_abstract_screening.csv', '%d - %d' % (screened, n_excl_ta)],
           ['Reports not retrieved', not_ret, 'review_data.py FULLTEXT', 'outcome = not retrieved'],
           ['Reports assessed for eligibility', assessed, 'review_data.py FULLTEXT', '%d - %d' % (sought, not_ret)],
           ['Reports excluded at full text', excl_ft, 'review_data.py FULLTEXT', 'outcome = excluded'],
           ['Studies included', n_inc, 'review_data.py STUDIES', '%d - %d' % (assessed, excl_ft)]])

write_csv('audit/fulltext_decisions.csv',
          ['id', 'title', 'year', 'venue', 'doi', 'priority_group', 'outcome', 'reason', 'assessed_by'],
          [[i, SCR[i]['title'], SCR[i]['year'], SCR[i]['venue'], SCR[i]['doi'], prio[i], o, r,
            'manual' if i in AUTHOR_JUDGED else ('AI assistant from full text' if o != 'not retrieved' else 'manual (access record)' if 'recorded at retrieval' in r else 'not assessed')]
           for i, (o, r) in sorted(FULLTEXT.items())])

write_csv('audit/exclusion_traceability.csv',
          ['id', 'database', 'year', 'title', 'title_abstract_decision', 'title_abstract_reason', 'fulltext_outcome', 'fulltext_reason'],
          [[r['id'], r['database'], r['year'], r['title'],
            r['decision'], r['reason'],
            FULLTEXT.get(r['id'], ('', ''))[0], FULLTEXT.get(r['id'], ('', ''))[1]] for r in screen])

EXT = ['id', 'key', 'short', 'setting', 'task', 'formulation', 'method', 'uncertainty', 'info', 'act', 'disp', 'esc',
       'ctype', 'constraint', 'blocked', 'env', 'envtype', 'baselines', 'rule_baseline', 'metrics',
       'dq', 'eff', 'escm', 'comp', 'robustness', 'result', 'limitation']
write_csv('audit/data_extraction.csv', EXT + ['year', 'title', 'venue', 'doi'],
          [[s[k] if k != 'setting' else SETTINGS[s[k]] for k in EXT] +
           [SCR[s['id']]['year'], SCR[s['id']]['title'], SCR[s['id']]['venue'], SCR[s['id']]['doi']] for s in STUDIES])

QITEMS = ['Q1 formulation', 'Q2 environment', 'Q3 non-learning baseline', 'Q4 metrics defined',
          'Q5 repeated runs with variance', 'Q6 unseen test conditions', 'Q7 limitations', 'Q8 reproducible details']
write_csv('audit/quality_appraisal.csv', ['id', 'key'] + QITEMS + ['items_met', 'items_partly'],
          [[s['id'], s['key']] + list(s['q']) + [s['q'].count('Y'), s['q'].count('P')] for s in STUDIES])

theme_of = collections.defaultdict(list)
for srq, theme, ids, ev, interp in THEMES:
    for i in ids:
        theme_of[i].append('%s: %s' % (srq, theme))
write_csv('audit/study_traceability.csv', ['id', 'key', 'setting', 'used_in_themes', 'appendix_tables'],
          [[s['id'], s['key'], SETTINGS[s['setting']], ' | '.join(theme_of[s['id']]), 'B, C, D'] for s in STUDIES])
write_csv('audit/thematic_traceability.csv', ['srq', 'theme', 'supporting_studies', 'evidence', 'interpretation'],
          [[srq, t, ' '.join('%s(%s)' % (i, S[i]['key']) for i in ids), ev, interp] for srq, t, ids, ev, interp in THEMES])

# ---------------------------------------------------------------------------
# Count macros
# ---------------------------------------------------------------------------
C = collections.OrderedDict()
C['NScopus'] = IDENT['scopus']; C['NACM'] = IDENT['acm']; C['NIEEE'] = IDENT['ieee']
C['NIdentified'] = identified; C['NDuplicates'] = IDENT['duplicates']; C['NAfterDedup'] = identified - IDENT['duplicates']
C['NAutoType'] = IDENT['type']; C['NAutoYear'] = IDENT['year']; C['NAutoA'] = IDENT['no_a']; C['NAutoB'] = IDENT['no_b']
C['NAutoString'] = IDENT['no_a'] + IDENT['no_b']; C['NAuto'] = auto
C['NScreened'] = screened; C['NExclTA'] = n_excl_ta; C['NSought'] = sought
C['NNotRetrieved'] = not_ret; C['NNotRetClosed'] = sum(1 for v in FULLTEXT.values() if v[0] == 'not retrieved' and v[1].startswith('Closed'))
C['NNotRetNoRecord'] = not_ret - C['NNotRetClosed']
C['NAssessed'] = assessed; C['NExclFT'] = excl_ft; C['NIncluded'] = n_inc
C['NPOne'] = sum(1 for i in prio if prio[i] == '1'); C['NPTwo'] = sum(1 for i in prio if prio[i] == '2')
C['NInclPOne'] = sum(1 for i in included if prio[i] == '1'); C['NInclPTwo'] = sum(1 for i in included if prio[i] == '2')
C['NFTDetect'] = sum(1 for v in FULLTEXT.values() if v[0] == 'excluded' and v[1].startswith('EC3'))
yrs = collections.Counter(int(SCR[i]['year']) for i in included)
C['NYearRecent'] = yrs[2025] + yrs[2026]; C['NYearTwentySix'] = yrs[2026]; C['NYearMin'] = min(yrs)
for code, name in (('ITOPS', 'SetITOPS'), ('SOC', 'SetSOC'), ('NET', 'SetNET'), ('ICS', 'SetICS'), ('DFIR', 'SetDFIR')):
    C['N' + name] = sum(1 for s in STUDIES if s['setting'] == code)
C['NInfo'] = sum(1 for s in STUDIES if s['info'])
C['NAct'] = sum(1 for s in STUDIES if s['act'])
C['NDisp'] = sum(1 for s in STUDIES if s['disp'])
C['NEsc'] = sum(1 for s in STUDIES if s['esc'])
C['NInfoAct'] = sum(1 for s in STUDIES if s['info'] and s['act'])
C['NAllThree'] = sum(1 for s in STUDIES if s['info'] and s['act'] and s['esc'])
C['NBelief'] = sum(1 for s in STUDIES if 'belief' in s['formulation'].lower())
C['NShield'] = sum(1 for s in STUDIES if s['ctype'] == 'Hard filter or shield')
C['NMask'] = sum(1 for s in STUDIES if s['ctype'] == 'Action masking')
C['NCostCon'] = sum(1 for s in STUDIES if s['ctype'] == 'Expected-cost constraint')
C['NPenalty'] = sum(1 for s in STUDIES if s['ctype'] == 'Reward penalty')
C['NNoCon'] = sum(1 for s in STUDIES if s['ctype'] == 'None')
C['NBlocked'] = sum(1 for s in STUDIES if s['blocked'])
C['NDQ'] = sum(s['dq'] for s in STUDIES); C['NEff'] = sum(s['eff'] for s in STUDIES)
C['NEscM'] = sum(s['escm'] for s in STUDIES); C['NComp'] = sum(s['comp'] for s in STUDIES)
C['NAllMetrics'] = sum(1 for s in STUDIES if s['dq'] and s['eff'] and s['escm'] and s['comp'])
C['NThreeMetrics'] = sum(1 for s in STUDIES if (s['dq'] + s['eff'] + s['escm'] + s['comp']) >= 3)
C['NRuleBase'] = sum(1 for s in STUDIES if s['rule_baseline'])
C['NRobust'] = sum(1 for s in STUDIES if s['robustness'])
for j, name in enumerate(['QOne', 'QTwo', 'QThree', 'QFour', 'QFive', 'QSix', 'QSeven', 'QEight']):
    C['N' + name] = sum(1 for s in STUDIES if s['q'][j] == 'Y')
C['NQHigh'] = sum(1 for s in STUDIES if s['q'].count('Y') >= 6)
C['NQLow'] = sum(1 for s in STUDIES if s['q'].count('Y') <= 2)
for t, name in (('Benchmark', 'EnvBench'), ('Custom simulator', 'EnvSim'), ('Emulated testbed', 'EnvEmu'),
                ('Public dataset', 'EnvData'), ('Operational data', 'EnvOps'), ('Testbed and benchmark', 'EnvTestbed')):
    C['N' + name] = sum(1 for s in STUDIES if s['envtype'] == t)
words = {0: 'zero', 1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six', 7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten'}
lines = ['% Generated by audit/generate.py from review_data.py and the screening record.\n']
for k, v in C.items():
    lines.append('\\newcommand{\\%s}{%s}\n' % (k, v))
write('tables/counts.tex', ''.join(lines))

# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------
def cites(ids):
    return '\\cite{%s}' % ','.join(S[i]['key'] for i in ids)

ORDER = ['ITOPS', 'SOC', 'NET', 'ICS', 'DFIR']
ordered = sorted(STUDIES, key=lambda s: (ORDER.index(s['setting']), int(SCR[s['id']]['year']), s['short']))

# Title/abstract exclusion reasons
rows = ''.join('%s & %s & %d \\\\\n' % (c, CODES[c], n) for c, n in sorted(ta_excl.items(), key=lambda x: -x[1]))
write('tables/tab_ta_reasons.tex', rows + '\\midrule\n & Total excluded & %d \\\\\n' % n_excl_ta)

# Full-text exclusions
rows = ''
for i in sorted(k for k, v in FULLTEXT.items() if v[0] == 'excluded'):
    key = EXCLUDED_CITED.get(i) or THESIS_KEYS.get(i)
    ref = (' \\cite{%s}' % key) if key else ''
    rows += '%s & %s%s & %s \\\\\n' % (i, tex(SCR[i]['title']), ref, tex(FULLTEXT[i][1]))
write('tables/tab_ft_exclusions.tex', rows)

# Not retrieved
rows = ''.join('%s & %s & %s \\\\\n' % (i, tex(SCR[i]['title']), tex(FULLTEXT[i][1]))
               for i in sorted(k for k, v in FULLTEXT.items() if v[0] == 'not retrieved'))
write('tables/tab_not_retrieved.tex', rows)

# Evidence base summary (counts)
def cnt(pred):
    return sum(1 for s in STUDIES if pred(s))
summ = [('Setting', SETTINGS[k], cnt(lambda s, k=k: s['setting'] == k)) for k in ORDER]
summ += [('Year', str(y), yrs[y]) for y in sorted(yrs)]
fam = [('Explicit belief (POMDP)', lambda s: 'belief' in s['formulation'].lower()),
       ('Other partially observable formulation', lambda s: ('partial' in s['formulation'].lower() or 'pomdp' in s['formulation'].lower() or 'partially' in s['formulation'].lower() or 'recurrent' in s['formulation'].lower()) and 'belief' not in s['formulation'].lower()),
       ('Constrained MDP', lambda s: 'onstrained' in s['formulation']),
       ('Offline MDP', lambda s: 'Offline' in s['formulation']),
       ('Game', lambda s: 'game' in s['formulation'].lower()),
       ('Hierarchical', lambda s: 'ierarchical' in s['formulation'])]
summ += [('Formulation', n, cnt(p)) for n, p in fam]
envs = ['Benchmark', 'Custom simulator', 'Emulated testbed', 'Testbed and benchmark', 'Public dataset', 'Operational data']
summ += [('Environment', e, cnt(lambda s, e=e: s['envtype'] == e)) for e in envs]
rows, last = '', None
for g, n, c in summ:
    rows += '%s & %s & %d \\\\\n' % (g if g != last else '', n, c)
    if g != last and last is not None:
        pass
    last = g
write('tables/tab_summary.tex', rows.replace('\nYear', '\n\\midrule\nYear').replace('\nFormulation', '\n\\midrule\nFormulation').replace('\nEnvironment', '\n\\midrule\nEnvironment'))

# Coverage summary
cov = [('Decision', 'Gathers information (explicit action)', C['NInfo']),
       ('', 'Takes or recommends a response or remediation action', C['NAct']),
       ('', 'Disposes of the alert (close, allow, prioritise)', C['NDisp']),
       ('', 'Escalates, defers or hands off to a person', C['NEsc']),
       ('', 'Information gathering and response action', C['NInfoAct']),
       ('', 'Information gathering, response action and escalation', C['NAllThree']),
       ('Constraint', 'Hard filter or shield', C['NShield']),
       ('', 'Action masking', C['NMask']),
       ('', 'Expected-cost or budget constraint', C['NCostCon']),
       ('', 'Reward penalty only', C['NPenalty']),
       ('', 'None stated', C['NNoCon']),
       ('', 'Handling of a blocked action reported', C['NBlocked']),
       ('Measures', 'Decision quality', C['NDQ']),
       ('', 'Investigation or time efficiency', C['NEff']),
       ('', 'Escalation behaviour', C['NEscM']),
       ('', 'Constraint compliance', C['NComp']),
       ('', 'Three or more of the four groups', C['NThreeMetrics']),
       ('', 'All four groups', C['NAllMetrics']),
       ('Evaluation', 'Non-learning (static or rule) baseline', C['NRuleBase']),
       ('', 'Robustness tested', C['NRobust'])]
rows = ''
for g, n, c in cov:
    if g and g != 'Decision':
        rows += '\\midrule\n'
    rows += '%s & %s & %d \\\\\n' % (g, n, c)
write('tables/tab_coverage_summary.tex', rows)

# Quality item counts
rows = ''
for j, item in enumerate(QITEMS):
    y = sum(1 for s in STUDIES if s['q'][j] == 'Y'); p = sum(1 for s in STUDIES if s['q'][j] == 'P')
    rows += 'Q%d & %s & %d & %d & %d \\\\\n' % (j + 1, item[3:].capitalize(), y, p, len(STUDIES) - y - p)
write('tables/tab_quality_summary.tex', rows)

# Traceability matrix
rows, last = '', None
for srq, theme, ids, ev, interp in THEMES:
    studies = ('All %d (Table~\\ref{tab:quality})' % len(ids)) if len(ids) == len(STUDIES) else cites(ids)
    if srq != last and last is not None:
        rows += '\\midrule\n'
    rows += '%s & %s & %s & %s \\\\\n' % (srq if srq != last else '', tex(theme), studies, tex(interp))
    last = srq
write('tables/tab_traceability.tex', rows)

# Appendix long tables
def mark(b):
    return '\\checkmark' if b else '--'
rows = ''
for s in ordered:
    rows += '%s \\cite{%s} & %s & %s & %s & %s & %s \\\\\n' % (
        tex(s['short']), s['key'], SCR[s['id']]['year'], tex(s['task']),
        tex(s['formulation'] + '; ' + s['method']), tex(s['env']), tex(s['result']))
write('tables/tab_characteristics_long.tex', rows)

rows = ''
for s in ordered:
    acts = '; '.join(x for x in (s['act'], s['disp']) if x)
    con = s['ctype'] + (': ' + s['constraint'] if s['constraint'] else '')
    if s['blocked']:
        con += '. Blocked or uncertain cases: ' + s['blocked']
    rows += '%s \\cite{%s} & %s & %s & %s & %s & %s \\\\\n' % (
        tex(s['short']), s['key'], tex(s['info']) or '--', tex(acts) or '--', tex(s['esc']) or '--',
        tex(con), tex(s['robustness']) or '--')
write('tables/tab_coverage_long.tex', rows)

rows = ''
for s in ordered:
    rows += '%s \\cite{%s} & %s & %d \\\\\n' % (tex(s['short']), s['key'],
                                              ' & '.join({'Y': 'Yes', 'P': 'Part', 'N': 'No'}[c] for c in s['q']),
                                              s['q'].count('Y'))
write('tables/tab_quality_long.tex', rows)

rows = ''
for i in sorted(FULLTEXT):
    o, r = FULLTEXT[i]
    key = S[i]['key'] if i in S else EXCLUDED_CITED.get(i) or THESIS_KEYS.get(i)
    ref = (' \\cite{%s}' % key) if key else ''
    rows += '%s & %s%s & %s & %s & %s \\\\\n' % (i, tex(SCR[i]['title']), ref, SCR[i]['year'], prio[i],
                                                tex(o.capitalize()) + ('. ' + tex(r) if r else ''))
write('tables/tab_decisionlog_long.tex', rows)

# Bar chart coordinates for the coverage figure
coords = [('Gathers information', C['NInfo']), ('Response action', C['NAct']), ('Escalates or defers', C['NEsc']),
          ('All three decisions', C['NAllThree']), ('Hard filter or shield', C['NShield']),
          ('Blocked action handled', C['NBlocked']), ('Decision quality measured', C['NDQ']),
          ('Efficiency measured', C['NEff']), ('Escalation measured', C['NEscM']),
          ('Compliance measured', C['NComp']), ('Robustness tested', C['NRobust'])]
write('tables/fig_coverage_coords.tex',
      '\\def\\CoverageSymbols{%s}\n\\def\\CoverageCoords{%s}\n' % (
          ','.join('{%s}' % n for n, _ in coords), ' '.join('(%d,{%s})' % (v, n) for n, v in coords)))
print('done:', dict(C))
