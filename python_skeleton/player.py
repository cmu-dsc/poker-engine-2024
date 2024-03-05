"""
Simple example pokerbot, written in Python.
"""

from skeleton.actions import Action, CallAction, CheckAction, RaiseAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot


class Player(Bot):
    """
    A pokerbot.
    """

    def __init__(self) -> None:
        """
        Called when a new game starts. Called exactly once.
        """
        pass

    def handle_new_round(
        self, game_state: GameState, round_state: RoundState, active: int
    ) -> None:
        """
        Called when a new round starts. Called NUM_ROUNDS times.
        """
        pass

    def handle_round_over(
        self, game_state: GameState, terminal_state: TerminalState, active: int
    ) -> None:
        """
        Called when a round ends. Called NUM_ROUNDS times.
        """
        pass

    def get_action(
        self, game_state: GameState, round_state: RoundState, active: int
    ) -> Action:
        """
        Where the magic happens - your code should implement this function.
        Called any time the engine needs an action from your bot.
        """
        legal_actions = round_state.legal_actions()  # the actions you are allowed to take
        street = round_state.street  # 0, 1, or 2 representing pre-flop, flop, or river respectively
        my_cards = round_state.hands[active]  # your cards
        board_cards = round_state.deck.peek(street)  # the board cards
        my_pip = round_state.pips[active]  # the number of chips you have contributed to the pot this round of betting
        opp_pip = round_state.pips[1 - active]  # the number of chips your opponent has contributed to the pot this round of betting
        my_stack = round_state.stacks[active]  # the number of chips you have remaining
        opp_stack = round_state.stacks[1 - active]  # the number of chips your opponent has remaining
        continue_cost = opp_pip - my_pip  # the number of chips needed to stay in the pot
        my_contribution = STARTING_STACK - my_stack  # the number of chips you have contributed to the pot
        opp_contribution = STARTING_STACK - opp_stack  # the number of chips your opponent has contributed to the pot

        if RaiseAction in legal_actions:
            min_raise, max_raise = round_state.raise_bounds()  # the smallest and largest numbers of chips for a legal bet/raise
            # Simple strategy: always raise the maximum amount
            return RaiseAction(max_raise)
        
        if CheckAction in legal_actions:
            return CheckAction()

        return CallAction()
    

if __name__ == "__main__":
    run_bot(Player(), parse_args())
