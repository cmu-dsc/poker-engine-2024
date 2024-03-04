from collections import namedtuple
from typing import Set, Type

from .config import *

from .evaluate import evaluate

from .engine import (
    Action,
    CallAction,
    CheckAction,
    FoldAction,
    RaiseAction,
    TerminalState,
)


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

    def proceed_street(self) -> "RoundState":
        """
        Resets the players' pips and advances the game tree to the next round of betting.
        """
        if self.street >= 2:  # After river, proceed to showdown
            return self.showdown()

        # Dealing the next card (flop or river) and advancing the street
        new_street = self.street + 1
        new_hands = self.hands
        if new_street in [1, 2]:  # Dealing a card for flop and river
            for i in range(len(new_hands)):
                new_hands[i].append(self.deck.deal(1))

        return RoundState(
            button=1 - self.button,  # Switching the dealer button
            street=new_street,
            pips=[0, 0],  # Resetting the current round's bet amounts
            stacks=self.stacks,
            hands=new_hands,
            deck=self.deck,
            previous_state=self,
        )

    def proceed(self, action: Action) -> "RoundState":
        """
        Advances the game tree by one action performed by the active player.
        """
        active = self.button % 2
        if isinstance(action, FoldAction):
            # Determine the amount lost by the folding player
            # If this is preflop, the SB loses their blind, and BB wins the SB amount
            if self.street == 0:  # Preflop
                sb_index = (
                    self.button % 2
                )  # SB is the player with the button in heads-up
                bb_index = 1 - sb_index
                delta = SMALL_BLIND if active == sb_index else BIG_BLIND
                deltas = [-delta if i == active else delta for i in range(2)]
            else:
                # Postflop, the pot could contain more than just the blinds
                delta = self.stacks[1 - active] - STARTING_STACK
                deltas = [delta, -delta] if active == 0 else [-delta, delta]
            return TerminalState(deltas, self)

        new_pips = list(self.pips)
        new_stacks = list(self.stacks)

        if isinstance(action, CallAction):
            # Player matches the current highest bet
            contribution = new_pips[1 - active] - new_pips[active]
            new_stacks[active] -= contribution
            new_pips[active] += contribution

        elif isinstance(action, CheckAction):
            # Player chooses not to bet further
            pass  # No change in pips or stacks

        elif isinstance(action, RaiseAction):
            # Player raises the bet
            contribution = action.amount - new_pips[active]
            new_stacks[active] -= contribution
            new_pips[active] += contribution

        # Check if both players have acted and the betting is equal
        if new_pips[0] == new_pips[1]:
            if self.street == 2:  # After river, proceed to showdown
                return self.showdown()
            else:
                # Proceed to the next street
                return self.proceed_street()

        # Update the game state and return
        return RoundState(
            button=1 - self.button,
            street=self.street,
            pips=new_pips,
            stacks=new_stacks,
            hands=self.hands,
            deck=self.deck,
            previous_state=self,
        )
