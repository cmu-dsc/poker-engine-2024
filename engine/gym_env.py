"""
CMU Poker Bot Competition Game Engine 2024
"""
import gymnasium as gym
from gymnasium import spaces
from collections import deque
import os
from typing import Deque, List, SupportsFloat

from .actions import (
    STREET_NAMES,
    Action,
    CallAction,
    CheckAction,
    FoldAction,
    RaiseAction,
    TerminalState,
)
from .config import (
    BIG_BLIND,
    BOT_LOG_FILENAME,
    GAME_LOG_FILENAME,
    LOGS_DIRECTORY,
    NUM_ROUNDS,
    PLAYER_1_DNS,
    PLAYER_1_NAME,
    PLAYER_2_DNS,
    PLAYER_2_NAME,
    SMALL_BLIND,
    STARTING_STACK,
    upload_logs,
    add_match_entry,
)
from .evaluate import ShortDeck
from .client import Client
from .roundstate import RoundState


class PokerEnv(gym.Env):
    """
    Manages logging and the high-level game procedure.
    """
    def __init__(self, num_rounds, init_enemy=None) -> None:
        super().__init__()
        self.num_rounds = num_rounds

        # Action space is a Box with 4 dimensions, each representing an action
        # 0: Fold, 1: Call, 2: Check, 3: Raise
        which_action_space = spaces.Discrete(4)
        raise_amount_space = spaces.Box(low=0, high=400, shape=(), dtype=int)
        self.action_space = spaces.Tuple([which_action_space, raise_amount_space])

        # Observation space is a Dict. 
        # Since we have two players, is_my_turn is a Discrete(2)
        # Make sure to check is_my_turn before taking an action
        # enemy_shown_card is "XX" if the enemy's card is not shown
        # Two players, so the observation space is a Tuple of two single_observation_spaces
        card_space = spaces.Text(min_length=2, max_length=2)
        observation_space = spaces.Dict({
            "is_my_turn": spaces.Discrete(2),
            "legal_actions": spaces.MultiBinary(4),
            "street": spaces.Discrete(3),
            "my_cards": card_space,
            "board_cards": spaces.Tuple([card_space, card_space, card_space]),
            "my_pip": spaces.Box(low=0, high=400, shape=(), dtype=int),
            "opponent_pip": spaces.Box(low=0, high=400, shape=(), dtype=int),
            "my_stack": spaces.Box(low=0, high=400, shape=(), dtype=int),
            "opponent_stack": spaces.Box(low=0, high=400, shape=(), dtype=int),
            "my_bankroll": spaces.Box(low=-400*NUM_ROUNDS, high=400*NUM_ROUNDS, shape=(), dtype=int),
            "min_raise": spaces.Box(low=0, high=400, shape=(), dtype=int),
            "max_raise": spaces.Box(low=0, high=400, shape=(), dtype=int),
            "enemy_shown_card": card_space,
            "round_num": spaces.Discrete(NUM_ROUNDS),
        })
        self.observation_space = spaces.Tuple([observation_space, observation_space])

        self.curr_round_state = None
        self.curr_round_num = 1
        self.player_last_actions = [None, None]
        self.reset()

    def _get_observation(self, player_num: int, enemy_shown_card="XX"):
        """
        Returns the observation for the player_num player.
        """ 
        round_state = self.curr_round_state
        legal_actions = round_state.legal_actions()
        my_pip = round_state.pips[player_num]
        opponent_pip = round_state.pips[1 - player_num]
        my_stack = round_state.stacks[player_num]
        opponent_stack = round_state.stacks[1 - player_num]
        min_raise, max_raise = round_state.raise_bounds()
        my_bankroll = self.bankrolls[player_num]


        return {
            "is_my_turn": int(round_state.button % 2 == player_num),
            "legal_actions": [int(action in legal_actions) for action in [FoldAction, CallAction, CheckAction, RaiseAction]],
            "street": round_state.street,
            "my_cards": round_state.hands[player_num],
            "board_cards": tuple(round_state.board),
            "my_pip": my_pip,
            "opponent_pip": opponent_pip,
            "my_stack": my_stack,
            "opponent_stack": opponent_stack,
            "my_bankroll": my_bankroll,
            "min_raise": min_raise,
            "max_raise": max_raise,
            "enemy_shown_card": enemy_shown_card,
            "round_num": self.curr_round_num,
        }

    def _end_round(self, round_state: TerminalState):
        """
        Ends the round, updating the bankrolls of the players.
        Returns the final observation
        """
        for index, delta in enumerate(round_state.deltas):
            self.bankrolls[index] += delta
        was_last_round = self.curr_round_num == self.num_rounds
        self._reset_round()
        self.curr_round_num += 1

        enemy_shown_cards = []
        for player_num in range(2):
            if self.player_last_actions[player_num] != FoldAction:
                enemy_shown_cards.append(round_state.previous_state.hands[1 - player_num])

        return (self._get_observation(0, enemy_shown_cards[0]), self._get_observation(1, enemy_shown_cards[1])), tuple(round_state.deltas), was_last_round, False, None

    def step(self, action):
        """
        Takes a step in the game, given the action taken by the active player.
        """
        active = self.curr_round_state.button % 2
        action_type, amount = action
        if action_type == 3:
            action = RaiseAction(amount)
        elif action_type == 2:
            action = CheckAction()
        elif action_type == 1:
            action = CallAction()
        else:
            action = FoldAction()

        action = self._validate_action(action, self.curr_round_state, active)
        self.player_last_actions[active] = action
        self.curr_round_state = self.curr_round_state.proceed(action)

        # If the round is over, return the final observation and reward    
        if isinstance(self.curr_round_state, TerminalState):
            return self._end_round(self.curr_round_state)
        
        return (self._get_observation(0), self._get_observation(1)), (0,0), False, False, None

    def _reset_round(self):
        """
        Resets the round.
        """

        # Alternate the dealer
        # self.players = self.players[::-1]  

        # Shuffle the deck and deal the hands
        pips = [SMALL_BLIND, BIG_BLIND]
        stacks = [STARTING_STACK - SMALL_BLIND, STARTING_STACK - BIG_BLIND]
        deck = ShortDeck()
        deck.shuffle()
        hands = [deck.deal(1), deck.deal(1)]

        self.curr_round_state = RoundState(0, 0, pips, stacks, hands, [], deck, None)
        self.new_actions = [deque(), deque()]  

        return (self._get_observation(0), self._get_observation(1))

    def reset(self, seed=None, options=None):
        """
        Resets the entire game.
        """
        self.bankrolls = [0, 0]
        obs = self._reset_round()
        return obs

    def _validate_action(
        self, action: Action, round_state: RoundState, player_name: str
    ) -> Action:
        """
        Validates an action taken by a player, ensuring it's legal given the current round state.
        If the action is illegal, defaults to a legal action (Check if possible, otherwise Fold).

        Args:
            action (Action): The action attempted by the player.
            round_state (RoundState): The current state of the round.
            player_name (str): The name of the player who took the action.

        Returns:
            Action: The validated (or corrected) action.
        """
        legal_actions = (
            round_state.legal_actions()
            if isinstance(round_state, RoundState)
            else {CheckAction}
        )
        if isinstance(action, RaiseAction):
            amount = int(action.amount)
            min_raise, max_raise = round_state.raise_bounds()
            if RaiseAction in legal_actions and min_raise <= amount <= max_raise:
                return action
            else:
                print(
                    f"Player {player_name} attempted illegal RaiseAction with amount {amount}"
                )
        elif type(action) in legal_actions:
            return action
        else:
            print(f"Player {player_name} attempted illegal {type(action).__name__}")

        return CheckAction() if CheckAction in legal_actions else FoldAction()
