from engine.gym_env import PokerEnv 

env = PokerEnv(3)
(obs1, obs2) = env.reset()
for i in range(10):
    action = env.action_space.sample()
    (obs1, obs2), (reward1, reward2), done, _, _ = env.step(action)
    if done:
        break