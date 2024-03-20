"""
This file contains the base class that you should implement for your pokerbot.
"""

from typing import Optional
from skeleton.actions import Action, FoldAction, CallAction, CheckAction, RaiseAction
from skeleton.states import GameState, RoundState, TerminalState


class Bot:
    """
    The base class for a pokerbot.
    """

    def handle_new_round(
        self, game_state: GameState, round_state: RoundState, active: int
    ) -> None:
        """
        Called when a new round starts. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Nothing.
        """
        raise NotImplementedError("handle_new_round")

    def handle_round_over(
        self, game_state: GameState, terminal_state: TerminalState, active: int, is_match_over: bool
    ) -> Optional[str]:
        """
        Called when a round ends. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        terminal_state: the TerminalState object.
        active: your player's index.
        is_match_over: last round in the match

        Returns:
        Your logs.
        """
        raise NotImplementedError("handle_round_over")

    def get_action(
        self, observation: dict
    ) -> Action:
        """
        Where the magic happens - your code should implement this function.
        Called any time the engine needs an action from your bot.

        Args:
            observation (dict): The observation of the current state.
            {
                "legal_actions": List of the Actions that are legal to take.
                "street": 0, 1, or 2 representing pre-flop, flop, or river respectively
                "my_cards": List[str] of your cards, e.g. ["1s", "2h"]
                "board_cards": List[str] of the cards on the board
                "my_pip": int, the number of chips you have contributed to the pot this round of betting
                "opp_pip": int, the number of chips your opponent has contributed to the pot this round of betting
                "my_stack": int, the number of chips you have remaining
                "opp_stack": int, the number of chips your opponent has remaining
                "my_bankroll": int, the number of chips you have won or lost from the beginning of the game to the start of this round
                "min_raise": int, the smallest number of chips for a legal bet/raise
                "max_raise": int, the largest number of chips for a legal bet/raise
            }

        Returns:
            Action: The action you want to take.
        """
        # raise NotImplementedError('get_action')
        # Example simple strategy:
        if CallAction in observation["legal_actions"]:
            return CallAction()
        elif CheckAction in observation["legal_actions"]:
            return CheckAction()
        else:
            return FoldAction()
