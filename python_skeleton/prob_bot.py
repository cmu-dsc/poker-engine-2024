"""
Simple example pokerbot, written in Python.
"""

import itertools
import pickle
from typing import Optional

from skeleton.actions import Action, CallAction, CheckAction, FoldAction, RaiseAction
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

        Arguments:
        Nothing.

        Returns:
        Nothing.
        """
        self.log = []
        self.pre_computed_probs = pickle.load(open("python_skeleton/skeleton/pre_computed_probs.pkl", "rb")) 
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
        self.log = []
        self.log.append("================================")
        self.log.append("new round")
        pass

    def handle_round_over(self, game_state: GameState, terminal_state: TerminalState, active: int, is_match_over: bool) -> Optional[str]:
        """
        Called when a round ends. Called NUM_ROUNDS times.

        Args:
            game_state (GameState): The state of the game.
            terminal_state (TerminalState): The state of the round when it ended.
            active (int): Your player's index.

        Returns:
            Your logs.
        """
        #my_delta = terminal_state.deltas[active] # your bankroll change from this round
        #previous_state = terminal_state.previous_state # RoundState before payoffs
        #street = previous_state.street # 0, 3, 4, or 5 representing when this round ended
        #my_cards = previous_state.hands[active] # your cards
        #opp_cards = previous_state.hands[1-active] # opponent's cards or [] if not revealed
        self.log.append("game over")
        self.log.append("================================\n")

        return self.log

    def get_action(self, observation: dict) -> Action:
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
        my_contribution = STARTING_STACK - observation["my_stack"] # the number of chips you have contributed to the pot
        opp_contribution = STARTING_STACK - observation["opp_stack"] # the number of chips your opponent has contributed to the pot
        continue_cost = observation["opp_pip"] - observation["my_pip"] # the number of chips needed to stay in the pot

        self.log.append("My cards: " + str(observation["my_cards"]))
        self.log.append("Board cards: " + str(observation["board_cards"]))
        self.log.append("My stack: " + str(observation["my_stack"]))
        self.log.append("My contribution: " + str(my_contribution))
        self.log.append("My bankroll: " + str(observation["my_bankroll"]))

        # Original probability calculation
        # leftover_cards = [f"{rank}{suit}" for rank in "123456789" for suit in "shd" if f"{rank}{suit}" not in my_cards + board_cards]
        # possible_card_comb = list(itertools.permutations(leftover_cards, 4 - len(board_cards)))
        # possible_card_comb = [board_cards + list(c) for c in possible_card_comb]
        # result = map(lambda x: self.pre_computed_evals['_'.join(sorted(my_cards+x[:2]))] > self.pre_computed_evals['_'.join(sorted(x))], possible_card_comb)
        # prob = sum(result) / len(possible_card_comb)

        # Use pre-computed probability calculation
        prob = self.pre_computed_probs['_'.join(sorted(observation["my_cards"])) + '_' + '_'.join(sorted(observation["board_cards"]))]

        expected_gain = prob * max(my_contribution, opp_contribution) - (1 - prob) * max(my_contribution, opp_contribution)

        self.log.append(f"Winning probability: {prob}")
        self.log.append(f"Expected gain: {expected_gain}")

        if continue_cost > 1:
            prob = prob * 0.8
            self.log.append(f"Adjusted Winning probability: {prob}")

        if prob > 0.7 and RaiseAction in observation["legal_actions"]:
            min_cost = observation["min_raise"] - observation["my_pip"] # the cost of a minimum bet/raise
            max_cost = observation["max_raise"] - observation["my_pip"] # the cost of a maximum bet/raise
            raise_amount = min(int(observation["min_raise"]*1.5), observation["max_raise"])
            action = RaiseAction(raise_amount)
        elif prob < 0.4 and continue_cost > 1 and FoldAction in observation["legal_actions"]:
            action = FoldAction()
        elif CheckAction in observation["legal_actions"]:
            action = CheckAction()
        else:
            action = CallAction()

        self.log.append(str(action) + "\n")
        return action

if __name__ == '__main__':
    run_bot(Player(), parse_args())