import gym
import torch
from matplotlib import pyplot as plt
from torch import nn as nn
from torch.distributions import Categorical, MultivariateNormal

from src.algorithms.actor_critic import ActorCriticBootstrappedVEstimate
from src.agent import Agent
from src.epsilon_greedy import DecayingEpsilonGreedyQPolicy, GreedyQPolicy
from src.algorithms.policy_gradient import PolicyGradient
from src.algorithms.ppo import PPO
from src.algorithms.dqn import DQN


def cartpoloe():
    training = True

    if training:
        environment = gym.make("CartPole-v1")
        q_model = nn.Sequential(
            nn.Linear(4, 24),
            nn.ReLU(),
            nn.Linear(24, 24),
            nn.ReLU(),
            nn.Linear(24, 2)
        )

        optimizer = torch.optim.Adam(q_model.parameters(), lr=0.001)

        learner = DQN(
            environment=environment,
            q_model=q_model, optimizer=optimizer,
            exploration_policy=
            DecayingEpsilonGreedyQPolicy(q_model, initial_epsilon=1.0, decay_factor=0.95, min_epsilon=0.05)
        )

        opt_policy, history = learner.learn_policy(episodes=200)
        plt.plot(history)
        plt.xlabel('episode')
        plt.ylabel('total reward')
        plt.savefig("score.png")
        # torch.save(q_model.module, "learned networks/cartpole/q_network.torch")

        agent = Agent(environment=environment, policy=opt_policy)
        input("add anything to continue")
        agent.perform_episode(render=True)

    else:
        environment = gym.make("CartPole-v1")
        q_model = torch.load("learned networks/cartpole/q_network.torch")
        opt_policy = GreedyQPolicy(q_model)
        agent = Agent(environment=environment, policy=opt_policy)
        agent.perform_episode(render=True)


def pl_grad():
    print("hi")
    environment = gym.make("CartPole-v1")
    net = nn.Sequential(
        nn.Linear(4, 40, bias=False),
        nn.ReLU(),
        nn.Linear(40, 2, bias=False),
        nn.Softmax(dim=1)
    )

    class distributionNet(nn.Module):
        def __init__(self):
            super(distributionNet, self).__init__()
            self.net = net

        def forward(self, x):
            return Categorical(self.net(x))

    a_model = distributionNet()
    optimizer = torch.optim.Adam(a_model.parameters(), lr=0.01)
    learner = PolicyGradient(environment, a_model, optimizer, discount_factor=0.99)
    opt_policy, history = learner.learn_policy(epochs=500, episodes_per_update=1)

    plt.plot(history)
    plt.xlabel('episode')
    plt.ylabel('total reward')
    plt.savefig("score.png")

    agent = Agent(environment=environment, policy=opt_policy)
    input("add anything to continue")
    agent.perform_episode(render=True)

    # torch.save(actor, "learned networks/cartpole/a_network.torch")


def walker():
    environment = gym.make("Pendulum-v0")
    print(environment.action_space)
    print(environment.observation_space)

    class action_distribution_model(nn.Module):

        def __init__(self):
            super(action_distribution_model, self).__init__()
            self.secquential = nn.Sequential(
                nn.Linear(3, 24),
                nn.ReLU(),
                nn.Linear(24, 1, bias = False),
                nn.Tanh()
            )

        def forward(self, x):
            mean = self.secquential(x)
            mean = mean*4

            return MultivariateNormal(mean, torch.eye(1) * 0.25)

    distribution = action_distribution_model()
    optimizer = torch.optim.Adam(distribution.parameters(), lr=0.01)

    v_model = nn.Sequential(
        nn.Linear(3, 24),
        nn.ReLU(),
        nn.Linear(24, 1)
    )
    v_optimizer = torch.optim.Adam(v_model.parameters(), lr=0.01)

    learner = PPO(
        environment,
        distribution, optimizer, discount_factor=0.99)

    opt_policy, history = learner.learn_policy(
        epochs=250,
        actor_iterations=10,
        episodes_per_update=2
    )
    plt.plot(history)
    plt.xlabel('episode')
    plt.ylabel('total reward')
    plt.savefig("score.png")

    a = Agent(environment, opt_policy)
    while input("continue ") == "c":
        a.perform_episode(render=True)


def actor_critic_cartpole():
    environment = gym.make("CartPole-v1")
    for init_epochs in [0, 10, 15, 30]:
        net = nn.Sequential(
            nn.Linear(4, 40, bias=False),
            nn.ReLU(),
            nn.Linear(40, 2, bias=False),
            nn.Softmax(dim=1)
        )

        class distributionNet(nn.Module):
            def __init__(self):
                super(distributionNet, self).__init__()
                self.net = net

            def forward(self, x):
                return Categorical(self.net(x))

        a_model = distributionNet()
        optimizer = torch.optim.Adam(a_model.parameters(), lr=0.01)
        v_model = nn.Sequential(
            nn.Linear(4, 40),
            nn.ReLU(),
            nn.Linear(40, 1),
        )

        v_optimizer = torch.optim.Adam(v_model.parameters(), lr=0.01)
        learner = ActorCriticBootstrappedVEstimate(
            environment,
            a_model, optimizer,
            v_model, v_optimizer,
            discount_factor=0.99,
        )

        opt_policy, history = learner.learn_policy(
            epochs=500,
            v_initialization_episodes=init_epochs
        )

        plt.plot(history)

    plt.xlabel('episode')
    plt.ylabel('total reward')
    plt.savefig("score.png")


def ppo():
    class actor_model(nn.Module):
        def __init__(self):
            super(actor_model, self).__init__()

            self.net = nn.Sequential(
                nn.Linear(4, 40, bias=False),
                nn.ReLU(),
                nn.Linear(40, 2, bias=False),
                nn.Softmax(dim=1)
            )

        def forward(self, x):
            y = self.net(x)
            return Categorical(y)

    actor = actor_model()
    a_optimizer = torch.optim.Adam(actor.parameters(), lr=0.01)

    critic = nn.Sequential(
        nn.Linear(4, 20),
        nn.ReLU(),
        nn.Linear(20, 1)
    )

    c_optimizer = torch.optim.Adam(critic.parameters(), lr=0.01)

    environment = gym.make("CartPole-v1")
    learner = PPO(
        environment,
        actor, a_optimizer,
        critic, c_optimizer,
        discount_factor=0.99)

    opt, rew = learner.learn_policy(
        epochs=250,
        actor_iterations=100,
        critic_iterations=20,
        episodes_per_update=1
    )

    plt.plot(rew)
    plt.xlabel('episode')
    plt.ylabel('total reward')
    plt.savefig("score.png")