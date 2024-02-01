"""
Encapsulates game and round state information for the player.
"""
from collections import namedtuple
from typing import List, Tuple

from actions import Action, FoldAction, CallAction, CheckAction, RaiseAction

# Constants for game settings
NUM_ROUNDS = 1000
STARTING_STACK = 400
BIG_BLIND = 2
SMALL_BLIND = 1

# GameState for overall game information
GameState = namedtuple("GameState", ["bankroll", "game_clock", "round_num"])

# TerminalState for end-of-round information
TerminalState = namedtuple("TerminalState", ["deltas", "previous_state"])


class RoundState(
    namedtuple(
        "_RoundState",
        ["button", "street", "pips", "stacks", "hands", "deck", "previous_state"],
    )
):
    """
    Encodes the game tree for one round of poker.
    """

    def showdown(self) -> TerminalState:
        """
        Compares the players' hands and computes payoffs.
        """
        # Implement logic to compare hands and determine the winner
        # For simplicity, return a placeholder TerminalState
        return TerminalState([0, 0], self)

    def legal_actions(self) -> List:
        """
        Returns a list which corresponds to the active player's legal moves.
        """
        active = self.button % 2
        continue_cost = self.pips[1 - active] - self.pips[active]
        if continue_cost == 0:
            bets_forbidden = self.stacks[0] == 0 or self.stacks[1] == 0
            return [CheckAction] if bets_forbidden else [CheckAction, RaiseAction]
        raises_forbidden = (
            continue_cost >= self.stacks[active] or self.stacks[1 - active] == 0
        )
        return (
            [FoldAction, CallAction]
            if raises_forbidden
            else [FoldAction, CallAction, RaiseAction]
        )

    def raise_bounds(self) -> Tuple[int, int]:
        """
        Returns a tuple of the minimum and maximum legal raises.
        """
        active = self.button % 2
        continue_cost = self.pips[1 - active] - self.pips[active]
        max_contribution = min(
            self.stacks[active], self.stacks[1 - active] + continue_cost
        )
        min_contribution = max(BIG_BLIND, continue_cost)
        return (
            self.pips[active] + min_contribution,
            self.pips[active] + max_contribution,
        )

    def proceed_street(self) -> "RoundState":
        """
        Advances the game tree to the next round of betting.
        """
        new_street = self.street + 1
        # Assuming streets are numbered as 0: preflop, 1: flop, 2: river
        if new_street > 2:  # After river, proceed to showdown
            return self.showdown()
        else:
            # Reset pips for the new betting round
            new_pips = [0, 0]
            return self._replace(street=new_street, pips=new_pips)

    def proceed(self, action: Action) -> "RoundState":
        """
        Advances the game tree by one action performed by the active player.
        """
        active = self.button % 2
        if isinstance(action, FoldAction):
            # Handle fold; the other player wins the pot
            delta = STARTING_STACK - self.stacks[1 - active]
            return TerminalState([delta, -delta], self)

        elif isinstance(action, CallAction):
            # Match the opponent's bet
            continue_cost = self.pips[1 - active] - self.pips[active]
            new_stacks = list(self.stacks)
            new_stacks[active] -= continue_cost
            new_pips = list(self.pips)
            new_pips[active] += continue_cost
            # Check if it's time to proceed to the next street
            if sum(new_pips) == sum(self.pips):  # Both players have acted
                return self.proceed_street()._replace(stacks=new_stacks, pips=new_pips)
            else:
                return self._replace(stacks=new_stacks, pips=new_pips)

        elif isinstance(action, CheckAction):
            # Proceed if both players have checked or it's a response to a check
            if sum(self.pips) == 0 or self.pips[active] == self.pips[1 - active]:
                return self.proceed_street()
            else:
                return self

        elif isinstance(action, RaiseAction):
            # Increase the bet
            contribution = action.amount - self.pips[active]
            new_stacks = list(self.stacks)
            new_stacks[active] -= contribution
            new_pips = list(self.pips)
            new_pips[active] += contribution
            return self._replace(stacks=new_stacks, pips=new_pips)
