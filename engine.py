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
from typing import Set, Type
from evaluate import evaluate
import eval7

from config import *

FoldAction = namedtuple("FoldAction", [])
CallAction = namedtuple("CallAction", [])
CheckAction = namedtuple("CheckAction", [])
RaiseAction = namedtuple("RaiseAction", ["amount"])
TerminalState = namedtuple("TerminalState", ["deltas", "previous_state"])


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
            "pips",
            "stacks",
            "hands",
            "deck",
            "previous_state",
        ],
    )
):
    """Encodes the game tree for one round of poker."""

    def showdown(self) -> TerminalState:
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

    def legal_actions(self) -> Set[Type]:
        """
        Returns a set which corresponds to the active player's legal moves.
        """
        active = self.button % 2
        continue_cost = self.pips[1 - active] - self.pips[active]

        if continue_cost == 0:  # No additional chips required to stay in the hand
            bets_forbidden = self.stacks[0] == 0 or self.stacks[1] == 0
            return {CheckAction} if bets_forbidden else {CheckAction, RaiseAction}

        # If the active player must contribute more chips to continue
        raises_forbidden = (
            continue_cost >= self.stacks[active] or self.stacks[1 - active] == 0
        )
        return (
            {FoldAction, CallAction}
            if raises_forbidden
            else {FoldAction, CallAction, RaiseAction}
        )

    def raise_bounds(self) -> (int, int):
        """
        Returns a tuple of the minimum and maximum legal raises.
        """
        active = self.button % 2
        continue_cost = self.pips[1 - active] - self.pips[active]
        max_contribution = min(
            self.stacks[active], self.stacks[1 - active] + continue_cost
        )
        min_contribution = min(
            max_contribution, continue_cost + max(continue_cost, BIG_BLIND)
        )
        return (
            self.pips[active] + min_contribution,
            self.pips[active] + max_contribution,
        )

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
