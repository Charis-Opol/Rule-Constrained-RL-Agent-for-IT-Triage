"""Comparison experiments (Chapter 3, Experiments 1 and 2) on model v2 with fix-with-verification
settings (v3).

    python -m experiments.pilot.run_comparison train --parallel 5
    python -m experiments.pilot.run_comparison evaluate [--n-eval 5000]

Experiment 1: the shielded agent against the baselines, then the escalation-cost sensitivity
analysis (the shielded agent retrained with escalation at half and twice the elicited 120 min).
Experiment 2: shielded vs unconstrained vs penalty-only, and blocked proposals over training.

Same training settings as Phase 5 (Double DQN, 500k steps, exploration to its final rate by 150k),
seeds 0-2 (decision of 9 Nov 2026). The Part B values in pilot_settings_v3.json are
researcher-provisional.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PILOT = ROOT / "experiments" / "pilot"
RUNS = ROOT / "results" / "pilot" / "runs"
LOGS = ROOT / "results" / "pilot" / "logs"
MODEL, SETTINGS = PILOT / "pilot_model_v2.json", PILOT / "pilot_settings_v3.json"
AGENTS = ("shielded", "unconstrained", "penalty")
SEEDS = (0, 1, 2)
BASE_ESCALATION = 120.0                      # elicited
SENSITIVITY_ESCALATION = (60.0, 240.0)       # half and twice
STEPS, EXPLORATION_STEPS, EVERY = 500_000, 150_000, 25_000


def run_name(agent, seed, escalation=None):
    suffix = "" if escalation in (None, BASE_ESCALATION) else f"_esc{int(escalation)}"
    return f"v3_{agent}{suffix}_seed{seed}"


def jobs():
    """Seed-major for the main comparison, so every finished batch holds all three agents;
    the sensitivity runs come last."""
    main = [(agent, seed, None) for seed in SEEDS for agent in AGENTS]
    sensitivity = [("shielded", seed, esc) for esc in SENSITIVITY_ESCALATION for seed in SEEDS]
    return main + sensitivity


def command(agent, seed, escalation):
    cmd = [sys.executable, "-m", "experiments.pilot.train_dqn", "--agent", agent, "--seed", str(seed),
           "--model", str(MODEL.relative_to(ROOT)), "--settings", str(SETTINGS.relative_to(ROOT)),
           "--steps", str(STEPS), "--double-q", "--exploration-steps", str(EXPLORATION_STEPS),
           "--every", str(EVERY), "--threads", "1", "--name", run_name(agent, seed, escalation)]
    if escalation is not None:
        cmd += ["--escalation-minutes", str(escalation)]
    return cmd


def train(parallel):
    LOGS.mkdir(parents=True, exist_ok=True)
    queue = [j for j in jobs() if not (RUNS / run_name(*j) / "finished.json").exists()]
    running = []
    while queue or running:
        while queue and len(running) < parallel:
            job = queue.pop(0)
            name = run_name(*job)
            if (RUNS / name).exists():
                raise SystemExit(f"{name} exists but did not finish; delete it to retrain")
            log = open(LOGS / f"{name}.log", "w")
            running.append((name, subprocess.Popen(command(*job), cwd=ROOT, stdout=log, stderr=subprocess.STDOUT),
                            log))
            print(f"{time.strftime('%H:%M:%S')} started {name}", flush=True)
        time.sleep(10)
        for item in list(running):
            name, process, log = item
            if process.poll() is not None:
                log.close()
                running.remove(item)
                status = "finished" if process.returncode == 0 else f"FAILED ({process.returncode})"
                print(f"{time.strftime('%H:%M:%S')} {status} {name}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("stage", choices=["train", "evaluate"])
    parser.add_argument("--parallel", type=int, default=5)
    args, rest = parser.parse_known_args()
    if args.stage == "train":
        train(args.parallel)
    else:
        from experiments.pilot.evaluate_comparison import main as evaluate
        evaluate(rest)


if __name__ == "__main__":
    main()
