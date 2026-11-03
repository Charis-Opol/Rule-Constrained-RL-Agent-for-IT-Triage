import re, sys

BS = chr(92)


def sents(p):
    t = open(p, encoding='utf-8').read()
    t = re.sub('%.*', '', t)
    t = re.sub(re.escape(BS) + 'cite[a-z]*' + re.escape('{') + '[^}]*' + re.escape('}'), '', t)
    t = re.sub(re.escape(BS) + '[a-zA-Z]+', ' ', t)
    t = re.sub('[{}~]', '', t)
    return [s.strip() for s in re.split(r'(?<=[.;])\s+', t) if len(s.split()) >= 6]


def grams(s, n=6):
    w = re.findall('[a-z0-9]+', s.lower())
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


src = set()
for p in sys.argv[2:]:
    for s in sents(p):
        src |= grams(s)
for s in sents(sys.argv[1]):
    g = grams(s)
    if g:
        r = len(g & src) / len(g)
        if r >= 0.3:
            print(f"{r:.0%} | {' '.join(s.split())[:200]}")
