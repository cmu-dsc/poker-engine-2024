"""
Simple example pokerbot, written in Python.
"""
import itertools
import random
import sys

from skeleton.actions import Action, CallAction, CheckAction, FoldAction, RaiseAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot
from skeleton.evaluate import evaluate

class Player(Bot):
    """
    A pokerbot.
    """

    def __init__(self) -> None:
        """
        Called when a new game starts. Called exactly once.

        Arguments:
        Nothing.

        Returns:
        Nothing.
        """
        self.log = []
        pass

    def handle_new_round(self, game_state: GameState, round_state: RoundState, active: int) -> None:
        """
        Called when a new round starts. Called NUM_ROUNDS times.
        
        Args:
            game_state (GameState): The state of the game.
            round_state (RoundState): The state of the round.
            active (int): Your player's index.

        Returns:
            None
        """
        #my_bankroll = game_state.bankroll # the total number of chips you've gained or lost from the beginning of the game to the start of this round
        #game_clock = game_state.game_clock # the total number of seconds your bot has left to play this game
        #round_num = game_state.round_num # the round number from 1 to NUM_ROUNDS
        #my_cards = round_state.hands[active] # your cards
        #big_blind = bool(active) # True if you are the big blind
        self.log.append("new round")
        pass

    def handle_round_over(self, game_state: GameState, terminal_state: TerminalState, active: int, is_match_over: bool) -> None:
        """
        Called when a round ends. Called NUM_ROUNDS times.

        Args:
            game_state (GameState): The state of the game.
            terminal_state (TerminalState): The state of the round when it ended.
            active (int): Your player's index.

        Returns:
            None
        """
        #my_delta = terminal_state.deltas[active] # your bankroll change from this round
        #previous_state = terminal_state.previous_state # RoundState before payoffs
        #street = previous_state.street # 0, 3, 4, or 5 representing when this round ended
        #my_cards = previous_state.hands[active] # your cards
        #opp_cards = previous_state.hands[1-active] # opponent's cards or [] if not revealed
        self.log.append("game over")
        
        if is_match_over:
            with open("logs/bot_log.txt", "w") as log_file:
                log_file.write("\n".join(self.log))
            # sys.exit(0) # why doesn't this shut the container down?
        pass

    def get_action(self, game_state: GameState, round_state: RoundState, active: int) -> Action:
        """
        Where the magic happens - your code should implement this function.
        Called any time the engine needs an action from your bot.

        Args:
            game_state (GameState): The state of the game.
            round_state (RoundState): The state of the round.
            active (int): Your player's index.

        Returns:
            Action: The action you want to take.
        """
        legal_actions = round_state.legal_actions() # the actions you are allowed to take
        street = round_state.street # 0, 1, or 2 representing pre-flop, flop, or river respectively
        my_cards = list(round_state.hands[active]) # your cards
        board_cards = list(round_state.board) # the board cards
        my_pip = round_state.pips[active] # the number of chips you have contributed to the pot this round of betting
        opp_pip = round_state.pips[1 - active] # the number of chips your opponent has contributed to the pot this round of betting
        my_stack = round_state.stacks[active] # the number of chips you have remaining
        opp_stack = round_state.stacks[1 - active] # the number of chips your opponent has remaining
        continue_cost = opp_pip - my_pip # the number of chips needed to stay in the pot
        my_contribution = STARTING_STACK - my_stack # the number of chips you have contributed to the pot
        opp_contribution = STARTING_STACK - opp_stack # the number of chips your opponent has contributed to the pot

        # self.log.append("My cards: " + str(my_cards))
        # self.log.append("Board cards: " + str(board_cards))

        # leftover_cards = [f"{rank}{suit}" for rank in "123456" for suit in "shd" if f"{rank}{suit}" not in my_cards + board_cards]
        # possible_card_comb = list(itertools.permutations(leftover_cards, 3 - len(board_cards)))
        # possible_card_comb = [board_cards + list(c) for c in possible_card_comb]

        # result = map(lambda x: evaluate([x[0], x[1]], my_cards) > evaluate([x[0], x[1]], [x[2]]), possible_card_comb)
        # prob = sum(result) / len(possible_card_comb)

        # if prob > 0.5 and RaiseAction in legal_actions:
        #     min_raise, max_raise = round_state.raise_bounds() # the smallest and largest numbers of chips for a legal bet/raise
        #     min_cost = min_raise - my_pip # the cost of a minimum bet/raise
        #     max_cost = max_raise - my_pip # the cost of a maximum bet/raise
        #     raise_amount = random.randint(min_raise, max_raise)
        #     action = RaiseAction(raise_amount)
        # elif prob < 0.1 and FoldAction in legal_actions:
        #     action = FoldAction()

        # Always check/call
        if CheckAction in legal_actions:
            action = CheckAction()
        else:
            action = CallAction()
        self.log.append(str(action))
        return action

if __name__ == '__main__':
    run_bot(Player(), parse_args())