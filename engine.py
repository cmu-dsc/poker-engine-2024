'''
CMU Data Science Club Poker Bot Competition Game Engine
'''

'''
Regular 6 player Texas hold 'em
'''

from collections import namedtuple

class RoundState():
    '''
    Encodes the game tree for one round of poker.
    '''
    
    def showdown(self) -> None:
        '''
        Compares the player's hands and computes payoffs.
        '''
    
    def legal_actions(self) -> None:
        '''
        Returns a set which corresponds to the active player's legal moves
        '''
        
    def raise_bounds(self) -> None:
        '''
        Returns a tuple of the minimum and maximum legal raises.
        '''
        
    def bid_bounds(self) -> None:
        '''
        Returns a tuple of the minimum and maximum legal bid amounts
        '''
        
    def proceed_street(self) -> None:
        '''
        Resets the players' pips and advances the game tree to the next round of betting.
        '''
        
    def proceed(self, action) -> None:
        '''
        Advances the game tree by one action performed by the active player.
        '''
    
class Player():
    '''
    Handles subprocess and socket interactions with one player's pokerbot.
    '''
    
    def __init__(self) -> None:
        pass
    
    def build(self) -> None:
        '''
        Loads the commands file and builds the pokerbot.
        '''
        
    def run(self) -> None:
        '''
        Runs the pokerbot and establishes the socket connection.
        '''
        
    def stop(self) -> None:
        '''
        Closes the socket connection and stops the pokerbot.
        '''

    def query(self, round_state, player_message, game_log) -> None:
        '''
        Requests one action from the pokerbot over the socket connection.
        At the end of the round, we request a CheckAction from the pokerbot.
        '''
    
class Game():
    '''
    Manages logging and the high-level game procedure.
    '''
    
    def __init__(self) -> None:
        pass
    
    def log_round_state(self, players, round_state) -> None:
        '''
        Incorporates RoundState information into the game log and player messages.
        '''
        
    def log_action(self, name, action, bet_override) -> None:
        '''
        Incorporates action information into the game log and player messages.
        '''
    
    def log_terminal_state(self, players, round_state) -> None:
        '''
        Incorporates TerminalState information into the game log and player messages.
        '''
    
    def run_round(self, players):
        '''
        Runs one round of poker (1 hand).
        '''
    
    def run(self):
        '''
        Runs one game of poker.
        '''
        
if __name__ == '__main__':
    Game().run()