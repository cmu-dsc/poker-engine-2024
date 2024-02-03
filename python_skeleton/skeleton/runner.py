"""
The infrastructure for interacting with the engine.
"""
import argparse
import socket
from .actions import Action, FoldAction, CallAction, CheckAction, RaiseAction
from .states import GameState, TerminalState, RoundState
from .states import STARTING_STACK, BIG_BLIND, SMALL_BLIND
from .bot import Bot


class Runner:
    """
    Interacts with the engine.
    """

    def __init__(self, pokerbot: Bot, socketfile):
        self.pokerbot: Bot = pokerbot
        self.socketfile = socketfile

    def receive(self):
        """
        Generator for incoming messages from the engine.
        """
        while True:
            packet = self.socketfile.readline().strip().split(" ")
            if not packet:
                break
            yield packet

    def send(self, action: Action):
        """
        Encodes an action and sends it to the engine.
        """
        code = ""
        if isinstance(action, FoldAction):
            code = "F"
        elif isinstance(action, CallAction):
            code = "C"
        elif isinstance(action, CheckAction):
            code = "K"
        elif isinstance(action, RaiseAction):
            code = "R" + str(action.amount)

        self.socketfile.write(code + "\n")
        self.socketfile.flush()

    def run(self):
        """
        Reconstructs the game tree based on the action history received from the engine.
        """
        game_state = GameState(STARTING_STACK, 0.0, 1)
        round_state = None
        active = 0
        for packet in self.receive():
            # Process packet to update game_state and round_state here
            # Omitted for brevity, use provided logic as a guide

            if round_state is None or isinstance(round_state, TerminalState):
                self.send(CheckAction())
            else:
                assert active == round_state.button % 2
                action = self.pokerbot.get_action(game_state, round_state, active)
                self.send(action)


def parse_args():
    """
    Parses arguments corresponding to socket connection information.
    """
    parser = argparse.ArgumentParser(description="Poker bot runner.")
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help='Host to connect to, defaults to "localhost".',
    )
    parser.add_argument("--port", type=int, help="Port on host to connect to.")
    return parser.parse_args()


def run_bot(pokerbot: Bot, args):
    """
    Initializes a connection and runs the pokerbot.
    """
    with socket.create_connection((args.host, args.port)) as sock:
        socketfile = sock.makefile("rw")
        runner = Runner(pokerbot, socketfile)
        runner.run()
