from multiprocessing import Process
import subprocess

from engine.engine import Game

def run_game_engine() -> None:
    """
    Runs the game engine process.
    """
    game = Game()
    game.run_match()

if __name__ == "__main__":
    player1_process = subprocess.Popen(["python", "python_skeleton/debugplayer.py", "--port", "50051"])
    player2_process = subprocess.Popen(["python", "python_skeleton/debugplayer.py", "--port", "50052"])

    game_engine_process = Process(target=run_game_engine)
    game_engine_process.start()
    game_engine_process.join()

    player1_process.terminate()
    player2_process.terminate()