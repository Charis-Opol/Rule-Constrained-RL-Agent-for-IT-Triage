"""PRISMA identification + automated eligibility for the new SLR exports.
Usage: python -I prisma.py <export_dir> <out_dir>"""
import csv, re, sys, json, collections, os

csv.field_size_limit(10**9)
src, out = sys.argv[1], sys.argv[2]

def norm(s):
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())

recs = []
# Scopus
for x in csv.DictReader(open(os.path.join(src, 'scopus export.csv'), encoding='utf-8-sig')):
    ab = x['Abstract']
    if ab.startswith('[No abstract'): ab = ''
    recs.append(dict(db='Scopus', title=x['Title'], year=x['Year'], venue=x['Source title'],
                     authors=x['Authors'], doi=x['DOI'].lower(), abstract=ab,
                     keywords=x['Author Keywords'] + '; ' + x['Index Keywords'],
                     type=x['Document Type'], lang='English'))

def bib(path, db):
    t = open(path, encoding='utf-8').read()
    parts = re.split(r'(?=@\w+\{)', t)
    for p in parts:
        m = re.match(r'@(\w+)\{', p)
        if not m: continue
        def f(k):
            mm = re.search(r'\b' + k + r'\s*=\s*\{((?:[^{}]|\{[^{}]*\})*)\}', p, re.I | re.S)
            return re.sub(r'[{}]', '', mm.group(1)).strip() if mm else ''
        typ = m.group(1).lower()
        recs.append(dict(db=db, title=f('title'), year=f('year'),
                         venue=f('journal') or f('booktitle') or f('publisher'),
                         authors=f('author'), doi=f('doi').lower(), abstract=f('abstract'),
                         keywords=f('keywords'), type=typ, lang='English'))

bib(os.path.join(src, 'acm (3).bib'), 'ACM')
for fn in os.listdir(src):
    if fn.startswith('IEEE') and fn.endswith('.bib'):
        bib(os.path.join(src, fn), 'IEEE')

log = collections.OrderedDict()
log['identified'] = collections.Counter(r['db'] for r in recs)

# De-duplication (DOI, then normalised title); keep the copy with an abstract
seen, uniq = {}, []
for r in recs:
    keys = [k for k in (r['doi'], norm(r['title'])) if k]
    hit = next((seen[k] for k in keys if k in seen), None)
    if hit is not None:
        if not hit['abstract'] and r['abstract']:
            hit['abstract'] = r['abstract']
        hit['db'] = hit['db'] if r['db'] in hit['db'] else hit['db'] + '+' + r['db']
        continue
    uniq.append(r)
    for k in keys: seen[k] = r
log['after_dedup'] = len(uniq)
log['duplicates_removed'] = len(recs) - len(uniq)

# Automated eligibility 1: protocol limits (type, year 2015-2026)
ok_types = {'Article', 'Conference paper', 'article', 'inproceedings'}
def limits(r):
    if r['type'] not in ok_types: return 'type:' + r['type']
    try: y = int(r['year'])
    except ValueError: return 'year:missing'
    if not 2015 <= y <= 2026: return 'year:%d' % y
    return None

# Automated eligibility 2: the protocol string, applied to title+abstract+keywords
A = r'reinforcement learning|deep q-?networks?|\bdqn\b|q-learning|policy gradient|actor-critic|proximal policy optimi|markov decision process|partially observable markov|\bpomdps?\b|\bmdps?\b|contextual bandit|multi-armed bandit'
B = (r'incident management|incident response|incident triage|incident handling|incident resolution|'
     r'incident mitigation|\baiops\b|\bit operations\b|it service management|\bitsm\b|site reliability|'
     r'service desk|help ?desk|trouble tickets?|ticket routing|ticket assignment|alert triage|'
     r'alert prioriti|security operations cent|automated remediation')
RC = r'root cause'
RCN = r'microservice|cloud|online service|it systems?'
C = (r'triage|escalat|defer|human-in-the-loop|human in the loop|human oversight|investigat|diagnos|'
     r'information gathering|information acquisition|remediat|mitigat|constrain|shield|'
     r'safe reinforcement learning|action mask|partial\w* observ|uncertain|ambigu|root cause')

def near(text, a, b, n=5):
    w = re.findall(r"[a-z0-9\-]+", text)
    s = ' '.join(w)
    for m in re.finditer(a, s):
        i = s[:m.start()].count(' ')
        win = ' '.join(w[max(0, i - n): i + n + 3])
        if re.search(b, win): return True
    return False

# Block C was dropped on 23 Oct 2026: it excluded two in-scope benchmark studies
# (Hammar & Li 2025; Hammar et al. 2026). See PRISMA_record.md.
USE_C = False
def string(r):
    t = ' '.join([r['title'], r['abstract'], r['keywords']]).lower()
    a = re.search(A, t, re.I)
    b = re.search(B, t, re.I) or near(t, RC, RCN)
    c = re.search(C, t, re.I)
    if not a: return 'string:no-method-term'
    if not b: return 'string:no-setting-term'
    if not c and USE_C: return 'string:no-decision-term'
    return None

lim_out, str_out, kept = collections.Counter(), collections.Counter(), []
for r in uniq:
    why = limits(r)
    if why: lim_out[why.split(':')[0] + ':' + ('other' if why.startswith('type') else 'out-of-range')] += 1; continue
    why = string(r)
    if why: str_out[why] += 1; continue
    kept.append(r)
log['removed_by_limits'] = dict(lim_out)
log['removed_by_string'] = dict(str_out)
log['to_title_abstract_screening'] = len(kept)

os.makedirs(out, exist_ok=True)
with open(os.path.join(out, 'screening.csv'), 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh)
    w.writerow(['id', 'db', 'year', 'title', 'venue', 'doi', 'authors', 'abstract'])
    for i, r in enumerate(sorted(kept, key=lambda r: r['title'].lower()), 1):
        w.writerow(['S%03d' % i, r['db'], r['year'], r['title'], r['venue'], r['doi'], r['authors'], r['abstract']])
json.dump(log, open(os.path.join(out, 'log.json'), 'w'), indent=1, default=dict)
print(json.dumps(log, indent=1, default=dict))
