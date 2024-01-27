'''
This file contains the base class that you should implement for your pokerbot.
'''


class Bot():
    '''
    The base class for a pokerbot.
    '''

    def handle_new_round(self, game_state, round_state, active):
        '''
        Called when a new round starts. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        raise NotImplementedError('handle_new_round')

    def handle_round_over(self, game_state, terminal_state, active):
        '''
        Called when a round ends. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        terminal_state: the TerminalState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        raise NotImplementedError('handle_round_over')

    def get_action(self, game_state, round_state, active):
        '''
        Where the magic happens - your code should implement this function.
        Called any time the engine needs an action from your bot.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Your action.
        '''
        # raise NotImplementedError('get_action')
        print(round_state)
        if round_state.auction:
            return BidAction(2)
        elif CallAction in round_state.legal_actions():
            return CallAction()
        elif CheckAction in round_state.legal_actions():
            return CheckAction()
        else:
            return FoldAction()