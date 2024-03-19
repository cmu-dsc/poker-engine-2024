from engine.gym_env import PokerEnv 
import numpy as np

# 0: Fold, 1: Call, 2: Check, 3: Raise

def call_check_bot(obs):
    # Call if possible, otherwise check
    if obs["legal_actions"][1] == 1:
        return (1, 0)
    elif obs["legal_actions"][2] == 1:
        return (2, 0)

def raise_bot(obs):
    # Raise if possible, otherwise call or check
    if obs["legal_actions"][3] == 1:
        min_raise = obs["min_raise"]
        max_raise = obs["max_raise"]
        if np.random.rand() < 0.5:
            return (3, max_raise)
        else:
            return (3, min_raise)
    else:
        return call_check_bot(obs)
    
def random_bot(obs):
    # Randomly choose a legal action
    action_probs = np.random.rand(4)
    action_probs = action_probs * obs["legal_actions"]
    action = np.argmax(action_probs)
    if action == 3:
        min_raise = obs["min_raise"]
        max_raise = obs["max_raise"]
        print(min_raise, max_raise)
        raise_amount = np.random.randint(min_raise, max_raise+1)
        return (action, raise_amount)
    else:
        return (action, 0)

num_to_action = {0: "Fold", 1: "Call", 2: "Check", 3: "Raise"}

env = PokerEnv(10)
(obs1, obs2) = env.reset()
bot1, bot2 = random_bot, random_bot
print(obs1)
print(obs2)
print("\n")

done = False
while not done:
    if obs1["is_my_turn"]:
        action = bot1(obs1)
        print(f"Bot1: {num_to_action[action[0]]} {action[1]}")
    else:
        action = bot2(obs2)
        print(f"Bot2: {num_to_action[action[0]]} {action[1]}")

    (obs1, obs2), (reward1, reward2), done, _, _ = env.step(action)
    if reward1 != 0:
        print("New Round")
    print(obs1, reward1, done)
    print(obs2, reward2, done)
    print("\n")

