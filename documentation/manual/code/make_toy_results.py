"""Trains both learners on the toy environment, runs the reference policies, and writes
toy_results.tex for the manual. All policies are scored on the same 1,000 unseen incidents."""
import numpy as np
from stable_baselines3.common.monitor import Monitor
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from toy_triage_env import ToyTriageEnv
from masked_dqn import MaskedDQN, MaskedDQNPolicy
from train_toy import MaskInObservation
from optimal_toy import optimal_policy

N_EVAL, EVAL_SEED = 1000, 10_000


def run(policy, make_env):
    env, returns, outcomes = make_env(), [], {}
    for k in range(N_EVAL):
        obs, _ = env.reset(seed=EVAL_SEED + k)
        total, done = 0.0, False
        while not done:
            obs, r, terminated, truncated, info = env.step(policy(env, obs))
            total, done = total + r, terminated or truncated
        returns.append(total)
        outcomes[info["outcome"]] = outcomes.get(info["outcome"], 0) + 1
    return np.mean(returns), {k: v / N_EVAL for k, v in outcomes.items()}


def threshold_policy(env, obs):
    e = env.unwrapped
    belief = e.prior.copy()                      # Bayes' rule over the checks seen so far
    for i, s in enumerate(e.status):
        if s != e.NOT_REQUESTED:
            belief *= e.theta[i] if s == e.POSITIVE else 1 - e.theta[i]
    belief /= belief.sum()
    p_star = (e.cost_wrong - e.cost_esc) / (e.r_correct + e.cost_wrong)
    unrun = np.flatnonzero(e.status == e.NOT_REQUESTED)
    if belief.max() > 0.8:                       # confident: recommend
        return e.n_checks + int(belief.argmax())
    if len(unrun):                               # not confident: gather evidence
        return int(unrun[0])
    # Checks exhausted: recommend only above the reward threshold p*, else escalate.
    return e.n_checks + int(belief.argmax()) if belief.max() > p_star else e.ESCALATE


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    rows = {
        "Random (valid actions)": run(lambda env, o: int(rng.choice(np.flatnonzero(env.unwrapped.action_masks()))), ToyTriageEnv),
        "Always escalate": run(lambda env, o: env.unwrapped.ESCALATE, ToyTriageEnv),
        "Threshold (knows $\\theta$)": run(threshold_policy, ToyTriageEnv),
    }

    dqn = MaskedDQN(MaskedDQNPolicy, Monitor(MaskInObservation(ToyTriageEnv())),
                    policy_kwargs=dict(net_arch=[128, 128]), learning_starts=1_000,
                    exploration_fraction=0.3, seed=0, verbose=0)
    dqn.learn(total_timesteps=100_000)
    rows["Masked DQN (100k steps)"] = run(lambda env, o: int(dqn.predict(o, deterministic=True)[0]),
                             lambda: MaskInObservation(ToyTriageEnv()))

    mask_fn = lambda e: e.unwrapped.action_masks()
    ppo = MaskablePPO("MlpPolicy", ActionMasker(Monitor(ToyTriageEnv()), mask_fn), seed=0, verbose=0)
    ppo.learn(total_timesteps=30_000)
    rows["MaskablePPO (30k steps)"] = run(lambda env, o: int(ppo.predict(o, deterministic=True, action_masks=mask_fn(env))[0]),
                              ToyTriageEnv)

    rows["Exact optimum"] = run(optimal_policy, ToyTriageEnv)
    oracle_return = ToyTriageEnv().r_correct
    lines = [r"\begin{tabular}{@{}lrrrrr@{}}", r"\toprule",
             r"Policy & Mean return & Correct & Wrong & Escalated & Step limit \\", r"\midrule"]
    for name, (ret, out) in rows.items():
        cells = " & ".join(f"{100 * out.get(k, 0):.1f}\\%" for k in ("correct", "wrong", "escalated", "step_limit"))
        lines.append(f"{name} & {ret:.2f} & {cells} \\\\")
        print(f"{name:28s} {ret:6.2f} {out}")
    lines += [f"Oracle (told the cause) & {oracle_return:.2f} & 100.0\\% & 0.0\\% & 0.0\\% & 0.0\\% \\\\",
              r"\bottomrule", r"\end{tabular}"]
    with open("toy_results.tex", "w") as f:
        f.write("\n".join(lines) + "\n")
