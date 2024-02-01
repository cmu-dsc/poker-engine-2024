"""
CMU Data Science Club Poker Bot Competition Game Engine 2024
"""

"""
the deck consists of 18 cards, ranked 1 to 6, with 3 suits.

each player is dealt 1 card preflop. A round of betting occurs.

there is a flop, of 1 card. A round of betting occurs.

there is a river, of 1 card. A round of betting occurs.

The hand rankings involve 3 cards:
trips (6 combos)
straight flush (12 combos)
flush (48 combos)
straight (96 combos)
pair (270 combos)
high card (384 combos)
TOTAL: 816 combos
"""

from collections import namedtuple
from evaluate import evaluate
import eval7

from config import *

FoldAction = namedtuple("FoldAction", [])
CallAction = namedtuple("CallAction", [])
CheckAction = namedtuple("CheckAction", [])
RaiseAction = namedtuple("RaiseAction", ["amount"])
BidAction = namedtuple("BidAction", ["amount"])
TerminalState = namedtuple("TerminalState", ["deltas", "bids", "previous_state"])


class ShortDeck(eval7.Deck):
    """Custom deck for the poker variant with cards ranked 1 to 6 across 3 suits."""

    def __init__(self):
        card_ranks = "123456"
        card_suits = "shd"  # spades, hearts, diamonds
        self.cards = [
            eval7.Card(rank + suit) for suit in card_suits for rank in card_ranks
        ]
        super().__init__()


class RoundState(
    namedtuple(
        "_RoundState",
        [
            "button",
            "street",
            "auction",
            "bids",
            "pips",
            "stacks",
            "hands",
            "deck",
            "previous_state",
        ],
    )
):
    """Encodes the game tree for one round of poker."""

    def showdown(self) -> None:
        """
        Compares the player's hands and computes payoffs.
        """
        score0 = evaluate(self.hands[0])
        score1 = evaluate(self.hands[1])
        if score0 > score1:
            delta = STARTING_STACK - self.stacks[1]
        elif score0 < score1:
            delta = self.stacks[0] - STARTING_STACK
        else:  # split the pot
            delta = (self.stacks[0] - self.stacks[1]) // 2
        return TerminalState([delta, -delta], self.bids, self)

    def legal_actions(self) -> None:
        """
        Returns a set which corresponds to the active player's legal moves
        """

    def raise_bounds(self) -> None:
        """
        Returns a tuple of the minimum and maximum legal raises.
        """

    def bid_bounds(self) -> None:
        """
        Returns a tuple of the minimum and maximum legal bid amounts
        """

    def proceed_street(self) -> None:
        """
        Resets the players' pips and advances the game tree to the next round of betting.
        """

    def proceed(self, action) -> None:
        """
        Advances the game tree by one action performed by the active player.
        """


class Player:
    """
    Handles subprocess and socket interactions with one player's pokerbot.
    """

    def __init__(self) -> None:
        pass

    def build(self) -> None:
        """
        Loads the commands file and builds the pokerbot.
        """

    def run(self) -> None:
        """
        Runs the pokerbot and establishes the socket connection.
        """

    def stop(self) -> None:
        """
        Closes the socket connection and stops the pokerbot.
        """

    def query(self, round_state, player_message, game_log) -> None:
        """
        Requests one action from the pokerbot over the socket connection.
        At the end of the round, we request a CheckAction from the pokerbot.
        """


class Game:
    """
    Manages logging and the high-level game procedure.
    """

    def __init__(self) -> None:
        pass

    def log_round_state(self, players, round_state) -> None:
        """
        Incorporates RoundState information into the game log and player messages.
        """

    def log_action(self, name, action, bet_override) -> None:
        """
        Incorporates action information into the game log and player messages.
        """

    def log_terminal_state(self, players, round_state) -> None:
        """
        Incorporates TerminalState information into the game log and player messages.
        """

    def run_round(self, players):
        """
        Runs one round of poker (1 hand).
        """

    def run(self):
        """
        Runs one game of poker.
        """


if __name__ == "__main__":
    Game().run()
