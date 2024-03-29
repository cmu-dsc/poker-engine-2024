from collections import namedtuple
from typing import Set, Type
from itertools import combinations

from .actions import (
    Action,
    CallAction,
    CheckAction,
    FoldAction,
    RaiseAction,
    TerminalState,
)
from .config import BIG_BLIND, STARTING_STACK
from .evaluate import evaluate


class RoundState(
    namedtuple(
        "_RoundState",
        [
            "button",
            "street",
            "pips",
            "stacks",
            "hands",
            "board",
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
        if len(self.board) < 2: #equity chop ALL IN!
            p0Eq = 0
            comb = 0
            for combo in combinations(self.deck.cards, 2 - len(self.board)):
                board = self.board + list(combo)
                score0 = evaluate(self.hands[0], board)
                score1 = evaluate(self.hands[1], board)
                if score0 > score1: p0Eq += 2
                if score0 == score1: p0Eq += 1
                comb += 2
            delta = round(2 * STARTING_STACK * p0Eq / comb) - STARTING_STACK
        else:
            score0 = evaluate(self.hands[0], self.board)
            score1 = evaluate(self.hands[1], self.board)
            if score0 > score1:
                delta = STARTING_STACK - self.stacks[1]
            elif score0 < score1:
                delta = self.stacks[0] - STARTING_STACK
            else:  # split the pot
                delta = (self.stacks[0] - self.stacks[1]) // 2
        return TerminalState([delta, -delta], self)

    def legal_actions(self) -> Set[Type]:
        """
        Returns a set which corresponds to the active player's legal moves.
        """
        active = self.button % 2
        continue_cost = self.pips[1 - active] - self.pips[active]

        if continue_cost == 0:
            # we can only raise the stakes if both players can afford it
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

    def raise_bounds(self) -> tuple[int, int]:
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
        if self.street >= 2 or sum(self.stacks)==0:  # After river, proceed to showdown OR equity chop
            return self.showdown()

        # Dealing the next card (flop or river) and advancing the street
        new_street = self.street + 1
        if new_street in [1, 2]:  # Dealing a card for flop and river
            self.board.extend(self.deck.deal(1))

        return RoundState(
            button=1,
            street=new_street,
            pips=[0, 0],  # Resetting the current round's bet amounts
            stacks=self.stacks,
            hands=self.hands,
            board=self.board,
            deck=self.deck,
            previous_state=self,
        )

    def proceed(self, action: Action) -> "RoundState":
        """
        Advances the game tree by one action performed by the active player.
        """
        active = self.button % 2
        if isinstance(action, FoldAction):
            delta = (
                self.stacks[0] - STARTING_STACK
                if active == 0
                else STARTING_STACK - self.stacks[1]
            )
            return TerminalState([delta, -delta], self)

        new_pips = list(self.pips)
        new_stacks = list(self.stacks)

        if isinstance(action, CallAction):
            if self.button == 0:  # sb calls bb preflop
                return RoundState(
                    button=1,
                    street=0,
                    pips=[BIG_BLIND] * 2,
                    stacks=[STARTING_STACK - BIG_BLIND] * 2,
                    hands=self.hands,
                    board=self.board,
                    deck=self.deck,
                    previous_state=self,
                )
            contribution = new_pips[1 - active] - new_pips[active]
            new_stacks[active] -= contribution
            new_pips[active] += contribution
            state = RoundState(
                button=self.button + 1,
                street=self.street,
                pips=new_pips,
                stacks=new_stacks,
                hands=self.hands,
                board=self.board,
                deck=self.deck,
                previous_state=self,
            )
            return state.proceed_street()

        elif isinstance(action, CheckAction):
            if (self.street == 0 and self.button > 0) or self.button > 1:
                # both players acted
                return self.proceed_street()
            return RoundState(
                button=self.button + 1,
                street=self.street,
                pips=self.pips,
                stacks=self.stacks,
                hands=self.hands,
                board=self.board,
                deck=self.deck,
                previous_state=self,
            )

        elif isinstance(action, RaiseAction):
            contribution = action.amount - new_pips[active]
            new_stacks[active] -= contribution
            new_pips[active] += contribution
            return RoundState(
                button=self.button + 1,
                street=self.street,
                pips=new_pips,
                stacks=new_stacks,
                hands=self.hands,
                board=self.board,
                deck=self.deck,
                previous_state=self,
            )
