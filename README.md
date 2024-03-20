# CMU Poker Bot Competition 2024 Engine

## To run

### As subprocesses

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r ./engine/requirements.txt
pip install -r ./python_skeleton/requirements.txt
python run.py
```

### With containers

(Requires docker installed):  
[Linux](https://docs.docker.com/engine/install/)  
[Mac](https://docs.docker.com/desktop/install/mac-install/)  
Brew: `brew cask install docker`  
[Windows](https://docs.docker.com/desktop/install/windows-install/)

```bash
./scripts/run_docker.sh
```

## To visualize

### Use the deployed app

https://cmu-poker-ai-2024.streamlit.app/


### Run locally

Make sure you have the environment set up as in the previous section.

```bash
pip install -r ./engine/requirements.txt
pip install -r ./python_skeleton/requirements.txt
```

```bash
pip install streamlit
streamlit run visualize.py
```

## Gym env

Refer to ```test_gym_env.py``` and ```engine/gym_env.py``` for more details.

### With multiple bots
```python
from engine.gym_env import PokerEnv 

env = PokerEnv(num_rounds=1000)
(obs1, obs2) = env.reset()
bot1, bot2 = random_bot, random_bot

done = False
while not done:
    if obs1["is_my_turn"]:
        action = bot1(obs1)
    else:
        action = bot2(obs2)
    (obs1, obs2), (reward1, reward2), done, _, _ = env.step(action)
```

### With a single bot (enemy bot fixed)
```python
env = PokerEnv(num_rounds=10, opp_bot=random_bot)
(obs1, obs2) = env.reset()
bot1 = random_bot

done = False
while not done:
    action = bot1(obs1)
    (obs1, obs2), (reward1, reward2), done, _, _ = env.step(action)
```