"""
CMU Poker Bot Competition Game Engine 2024
"""
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from collections import deque
from .actions import (
    Action,
    CallAction,
    CheckAction,
    FoldAction,
    RaiseAction,
    TerminalState,
)
from .config import (
    BIG_BLIND,
    NUM_ROUNDS,
    SMALL_BLIND,
    STARTING_STACK,
)
from .evaluate import ShortDeck
from .roundstate import RoundState

def card_to_int(card: str):
    rank, suit = card[0], card[1]
    suit = {"s": 0, "h": 1, "d": 2}[suit]
    return (suit * 10 + int(rank))

class PokerEnv(gym.Env):
    """
    Manages logging and the high-level game procedure.
    """
    def __init__(self, num_rounds, opp_bot=None) -> None:
        super().__init__()
        self.num_rounds = num_rounds

        # Action space is a Tuple (action, amount) where action is a Discrete(4) and amount is a Discrete(400,
        # 0: Fold, 1: Call, 2: Check, 3: Raise 
        self.action_space = spaces.Tuple([spaces.Discrete(4), spaces.Discrete(400, start=1)])

        # Observation space is a Dict. 
        # Since we have two players, is_my_turn is a Discrete(2)
        # Make sure to check is_my_turn before taking an action
        # opp_shown_card is "0" if the opp's card is not shown
        # Two players, so the observation space is a Tuple of two single_observation_spaces
        cards_space = spaces.Box(low=0, high=1, shape=(2,))
        self.observation_space_one_player = spaces.Dict({
            "is_my_turn": spaces.Discrete(2),
            "legal_actions": spaces.MultiBinary(4),
            "street": spaces.Discrete(3),
            "my_cards": cards_space,
            "board_cards": cards_space,
            "my_pip": spaces.Box(low=0, high=1, shape=(1,)), 
            "opp_pip": spaces.Box(low=0, high=1, shape=(1,)),
            "my_stack": spaces.Box(low=0, high=1, shape=(1,)),
            "opp_stack": spaces.Box(low=0, high=1, shape=(1,)),
            "my_bankroll": spaces.Box(low=-1, high=1, shape=(1,)), 
            "min_raise": spaces.Box(low=0, high=1, shape=(1,)),
            "max_raise": spaces.Box(low=0, high=1, shape=(1,)),
            "opp_shown_card": cards_space,
            "round_num": spaces.Discrete(NUM_ROUNDS)
        })

        # If opp_bot is not None, the observation space is a single_observation_space (one player mode)
        if opp_bot is None:
            self.game_mode = "two_player"
            self.observation_space = spaces.Tuple([self.observation_space_one_player, self.observation_space_one_player])
        else:
            self.game_mode = "single_player"
            self.observation_space = self.observation_space_one_player

        self.curr_round_state = None
        self.curr_round_num = 1
        self.player_last_actions = [None, None]
        self.opp_bot = opp_bot

    def _get_observation(self, player_num: int, opp_shown_card=None):
        """
        Returns the observation for the player_num player.
        """ 
        round_state = self.curr_round_state
        legal_actions = round_state.legal_actions()
        my_pip = round_state.pips[player_num]
        opp_pip = round_state.pips[1 - player_num]
        my_stack = round_state.stacks[player_num]
        opp_stack = round_state.stacks[1 - player_num]
        min_raise, max_raise = round_state.raise_bounds()
        my_bankroll = self.bankrolls[player_num]
        if opp_shown_card is not None:
            opp_shown_card = [card_to_int(card) for card in opp_shown_card]
        else:
            opp_shown_card = [0, 0]

        board_cards = [card_to_int(card) for card in round_state.board]
        padding = [0] * (2 - len(board_cards))
        board_cards += padding

        obs = {
            "is_my_turn": int(round_state.button % 2 == player_num),
            "legal_actions": np.array([int(action in legal_actions) for action in [FoldAction, CallAction, CheckAction, RaiseAction]]).astype(np.int8),
            "street": round_state.street,
            "my_cards": np.array([card_to_int(card) for card in round_state.hands[player_num]]),
            "board_cards": np.array(board_cards),
            "my_pip": np.array(my_pip).reshape(1,),
            "opp_pip": np.array(opp_pip).reshape(1,),
            "my_stack": np.array(my_stack).reshape(1,),
            "opp_stack": np.array(opp_stack).reshape(1,),
            "my_bankroll": np.array(my_bankroll).reshape(1,),
            "min_raise": np.array(min_raise).reshape(1,),
            "max_raise": np.array(max_raise).reshape(1,),
            "opp_shown_card": np.array(opp_shown_card),
            "round_num": self.curr_round_num
        }
        # assert self.observation_space_one_player.contains(obs)
        return obs

    def _end_round(self, round_state: TerminalState):
        """
        Ends the round, updating the bankrolls of the players.
        Returns the final observation
        """
        for index, delta in enumerate(round_state.deltas):
            self.bankrolls[index] += delta
        was_last_round = self.curr_round_num >= self.num_rounds
        self._reset_round()
        self.curr_round_num += 1

        opp_shown_cards = []
        for player_num in range(2):
            if self.player_last_actions[player_num] != FoldAction:
                opp_shown_cards.append(round_state.previous_state.hands[1 - player_num])

        return (self._get_observation(0, opp_shown_cards[0]), self._get_observation(1, opp_shown_cards[1])), tuple(round_state.deltas), was_last_round, False, {"mode": self.game_mode}

    def _step_without_opp(self, action):
        """
        Takes a step in the game, given the action taken by the active player.
        """
        active = self.curr_round_state.button % 2
        action_type, amount = action
        if action_type == 3:
            action = RaiseAction(amount)
        else:
            action = [FoldAction(), CallAction(), CheckAction()][action_type]
        action = self._validate_action(action, self.curr_round_state, active)
        self.player_last_actions[active] = action
        self.curr_round_state = self.curr_round_state.proceed(action)

        # If the round is over, return the final observation and reward    
        if isinstance(self.curr_round_state, TerminalState):
            return self._end_round(self.curr_round_state)
        
        return (self._get_observation(0), self._get_observation(1)), (0,0), False, False, {"mode": self.game_mode}

    def _step_with_opp(self, action):
        assert self.opp_bot is not None
        assert self.curr_round_state.button % 2 == 0
        (obs1, obs2), (reward1, _), done, trunc, info = self._step_without_opp(action)
        while obs2["is_my_turn"]:
            action2 = self.opp_bot(obs2)        
            (obs1, obs2), (reward1, _), done, trunc, info = self._step_without_opp(action2)  
        return obs1, reward1, done, trunc, info

    def step(self, action):
        assert self.curr_round_num <= self.num_rounds
        if self.game_mode == "two_player":
            return self._step_without_opp(action)
        elif self.game_mode == "single_player":
            return self._step_with_opp(action)

    def _reset_round(self):
        """
        Resets the round.
        """
        
        # Shuffle the deck and deal the hands
        pips = [SMALL_BLIND, BIG_BLIND]
        stacks = [STARTING_STACK - SMALL_BLIND, STARTING_STACK - BIG_BLIND]
        deck = ShortDeck()
        deck.shuffle()
        hands = [deck.deal(2), deck.deal(2)]

        self.curr_round_state = RoundState(0, 0, pips, stacks, hands, [], deck, None)
        self.new_actions = [deque(), deque()]  

        return (self._get_observation(0), self._get_observation(1))

    def reset(self, seed=None, options=None):
        """
        Resets the entire game.
        """
        self.bankrolls = [0, 0]
        self.curr_round_num = 1
        obs1, obs2 = self._reset_round()
        info = dict(mode=self.game_mode)
        if self.game_mode == "single_player":
            return obs1, info
        return (obs1, obs2), info

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
