import numpy as np
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3.common.monitor import Monitor
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from toy_triage_env import ToyTriageEnv
from masked_dqn import MaskedDQN, MaskedDQNPolicy


class MaskInObservation(gym.ObservationWrapper):
    """Appends the action mask to the observation, for MaskedDQN."""

    def __init__(self, env):
        super().__init__(env)
        n, base = env.action_space.n, env.observation_space
        self.observation_space = spaces.Box(0.0, 1.0, shape=(base.shape[0] + n,), dtype=np.float32)

    def observation(self, obs):
        return np.concatenate([obs, self.env.unwrapped.action_masks().astype(np.float32)])


def evaluate(model, env, n=1000):
    outcomes = {}
    for k in range(n):
        obs, _ = env.reset(seed=10_000 + k)            # evaluation seeds never used in training
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True,
                                      **({"action_masks": env.action_masks()} if isinstance(model, MaskablePPO) else {}))
            obs, _, terminated, truncated, info = env.step(action)
            done = terminated or truncated
        outcomes[info["outcome"]] = outcomes.get(info["outcome"], 0) + 1
    return {k: v / n for k, v in sorted(outcomes.items())}


if __name__ == "__main__":
    # DQN: mask travels inside the observation.
    dqn_env = Monitor(MaskInObservation(ToyTriageEnv()))
    dqn = MaskedDQN(MaskedDQNPolicy, dqn_env, policy_kwargs=dict(net_arch=[128, 128]),
                    learning_starts=1_000, exploration_fraction=0.3, seed=0, verbose=0)
    dqn.learn(total_timesteps=100_000)
    print("DQN:", evaluate(dqn, MaskInObservation(ToyTriageEnv())))

    # PPO: mask supplied by the ActionMasker wrapper.
    ppo_env = ActionMasker(Monitor(ToyTriageEnv()), lambda e: e.unwrapped.action_masks())
    ppo = MaskablePPO("MlpPolicy", ppo_env, seed=0, verbose=0)
    ppo.learn(total_timesteps=30_000)
    print("PPO:", evaluate(ppo, ActionMasker(ToyTriageEnv(), lambda e: e.unwrapped.action_masks())))
