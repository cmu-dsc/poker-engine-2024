# CMU Poker Bot Competition 2024 Engine

## Your job
Edit ```python_skeleton/player.py```

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
python -m venv .venv
source .venv/bin/activate
pip install -r ./engine/requirements.txt
pip install -r ./python_skeleton/requirements.txt
```
Then install streamlit, pillow
```bash
pip install streamlit==1.32.2
pip install pillow==10.2.0
streamlit run visualize.py
```

If you ever use any additional packages, be sure to regenerate `requirements.txt` like so:

```bash
pip freeze > python_skeleton/requirements.txt
```

## Gym env

Refer to ```test_gym_env.py``` and ```engine/gym_env.py``` for more details.

### With multiple bots
```python
from engine.gym_env import PokerEnv 

env = PokerEnv(num_rounds=1000)
(obs1, obs2), info = env.reset()
bot1, bot2 = random_bot, random_bot

done = False
while not done:
    if obs1["is_my_turn"]:
        action = bot1(obs1)
    else:
        action = bot2(obs2)
    (obs1, obs2), (reward1, reward2), done, trunc, info = env.step(action)
```

### With a single bot (enemy bot fixed)
```python
env = PokerEnv(num_rounds=10, opp_bot=random_bot)
(obs1, obs2) = env.reset()
bot = random_bot

done = False
while not done:
    action = bot(obs)
    obs, reward, done, trunc, info = env.step(action)
```
