"""Watches a training run: every `every` steps the greedy agent is scored on a fixed set of
tuning incidents, one line is appended to metrics.jsonl and a checkpoint is saved. The
dashboard reads both. Scoring uses its own environment and no exploration, so it does not
change what the agent learns, and it never touches the evaluation incidents.
"""
import json
import time
from pathlib import Path

import numpy as np
from stable_baselines3.common.callbacks import BaseCallback

from src.agents.dqn import AgentPolicy, REWARD_SCALE
from src.agents.exact import ExactPolicy
from src.evaluation import run_episodes, summarise

MONITOR_SEED = 3_000_000   # its own range, apart from training, tuning and evaluation incidents


class Recorder:
    """The agent as a policy, noting where it agrees with the exact policy and its value
    estimate at the start of each incident."""

    def __init__(self, model, layout, exact=None):
        self.agent, self.layout, self.exact = AgentPolicy(model), layout, exact
        self.agree = self.compared = 0
        self.start_values, self.exact_start_values = [], []

    def __call__(self, obs, mask):
        action = self.agent(obs, mask)
        status, symptoms, context, t, blocked = self.layout.decode(obs)
        if t == 0:
            self.start_values.append(float(np.max(self.agent.model.q_values(np.concatenate([obs, mask])))))
        if self.exact is not None and not blocked:
            self.compared += 1
            self.agree += action == self.exact(obs, mask)
            if t == 0:
                self.exact_start_values.append(float(np.nanmax(self.exact.solution.q_values(status, symptoms, context))))
        return action


class TrainingMonitor(BaseCallback):
    def __init__(self, run_dir, make_eval_env, exact_solution=None, every=10_000, n_incidents=1000):
        super().__init__()
        self.run_dir = Path(run_dir)
        self.make_eval_env, self.exact_solution = make_eval_env, exact_solution
        self.every, self.n_incidents = every, n_incidents
        (self.run_dir / "checkpoints").mkdir(parents=True, exist_ok=True)

    def _on_training_start(self):
        self.started = time.time()
        self.evaluate()

    def _on_step(self):
        if self.num_timesteps % self.every == 0:
            self.evaluate()
        return True

    def evaluate(self):
        env = self.make_eval_env()
        layout = env.unwrapped.layout
        exact = ExactPolicy(env, self.exact_solution) if self.exact_solution is not None else None
        recorder = Recorder(self.model, layout, exact)
        m = summarise(run_episodes(recorder, env, self.n_incidents, first_seed=MONITOR_SEED))
        episodes = list(self.model.ep_info_buffer)
        elapsed = time.time() - self.started
        row = {
            "step": int(self.num_timesteps),
            "seconds": round(elapsed, 1),
            "steps_per_second": round(self.num_timesteps / elapsed, 1) if elapsed > 0 else None,
            "exploration_rate": float(self.model.exploration_rate),
            "loss": self.model.logger.name_to_value.get("train/loss"),
            "training_return": float(np.mean([e["r"] for e in episodes]) * REWARD_SCALE) if episodes else None,
            "learned_start_value": float(np.mean(recorder.start_values)),
            "exact_start_value": float(np.mean(recorder.exact_start_values)) if recorder.exact_start_values else None,
            "agreement_with_exact": recorder.agree / recorder.compared if recorder.compared else None,
            **{k: v for k, v in m.items() if not isinstance(v, tuple)},
            "return_ci": list(m["return_ci"]),
        }
        with open(self.run_dir / "metrics.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=_jsonable) + "\n")
        self.model.save(self.run_dir / "checkpoints" / f"step_{self.num_timesteps:07d}")


def _jsonable(value):
    if isinstance(value, float) and value != value:
        return None
    return float(value)
