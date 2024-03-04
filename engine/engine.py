"""
CMU Poker Bot Competition Game Engine 2024
"""

from collections import namedtuple, deque
from typing import Deque, List, Union

from .roundstate import RoundState
from .player import Player

from .evaluate import ShortDeck
from .config import *

FoldAction = namedtuple("FoldAction", [])
CallAction = namedtuple("CallAction", [])
CheckAction = namedtuple("CheckAction", [])
# we coalesce BetAction and RaiseAction for convenience
RaiseAction = namedtuple("RaiseAction", ["amount"])
Action = Union[FoldAction, CallAction, CheckAction, RaiseAction]
TerminalState = namedtuple("TerminalState", ["deltas", "previous_state"])

# i'm still not sure what these do tbh
CCARDS = lambda cards: ",".join(map(str, cards))
PCARDS = lambda cards: "[{}]".format(" ".join(map(str, cards)))
PVALUE = lambda name, value: ", {} ({})".format(name, value)
STATUS = lambda players: "".join([PVALUE(p.name, p.bankroll) for p in players])


class Game:
    """
    Manages logging and the high-level game procedure.
    """

    def __init__(self) -> None:
        self.players: List[Player] = []
        self.log: List[str] = [
            f"CMU Poker Bot Game - {PLAYER_1_NAME} vs {PLAYER_2_NAME}"
        ]
        self.new_actions: List[Deque[Action]] = [deque(), deque()]

    def log_round_state(self, round_state) -> None:
        """
        Logs the current state of the round.
        """
        # Implementation...

    def log_action(self, player_name: str, action, is_preflop: bool) -> None:
        """
        Logs an action taken by a player.
        """
        # Implementation...

    def log_terminal_state(self, round_state) -> None:
        """
        Logs the terminal state of a round, including outcomes.
        """
        # Implementation...

    def run_round(self, last_round: bool) -> None:
        """
        Runs one round of poker (1 hand).
        """
        deck = ShortDeck()
        deck.shuffle()
        hands = [deck.deal(1), deck.deal(1)]
        board = []
        pips = [SMALL_BLIND, BIG_BLIND]
        stacks = [STARTING_STACK - SMALL_BLIND, STARTING_STACK - BIG_BLIND]

        round_state = RoundState(0, 0, pips, stacks, hands, deck, None)
        self.new_actions = [deque, []]

        while not isinstance(round_state, TerminalState):
            self.log_round_state(RoundState)
            active = round_state.button % 2
            player = self.players[active]
            action = player.request_action(
                hands[active], board, self.new_actions[active]
            )
            # deal, bets for small blind, etc.
            # send start phase to bots
            # loop through players:
            # action request with previous players action if it exists
            # validate action, otherwise fold
            # add action to action_history
            # log action
            round_state = round_state.proceed()

        for player, delta in zip(self.players, delta):
            player.end_round(last_round)
            player.bankroll += delta
        self.log_terminal_state(round_state)

    def run_match(self) -> None:
        """
        Runs one game of poker.
        """
        print("Starting the Poker Game...")
        self.players = [
            Player(PLAYER_1_NAME, PLAYER_1_DNS),
            Player(PLAYER_2_NAME, PLAYER_2_DNS),
        ]

        if not all(player.check_ready() for player in self.players):
            print("One or more bots are not ready. Aborting the match.")
            return

        for round_num in range(1, NUM_ROUNDS + 1):
            self.log.append(f"\nRound #{round_num}")
            self.run_round(self.players, round_num == NUM_ROUNDS)
            self.players = self.players[::-1]  # Alternate the dealer

        self.finalize_log()

    def finalize_log(self) -> None:
        """
        Finalizes the game log, writing it to a file and uploading it.
        """
        log_filename = f"{GAME_LOG_FILENAME}.txt"
        log_index = 1
        while os.path.exists(log_filename):
            log_filename = f"{GAME_LOG_FILENAME}_{log_index}.txt"
            log_index += 1

        print(f"Writing {log_filename}")
        with open(log_filename, "w") as log_file:
            log_file.write("\n".join(self.log))

        # Placeholder for uploading log, adjust as necessary
        # upload_log_to_s3(log_filename)


if __name__ == "__main__":
    Game().run_match()
