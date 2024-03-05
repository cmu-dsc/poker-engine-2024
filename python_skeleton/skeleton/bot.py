"""
This file contains the base class that you should implement for your pokerbot.
"""

from .actions import Action, FoldAction, CallAction, CheckAction, RaiseAction
from .states import GameState, RoundState, TerminalState


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
        self, game_state: GameState, terminal_state: TerminalState, active: int
    ) -> None:
        """
        Called when a round ends. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        terminal_state: the TerminalState object.
        active: your player's index.

        Returns:
        Nothing.
        """
        raise NotImplementedError("handle_round_over")

    def get_action(
        self, game_state: GameState, round_state: RoundState, active: int
    ) -> Action:
        """
        Where the magic happens - your code should implement this function.
        Called any time the engine needs an action from your bot.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Your action.
        """
        # raise NotImplementedError('get_action')
        # Example simple strategy:
        legal_actions = round_state.legal_actions()
        if CallAction in legal_actions:
            return CallAction()
        elif CheckAction in legal_actions:
            return CheckAction()
        else:
            return FoldAction()
