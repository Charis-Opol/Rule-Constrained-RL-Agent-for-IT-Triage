"""DQN with action masking for Stable-Baselines3.

The environment appends its action mask (1 = allowed) to the end of the observation.
Masking the Q-values inside the network covers both action selection and the max in
the learning target, because the target network sees the mask in the next observation.
"""
import numpy as np
from stable_baselines3 import DQN
from stable_baselines3.dqn.policies import DQNPolicy, QNetwork


class MaskedQNetwork(QNetwork):
    def forward(self, obs):
        q = super().forward(obs)
        mask = obs[:, -int(self.action_space.n):]
        return q.masked_fill(mask < 0.5, -1e9)


class MaskedDQNPolicy(DQNPolicy):
    def make_q_net(self):
        net_args = self._update_features_extractor(self.net_args, features_extractor=None)
        return MaskedQNetwork(**net_args).to(self.device)


class MaskedDQN(DQN):
    def _masked_random(self, obs):
        n = int(self.action_space.n)
        masks = np.asarray(obs).reshape(-1, np.asarray(obs).shape[-1])[:, -n:].astype(np.int8)
        return np.array([self.action_space.sample(mask=m) for m in masks])

    def predict(self, observation, state=None, episode_start=None, deterministic=False):
        if not deterministic and np.random.rand() < self.exploration_rate:
            return self._masked_random(observation), state       # masked epsilon-greedy
        return self.policy.predict(observation, state, episode_start, deterministic)

    def _sample_action(self, learning_starts, action_noise=None, n_envs=1):
        if self.num_timesteps < learning_starts:                  # masked warm-up
            action = self._masked_random(self._last_obs)
            return action, action
        return super()._sample_action(learning_starts, action_noise, n_envs)
