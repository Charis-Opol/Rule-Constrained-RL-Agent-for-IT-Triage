"""Exact optimal policy of the toy environment, by searching over every possible
sequence of check results (feasible only because the toy is tiny)."""
import numpy as np
from toy_triage_env import ToyTriageEnv


def solve(env, status, t):
    """Returns (expected return, best action) from this point of an episode."""
    belief = env.prior.copy()
    for i, s in enumerate(status):
        if s != env.NOT_REQUESTED:
            belief = belief * (env.theta[i] if s == env.POSITIVE else 1 - env.theta[i])
    belief = belief / belief.sum()
    options = [(-env.cost_esc, env.ESCALATE)]
    options += [(b * env.r_correct - (1 - b) * env.cost_wrong, env.n_checks + j)
                for j, b in enumerate(belief)]
    if t + 1 < env.max_steps:               # room to run another check and still decide
        for i in np.flatnonzero(status == env.NOT_REQUESTED):
            p_pos = float(belief @ env.theta[i])
            value = -env.check_costs[i]
            for s, p in ((env.POSITIVE, p_pos), (env.NEGATIVE, 1 - p_pos)):
                nxt = status.copy(); nxt[i] = s
                value += p * solve(env, nxt, t + 1)[0]
            options.append((value, int(i)))
    return max(options)


def optimal_policy(env, obs):
    e = env.unwrapped
    return solve(e, e.status, e.t)[1]



if __name__ == "__main__":
    from make_toy_results import run
    lines = [r"\begin{tabular}{@{}rrrrrr@{}}", r"\toprule",
             r"$\lambda_{\text{wrong}}$ & $p^*$ & Optimal return & Correct & Wrong & Escalated \\",
             r"\midrule"]
    for cost_wrong in (10, 20, 40):
        make = lambda: ToyTriageEnv(cost_wrong=cost_wrong)
        e = make()
        p_star = (e.cost_wrong - e.cost_esc) / (e.r_correct + e.cost_wrong)
        value = solve(e, np.full(e.n_checks, e.NOT_REQUESTED), 0)[0]
        _, out = run(optimal_policy, make)
        shares = " & ".join(f"{100 * out.get(k, 0):.1f}" + r"\%" for k in ("correct", "wrong", "escalated"))
        lines.append(f"{cost_wrong} & {p_star:.2f} & {value:.2f} & {shares} " + r"\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    with open("reward_threshold.tex", "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
