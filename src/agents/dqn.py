"""The learning agent: DQN with action masking (adapted from the manual's masked_dqn.py),
plus the training wrappers and the settings agreed in the pilot plan (Section 2, Agent).

The environment's action mask is appended to the observation. Masking the Q-values inside
the network covers action selection and the max in the learning target.
"""
import gymnasium as gym
import numpy as np
import torch
import torch.nn.functional as F
from gymnasium import spaces
from stable_baselines3 import DQN
from stable_baselines3.dqn.policies import DQNPolicy, QNetwork

from src.rules.safety import RuleMonitor, SafetyMechanism
from src.sim.triage_env import TriageEnv

REWARD_SCALE = 10.0        # rewards are divided by this during training only
AGENTS = ("shielded", "unconstrained", "penalty")


class MaskInObservation(gym.ObservationWrapper):
    def __init__(self, env):
        super().__init__(env)
        n, base = env.action_space.n, env.observation_space
        self.observation_space = spaces.Box(0.0, 1.0, shape=(base.shape[0] + n,), dtype=np.float32)

    def observation(self, obs):
        return np.concatenate([obs, self.env.action_masks().astype(np.float32)])

    def action_masks(self):
        return self.env.action_masks()


class ScaleReward(gym.RewardWrapper):
    def reward(self, reward):
        return reward / REWARD_SCALE

    def action_masks(self):
        return self.env.action_masks()


def make_env(scenario, agent="shielded", penalty=10.0, train=True, **env_kwargs):
    """shielded: safety mechanism; unconstrained: rules recorded, not enforced;
    penalty: not enforced, with a penalty per violation. Training adds the reward scaling and
    puts the mask in the observation; without `train` it is the form src.evaluation runs,
    and AgentPolicy appends the mask itself."""
    env = TriageEnv(scenario, **env_kwargs)
    if agent == "shielded":
        env = SafetyMechanism(env)
    elif agent == "unconstrained":
        env = RuleMonitor(env)
    elif agent == "penalty":
        env = RuleMonitor(env, penalty=penalty)
    else:
        raise ValueError(f"agent must be one of {AGENTS}")
    if train:
        env = MaskInObservation(ScaleReward(env))
    return env


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
    """Random actions respect the mask, and a share `check_bias` of them are checks, so that
    exploration reaches deep investigations (plan, Section 2: training risk)."""

    def __init__(self, *args, n_checks=0, check_bias=0.8, double_q=False, **kwargs):
        self.n_checks, self.check_bias, self.double_q = n_checks, check_bias, double_q
        super().__init__(*args, **kwargs)

    def train(self, gradient_steps, batch_size=100):
        """Stable-Baselines3's DQN update, with the Double DQN target as an option: the online
        network picks the next action and the target network values it, which reduces the
        overestimation that the max in the plain target causes."""
        self.policy.set_training_mode(True)
        self._update_learning_rate(self.policy.optimizer)
        losses = []
        for _ in range(gradient_steps):
            replay_data = self.replay_buffer.sample(batch_size, env=self._vec_normalize_env)
            discounts = replay_data.discounts if replay_data.discounts is not None else self.gamma
            with torch.no_grad():
                next_q = self.q_net_target(replay_data.next_observations)
                if self.double_q:
                    best = self.q_net(replay_data.next_observations).argmax(dim=1, keepdim=True)
                    next_q = torch.gather(next_q, dim=1, index=best)
                else:
                    next_q = next_q.max(dim=1)[0].reshape(-1, 1)
                target = replay_data.rewards + (1 - replay_data.dones) * discounts * next_q
            current = torch.gather(self.q_net(replay_data.observations), dim=1, index=replay_data.actions.long())
            loss = F.smooth_l1_loss(current, target)
            losses.append(loss.item())
            self.policy.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.policy.parameters(), self.max_grad_norm)
            self.policy.optimizer.step()
        self._n_updates += gradient_steps
        self.logger.record("train/n_updates", self._n_updates, exclude="tensorboard")
        self.logger.record("train/loss", np.mean(losses))

    def _masked_random(self, obs):
        n = int(self.action_space.n)
        masks = np.asarray(obs).reshape(-1, np.asarray(obs).shape[-1])[:, -n:] > 0.5
        actions = []
        for mask in masks:
            checks = np.flatnonzero(mask[:self.n_checks])
            others = np.flatnonzero(mask[self.n_checks:]) + self.n_checks
            pool = checks if len(checks) and (len(others) == 0 or np.random.rand() < self.check_bias) else others
            actions.append(int(np.random.choice(pool)))
        return np.array(actions)

    def predict(self, observation, state=None, episode_start=None, deterministic=False):
        if not deterministic and np.random.rand() < self.exploration_rate:
            return self._masked_random(observation), state       # masked epsilon-greedy
        return self.policy.predict(observation, state, episode_start, deterministic)

    def _sample_action(self, learning_starts, action_noise=None, n_envs=1):
        if self.num_timesteps < learning_starts:                  # masked warm-up
            action = self._masked_random(self._last_obs)
            return action, action
        return super()._sample_action(learning_starts, action_noise, n_envs)

    def q_values(self, obs_with_mask):
        """Q-values in reward units (unscaled), -inf for masked actions."""
        with torch.no_grad():
            tensor = torch.as_tensor(obs_with_mask, dtype=torch.float32, device=self.device)[None]
            q = self.q_net(tensor)[0].cpu().numpy().astype(float) * REWARD_SCALE
        q[np.asarray(obs_with_mask)[-len(q):] < 0.5] = -np.inf
        return q


HYPERPARAMETERS = dict(
    learning_rate=1e-4, buffer_size=200_000, learning_starts=1_000, batch_size=64,
    gamma=1.0, train_freq=4, gradient_steps=1, target_update_interval=1_000,
    exploration_fraction=0.5, exploration_initial_eps=1.0, exploration_final_eps=0.05,
    check_bias=0.8, double_q=False, net_arch=[128, 128],
)


def build_model(env, seed, hyperparameters=HYPERPARAMETERS):
    hp = dict(hyperparameters)
    net_arch = hp.pop("net_arch")
    return MaskedDQN(MaskedDQNPolicy, env, n_checks=env.unwrapped.n_checks, seed=seed,
                     policy_kwargs=dict(net_arch=net_arch), verbose=0, **hp)


class AgentPolicy:
    """Wraps a trained model as a policy for src.evaluation: greedy, with the mask appended."""
    name = "DQN"

    def __init__(self, model):
        self.model = model

    def __call__(self, obs, mask):
        full = np.concatenate([obs, mask.astype(np.float32)])
        return int(self.model.predict(full, deterministic=True)[0])
