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
