"""Phase 4: train one DQN agent with live monitoring. Watch it with:

    streamlit run dashboard/app.py

    python -m experiments.pilot.train_dqn --agent shielded --seed 100 --steps 300000

Seeds 100 and up are for tuning; seeds 0-9 are kept for the final experiments (Chapter 3).
"""
import argparse
import json
import subprocess
import time
from pathlib import Path

import torch

from src.agents.baselines import AlwaysEscalate, Threshold
from src.agents.dqn import AGENTS, HYPERPARAMETERS, build_model, make_env
from src.agents.exact import ExactPolicy, solve
from src.agents.monitoring import MONITOR_SEED, TrainingMonitor
from src.evaluation import run_episodes, summarise
from src.sim.scenario import load_scenario

PILOT = Path(__file__).resolve().parent
ROOT = PILOT.parents[1]
RUNS = ROOT / "results" / "pilot" / "runs"
MODEL, SETTINGS = PILOT / "pilot_model.json", PILOT / "pilot_settings.json"
THRESHOLD_TAU = 0.65       # tuned in Phase 3


def git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def main():
    parser = argparse.ArgumentParser(description="Train one DQN agent with live monitoring")
    parser.add_argument("--agent", choices=AGENTS, default="shielded")
    parser.add_argument("--seed", type=int, default=100)
    parser.add_argument("--steps", type=int, default=300_000)
    parser.add_argument("--every", type=int, default=10_000)
    parser.add_argument("--incidents", type=int, default=1000)
    parser.add_argument("--name", default=None)
    parser.add_argument("--double-q", action="store_true", help="use the Double DQN target")
    parser.add_argument("--exploration-steps", type=int, default=None,
                        help="steps over which exploration falls to its final rate (default: half the run)")
    parser.add_argument("--threads", type=int, default=None, help="CPU threads for PyTorch (for parallel runs)")
    parser.add_argument("--model", type=Path, default=MODEL, help="scenario model (default: pilot_model.json)")
    parser.add_argument("--settings", type=Path, default=SETTINGS, help="settings (default: pilot_settings.json)")
    parser.add_argument("--escalation-minutes", type=float, default=None,
                        help="override the cost of escalation (sensitivity analysis only)")
    args = parser.parse_args()
    if args.threads:
        torch.set_num_threads(args.threads)
    hyperparameters = {**HYPERPARAMETERS, "double_q": args.double_q}
    if args.exploration_steps:
        hyperparameters["exploration_fraction"] = args.exploration_steps / args.steps

    scenario = load_scenario(args.model, args.settings, args.escalation_minutes)
    name = args.name or f"{time.strftime('%Y%m%d-%H%M')}_{args.agent}_seed{args.seed}"
    run_dir = RUNS / name
    run_dir.mkdir(parents=True, exist_ok=False)
    make_eval_env = lambda: make_env(scenario, args.agent, train=False)

    print("Solving the exact policy for reference...")
    solution = solve(make_eval_env()) if scenario.p_miss == 0 and not scenario.verify else None
    # Reference policies on the same monitoring incidents, so the lines are like for like.
    references = {}
    for label, policy in (("Always escalate", AlwaysEscalate(make_eval_env())),
                          (f"Threshold ({THRESHOLD_TAU})", Threshold(make_eval_env(), THRESHOLD_TAU)),
                          ("Exact optimal", ExactPolicy(make_eval_env(), solution) if solution else None)):
        if policy is not None:
            m = summarise(run_episodes(policy, make_eval_env(), args.incidents, first_seed=MONITOR_SEED))
            references[label] = {k: m[k] for k in ("mean_return", "resolution_accuracy", "wrong_rate",
                                                   "escalation_rate", "mean_checks")}

    config = {"agent": args.agent, "seed": args.seed, "steps": args.steps, "every": args.every,
              "incidents": args.incidents, "hyperparameters": hyperparameters,
              "model": str(args.model.resolve().relative_to(ROOT)),
              "settings": str(args.settings.resolve().relative_to(ROOT)),
              "escalation_minutes": args.escalation_minutes, "p_noise": scenario.p_noise, "p_miss": scenario.p_miss, "git_commit": git_commit(),
              "exact_value": solution.value if solution else None, "references": references,
              "started": time.strftime("%Y-%m-%d %H:%M:%S")}
    (run_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(f"Run folder: {run_dir}")

    model = build_model(make_env(scenario, args.agent), args.seed, hyperparameters)
    model.learn(total_timesteps=args.steps,
                callback=TrainingMonitor(run_dir, make_eval_env, solution, args.every, args.incidents))
    model.save(run_dir / "final")
    (run_dir / "finished.json").write_text(json.dumps({"finished": time.strftime("%Y-%m-%d %H:%M:%S")}) + "\n",
                                           encoding="utf-8")
    print("Done.")


if __name__ == "__main__":
    main()
