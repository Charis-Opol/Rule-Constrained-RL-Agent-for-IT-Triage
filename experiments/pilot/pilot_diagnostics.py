"""Pre-training diagnostics of the pilot responses: integrity, exact Bayes ceilings,
exact optimal policy (DP over 3^10 evidence states) and a Monte Carlo threshold policy."""
import itertools, sys, time, warnings
import numpy as np
from openpyxl import load_workbook

warnings.filterwarnings("ignore")
PATH = sys.argv[1]
v = load_workbook(PATH, data_only=True)
f = load_workbook(PATH)
SCALE = {v["Scale"][f"A{r}"].value: v["Scale"][f"B{r}"].value for r in range(5, 11)}
print("sample prob cell formula:", str(f["Check probabilities"]["D6"].value)[:140])

K, D, S = 8, 10, 4
causes = [v["Causes"][f"C{r}"].value for r in range(6, 14)]
remedies = [v["Causes"][f"E{r}"].value for r in range(6, 14)]
cats = [v["Causes"][f"B{r}"].value for r in range(6, 14)]
freq = [v["Causes"][f"F{r}"].value for r in range(6, 14)]
effort = [v["Checks"][f"E{r}"].value for r in range(6, 16)]
checks = [v["Checks"][f"B{r}"].value for r in range(6, 16)]
theta = np.array([[SCALE[v["Check likelihoods"].cell(r, 4 + i).value] for r in range(6, 14)] for i in range(D)])  # [check, cause]
sym = np.array([[SCALE[v["Symptom likelihoods"].cell(r, 4 + i).value] for r in range(6, 14)] for i in range(S)])
cached = np.array([[v["Check probabilities"].cell(r, 4 + i).value for r in range(6, 14)] for i in range(D)], float)
cached_s = np.array([[v["Symptom probabilities"].cell(r, 4 + i).value for r in range(6, 14)] for i in range(S)], float)
print("ratings mapped == cached probability tabs:", np.allclose(theta, cached), np.allclose(sym, cached_s))

rules = []
for r in range(6, 11):
    rem, when, unless = (v["Rules"][f"{c}{r}"].value for c in "BCD")
    assert rem in remedies, rem
    i = checks.index(unless.split(" ", 1)[1])
    rules.append((remedies.index(rem), "prod" if "production" in when else "high", i))
print("rules (cause idx, ctx, check idx):", rules)
print("all rule remedies and checks resolve exactly: True")

WEIGHTS = {"geometric": {"Rare": 1, "Occasional": 2, "Common": 4},
           "linear": {"Rare": 2, "Occasional": 3, "Common": 4}}
def prior_of(name):
    w = np.array([WEIGHTS[name][x] for x in freq], float)
    return w / w.sum()
prior = prior_of("geometric")
print("prior:", np.round(prior, 3), "| rule-covered prior mass (prod rules):",
      round(sum(prior[c] for c, x, _ in rules if x == "prod"), 3), "R04:", round(prior[rules[3][0]], 3))
print("categories:", {c: cats.count(c) for c in set(cats)})
COST_MIN = {"Low": 5, "Medium": 15, "High": 30}
k = np.array([COST_MIN[e] / 60 for e in effort])
P_PROD, P_HIGH = 0.8, 0.2
CTX = [(a, b) for a in (0, 1) for b in (0, 1)]
P_CTX = np.array([(P_PROD if a else 1 - P_PROD) * (P_HIGH if b else 1 - P_HIGH) for a, b in CTX])


def noisy(th, n):
    return th * (1 - n) + (1 - th) * n


def evid(mat):
    """P(pattern | cause) for all 2^n binary patterns: [patterns, K]."""
    n = mat.shape[0]
    out = []
    for bits in itertools.product((0, 1), repeat=n):
        l = np.ones(K)
        for i, b in enumerate(bits):
            l = l * (mat[i] if b else 1 - mat[i])
        out.append(l)
    return np.array(out)


SYM_L = evid(sym)
print("\n--- Bayes ceilings (exact, recommend most probable cause, no rules) ---")
for pname in WEIGHTS:
    pr = prior_of(pname)
    for n in (0, .1, .2, .3):
        Lc = evid(noisy(theta, n))
        js = pr * SYM_L  # [16,K]
        sym_only = js.max(1).sum()
        # all evidence: [1024,16,K]
        J = Lc[:, None, :] * js[None]
        ceil = J.max(2).sum()
        per = np.zeros(K)
        idx = J.argmax(2)
        for c in range(K):
            per[c] = (J[:, :, c] * (idx == c)).sum() / pr[c]
        print(f"prior={pname:9s} noise={n:.1f} prior-only={pr.max():.3f} symptoms-only={sym_only:.3f} all-checks={ceil:.3f} per-cause={np.round(per,2)}")

print("\n--- value of each check at the start (mutual information with cause, bits, avg over symptoms) ---")
def H(p):
    p = p[p > 0]
    return -(p * np.log2(p)).sum()
js = prior * SYM_L; ps = js.sum(1); post = js / ps[:, None]
print("H(cause) prior bits:", round(H(prior), 3), " H(cause|symptoms):", round(sum(ps[i] * H(post[i]) for i in range(16)), 3))
for i in range(D):
    mi = 0
    for s in range(16):
        b = post[s]; pp = (b * theta[i]).sum()
        pa = b * theta[i] / pp; na = b * (1 - theta[i]) / (1 - pp)
        mi += ps[s] * (H(b) - pp * H(pa) - (1 - pp) * H(na))
    print(f"  D{i+1:02d} {checks[i]:32s} {effort[i]:6s} MI={mi:.3f}")

print("\n--- closest cause pairs (Bhattacharyya over checks+symptoms; larger=harder) ---")
pairs = []
all_m = np.vstack([theta, sym])
for a, b in itertools.combinations(range(K), 2):
    bc = np.prod(np.sqrt(all_m[:, a] * all_m[:, b]) + np.sqrt((1 - all_m[:, a]) * (1 - all_m[:, b])))
    pairs.append((round(float(bc), 3), f"C{a+1:02d}", f"C{b+1:02d}"))
print(sorted(pairs, reverse=True)[:5])

digits = np.array(list(itertools.product((0, 1, 2), repeat=D)), dtype=np.int8)[:, ::-1]  # index base-3, digit i = status of check i
pow3 = 3 ** np.arange(D)
N = 3 ** D
assert (digits @ pow3 == np.arange(N)).all()


def dp(r, le, lw, noise=0.0, enforce=True, pr=prior, costs=k):
    th = noisy(theta, noise)
    lik = np.ones((N, K))
    for i in range(D):
        lik *= np.where(digits[:, i, None] == 2, th[i], np.where(digits[:, i, None] == 1, 1 - th[i], 1.0))
    base = pr[None] * SYM_L  # [16,K]
    V = np.zeros((N, 4, 16))
    # stats: correct, wrong, esc, n_checks, cost, violation
    ST = np.zeros((N, 4, 16, 6), dtype=np.float32)
    rule_ctx = np.array([[(a if x == "prod" else b) for a, b in CTX] for _, x, _ in rules], bool)  # [rules, ctx]
    for idx in range(N - 1, -1, -1):
        d = digits[idx]
        J = base * lik[idx]  # [16,K]
        tot = J.sum(1)
        rv = J * r - (tot[:, None] - J) * lw  # [16,K]
        forb = np.zeros((4, K), bool)
        for ri, (c, _, chk) in enumerate(rules):
            if d[chk] == 0:
                forb[:, c] |= rule_ctx[ri]
        if enforce:
            q = np.where(forb[:, None, :], -np.inf, rv[None])  # [4,16,K]
        else:
            q = np.broadcast_to(rv[None], (4, 16, K))
        jstar = q.argmax(2)
        qrec = np.take_along_axis(q, jstar[:, :, None], 2)[:, :, 0]
        qesc = np.broadcast_to(-le * tot, (4, 16))
        rec_better = qrec > qesc
        best = np.where(rec_better, qrec, qesc)
        chosen_stats = np.zeros((4, 16, 6))
        cor = np.take_along_axis(np.broadcast_to(J[None], (4, 16, K)), jstar[:, :, None], 2)[:, :, 0]
        chosen_stats[..., 0] = np.where(rec_better, cor, 0)
        chosen_stats[..., 1] = np.where(rec_better, tot - cor, 0)
        chosen_stats[..., 2] = np.where(rec_better, 0, tot)
        if not enforce:
            viol = np.take_along_axis(np.broadcast_to(forb[:, None, :], (4, 16, K)), jstar[:, :, None], 2)[:, :, 0]
            chosen_stats[..., 5] = np.where(rec_better & viol, tot, 0)
        for i in np.flatnonzero(d == 0):
            neg, pos = idx + pow3[i], idx + 2 * pow3[i]
            qc = -costs[i] * tot + V[neg] + V[pos]
            better = qc > best + 1e-12
            if better.any():
                best = np.where(better, qc, best)
                add = ST[neg] + ST[pos]
                add = add.astype(float)
                add[..., 3] += tot
                add[..., 4] += costs[i] * tot
                chosen_stats = np.where(better[..., None], add, chosen_stats)
        V[idx] = best
        ST[idx] = chosen_stats
    w = P_CTX
    ret = (V[0].sum(1) * w).sum()
    stats = (ST[0].sum(1) * w[:, None]).sum(0)
    bypc = {CTX[i]: round(float(V[0][i].sum()), 3) for i in range(4)}
    return ret, stats, bypc


print("\n--- exact optimal policy (reward unit = expert hours; lw = 5 x le from the response) ---")
print("le=2 (120 min), lw=10 (5x), check costs Low/Med/High=5/15/30 min (researcher-set), P(prod)=.8, P(high)=.2")
print("r      noise rules | p*    return  correct wrong  esc   checks cost  would-violate")
t0 = time.time()
for r in (2, 5, 10):
    for n in (0.0, 0.1, 0.2):
        for en in (True, False):
            if not en and n == 0.2:
                continue
            ret, st, _ = dp(r, 2, 10, n, en)
            ps = (10 - 2) / (r + 10)
            print(f"r={r:<3d} {n:.1f}  {'on ' if en else 'off'}  | {ps:.2f}  {ret:7.3f} {st[0]:.3f}  {st[1]:.3f}  {st[2]:.3f} {st[3]:.2f}  {st[4]:.2f}  {st[5]:.3f}")
            sys.stdout.flush()
print("dp time", round(time.time() - t0))

print("\n--- simple reference returns at r=5, le=2, lw=10 ---")
print("always escalate:", -2.0)
c = int(prior.argmax()); print("always most common fix (ignoring rules):", round(prior[c] * 5 - (1 - prior[c]) * 10, 3))
js = prior * SYM_L
print("symptoms-only MAP, always recommend (ignoring rules):", round(sum(js[s].max() * 5 - (js[s].sum() - js[s].max()) * 10 for s in range(16)), 3))
print("symptoms-only, recommend or escalate (ignoring rules):", round(sum(max(js[s].max() * 5 - (js[s].sum() - js[s].max()) * 10, -2 * js[s].sum()) for s in range(16)), 3))


def threshold_mc(n_ep, r, le, lw, noise, miss, tau, seed=0):
    rng = np.random.default_rng(seed)
    th = noisy(theta, noise)
    out = dict(c=0, w=0, e=0, forced=0, blocks=0, props=0, chk=0, cost=0.0, ret=0.0, lab=0, ceil=0)
    for _ in range(n_ep):
        cz = rng.choice(K, p=prior)
        prod, high = rng.random() < P_PROD, rng.random() < P_HIGH
        s = rng.random(S) < sym[:, cz]
        res = rng.random(D) < th[:, cz]
        avail = rng.random(D) >= miss
        full = prior * np.prod(np.where(s[:, None], sym, 1 - sym), 0)
        b_all = full * np.prod(np.where(avail[:, None], np.where(res[:, None], th, 1 - th), 1.0), 0)
        unsat = any(c == cz and (prod if x == "prod" else high) and not avail[chk] for c, x, chk in rules)
        lab = unsat or b_all.argmax() != cz
        out["lab"] += lab
        out["ceil"] += b_all.argmax() == cz
        b = full.copy(); done = np.zeros(D, bool); seen = np.zeros(D, bool); ret = 0; blocked = False; outcome = None
        for t in range(12):
            bn = b / b.sum()
            j = bn.argmax()
            if bn[j] >= tau or (~done).sum() == 0:
                if bn[j] < tau:
                    outcome = "e"; break
                out["props"] += 1
                forb = any(c == j and (prod if x == "prod" else high) and not seen[chk] for c, x, chk in rules)
                if forb:
                    out["blocks"] += 1
                    if blocked or (~done).sum() == 0:
                        outcome = "f"; break
                    blocked = True
                    # review: most informative remaining check is taken below
                else:
                    outcome = "c" if j == cz else "w"; break
            else:
                blocked = False
            cand = np.flatnonzero(~done)
            if len(cand) == 0:
                outcome = "e"; break
            def mi(i):
                pp = (bn * th[i]).sum()
                return H(bn) - pp * H(bn * th[i] / pp) - (1 - pp) * H(bn * (1 - th[i]) / (1 - pp))
            i = max(cand, key=mi)
            done[i] = True; out["chk"] += 1; out["cost"] += k[i]; ret -= k[i]
            if avail[i]:
                seen[i] = True
                b = b * (th[i] if res[i] else 1 - th[i])
        else:
            outcome = "e"
        if outcome == "c": ret += r; out["c"] += 1
        elif outcome == "w": ret -= lw; out["w"] += 1
        elif outcome == "f": ret -= le; out["forced"] += 1
        else: ret -= le; out["e"] += 1
        out["ret"] += ret
    return {a: round(x / n_ep, 3) for a, x in out.items()}


print("\n--- rule-unaware threshold policy (Monte Carlo 20k; tau=p*) at r=5 and thresholds; miss sweep ---")
for noise, miss in [(0, 0), (.1, 0), (.1, .2), (.1, .4), (.2, .2)]:
    print(f"noise={noise} miss={miss}", threshold_mc(20000, 5, 2, 10, noise, miss, tau=8 / 15))
