import math
from random import randint, shuffle
from type_definitions import *
import matplotlib.pyplot as plt


class AgentObserver(object):
    def on_episode_start(self, **kwargs):
        raise NotImplementedError

    def on_step(self, **kwargs):
        raise NotImplementedError

    def on_episode_end(self):
        raise NotImplementedError


class TrajectoryObserver(AgentObserver):
    def __init__(self, buffer_size=math.inf):
        """
        Stores trajectories performed by agent it attaches to. Currently it only supports being attached to only one active agent
        :param buffer_size max amount of stored trajectories to have. Older trajectories are discarded
        """
        self.sampled_trajectories = []
        self.buffer_size = buffer_size

    def on_episode_start(self, **kwargs):
        if len(self.sampled_trajectories) == self.buffer_size:
            self.sampled_trajectories = self.sampled_trajectories[1:]

        self.sampled_trajectories.append([])

    def on_step(self, state=None, action=None, reward=None, **kwargs):
        current_trajectory_index = len(self.sampled_trajectories) - 1
        self.sampled_trajectories[current_trajectory_index] += [(state, action, reward)]

    def on_episode_end(self):
        pass

    def clear_trajectories(self):
        self.sampled_trajectories = []

    @staticmethod
    def get_reward_to_go(trajectory: TrajectoryType, discount_factor: float) -> List[float]:
        """
        :param discount_factor:
        :param trajectory: ordered list of transitions (state, action, reward)
        :return: the list of discounted reward to go for each point in trajectory
        """

        T = len(trajectory)
        reward_index = 2  # TODO get the index of reward in a better cleaner way
        reward_to_go = []
        current_reward_to_go = 0
        for t in range(T - 1, -1, 0):
            reward = trajectory[t][reward_index]
            current_reward_to_go = reward + discount_factor * current_reward_to_go
            reward_to_go = [current_reward_to_go] + reward_to_go
        return reward_to_go

    def sample_transitions_from_stored_trajectories(self, n_samples) \
            -> List[Tuple[StateType, ActionType, float, StateType, bool]]:
        """
        Samples transitions from stored trajectories. In case of terminal state, it loops to first in trajectory

        :param n_samples: number of samples to take
        :return: a list of (state, action, reward, state_next, done).
        """
        n = self.amount_of_stored_transitions()
        ind_samples = [randint(0, n-1) for _ in range(n_samples)]
        ind_samples.sort()
        res = []
        state_index = 0

        iter_trajectory = iter(self.sampled_trajectories)
        current_transition_ind = 0
        trajectory = next(iter_trajectory)

        for ind_sample in ind_samples:
            # advance trajectories until sample is in current trajectory
            i = ind_sample - current_transition_ind
            while i >= len(trajectory):
                current_transition_ind += len(trajectory)
                trajectory = next(iter_trajectory)
                i = ind_sample - current_transition_ind

            # construct transition
            state_next = trajectory[0][state_index]  # in case there is no default state
            done = i == len(trajectory) - 1

            if not done:
                state_next = trajectory[i + 1][state_index]

            transition = trajectory[i] + (state_next, done)
            res.append(transition)

        # the transitions are ordered in time, so they do not behave exactly like a batch of sampled transitions
        # to solve this problem, shuffle res before return
        shuffle(res)

        return res

    def amount_of_stored_transitions(self) -> int:
        """
        Sums all the transitions in all the already sampled trajectories
        """
        res = 0
        for t in self.sampled_trajectories:
            res += len(t)
        return res


class RewardObserver(AgentObserver):
    def __init__(self):
        self.trajectory_rewards = []

    def on_episode_start(self, **kwargs):
        self.trajectory_rewards.append(0)

    def on_step(self, reward=0, **kwargs):
        self.trajectory_rewards[-1] += reward

    def on_episode_end(self):
        pass

    def plot(self):
        plt.plot(self.trajectory_rewards)
        plt.xlabel('episode')
        plt.ylabel('total reward')
        plt.savefig("score.png")