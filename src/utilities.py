from typing import List

import torch

from src.type_definitions import TrajectoryType


def list_of_tuples_to_tuple_of_tensors(transition_list):
    """
    Takes a list of tuples [(a, b, c....)] and outputs the tuple of each entry as a torch tensor. (tensor of as,
    tensor of bs, tensor of cs....)
    """
    res = []
    [res.append([]) for _ in range(len(transition_list[0]))]

    for point in transition_list:
        index = 0
        for entry in point:
            res[index].append(entry)
            index += 1

    res = [torch.tensor(entry, dtype=torch.float32) for entry in res]
    return tuple(res)


def get_reward_to_go(trajectory: TrajectoryType, discount_factor: float) -> List[float]:
    """
    :param discount_factor:
    :param trajectory: ordered list of trajectories (state, action, reward)
    :return: the list of discounted reward to go for each point in trajectory
    """

    T = len(trajectory)
    reward_index = 2  # TODO get the index of reward in a better cleaner way
    reward_to_go = []
    current_reward_to_go = 0
    for t in range(T - 1, -1, -1):
        reward = trajectory[t][reward_index]
        current_reward_to_go = reward + discount_factor * current_reward_to_go
        reward_to_go = [current_reward_to_go] + reward_to_go
    return reward_to_go


def update_exponential_average(model_to_update, new_model, update_factor):
    for weights_new, weights_old in zip(new_model.parameters(), model_to_update.parameters()):
        weights_old.data.copy_(update_factor * weights_new.data + (1.0 - update_factor) * weights_old.data)


def copy_model_and_optimizer(model, optimizer):
    model2 = type(model)()
    optimizer2 = type(optimizer)(model2.parameters(), lr=optimizer.defaults["lr"])
    # optimizer2.load_state_dict(optimizer.state_dict())

    return model, optimizer2