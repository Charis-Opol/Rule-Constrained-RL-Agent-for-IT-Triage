"""Phase 5: train the three agents with five seeds each, then evaluate them.

    python -m experiments.pilot.run_phase5 train --parallel 5
    python -m experiments.pilot.run_phase5 evaluate

Settings chosen in Phase 4: Double DQN, 500k steps, exploration falling to its final rate by
150k. Seeds 0-4 are the final-experiment seeds (tuning used seed 100).
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "results" / "pilot" / "runs"
LOGS = ROOT / "results" / "pilot" / "logs"
AGENTS = ("shielded", "unconstrained", "penalty")
SEEDS = (0, 1, 2, 3, 4)
STEPS, EXPLORATION_STEPS, EVERY = 500_000, 150_000, 25_000


def run_name(agent, seed):
    return f"phase5_{agent}_seed{seed}"


def train(parallel):
    LOGS.mkdir(parents=True, exist_ok=True)
    # Seed-major order, so every finished batch holds all three agents.
    queue = [(agent, seed) for seed in SEEDS for agent in AGENTS
             if not (RUNS / run_name(agent, seed) / "finished.json").exists()]
    running = []
    while queue or running:
        while queue and len(running) < parallel:
            agent, seed = queue.pop(0)
            name = run_name(agent, seed)
            if (RUNS / name).exists():
                raise SystemExit(f"{name} exists but did not finish; delete it to retrain")
            cmd = [sys.executable, "-m", "experiments.pilot.train_dqn", "--agent", agent, "--seed", str(seed),
                   "--steps", str(STEPS), "--double-q", "--exploration-steps", str(EXPLORATION_STEPS),
                   "--every", str(EVERY), "--threads", "1", "--name", name]
            log = open(LOGS / f"{name}.log", "w")
            running.append((name, subprocess.Popen(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT), log))
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
    args = parser.parse_args()
    if args.stage == "train":
        train(args.parallel)
    else:
        from experiments.pilot.evaluate_phase5 import main as evaluate
        evaluate()


if __name__ == "__main__":
    main()
