"""
CMU Poker Bot Competition Game Engine 2024
"""

import grpc
from collections import namedtuple, deque
from typing import Deque, List, Optional, Set, Type, Union

from shared.pokerbot_pb2_grpc import PokerBotStub
from shared.pokerbot_pb2 import (
    ReadyCheckRequest,
    ActionRequest,
    EndRoundMessage,
    ActionType,
    Action as ProtoAction,
)
from evaluate import evaluate, ShortDeck
from config import *

FoldAction = namedtuple("FoldAction", [])
CallAction = namedtuple("CallAction", [])
CheckAction = namedtuple("CheckAction", [])
# we coalesce BetAction and RaiseAction for convenience
RaiseAction = namedtuple("RaiseAction", ["amount"])
Action = Union[FoldAction, CallAction, CheckAction, RaiseAction]
TerminalState = namedtuple("TerminalState", ["deltas", "previous_state"])

CCARDS = lambda cards: ",".join(map(str, cards))
PCARDS = lambda cards: "[{}]".format(" ".join(map(str, cards)))
PVALUE = lambda name, value: ", {} ({})".format(name, value)
STATUS = lambda players: "".join([PVALUE(p.name, p.bankroll) for p in players])


class RoundState(
    namedtuple(
        "_RoundState",
        [
            "button",
            "street",
            "pips",
            "stacks",
            "hands",
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
        score0 = evaluate(self.hands[0])
        score1 = evaluate(self.hands[1])
        if score0 > score1:
            delta = STARTING_STACK - self.stacks[1]
        elif score0 < score1:
            delta = self.stacks[0] - STARTING_STACK
        else:  # split the pot
            delta = (self.stacks[0] - self.stacks[1]) // 2
        return TerminalState([delta, -delta], self.bids, self)

    def legal_actions(self) -> Set[Type]:
        """
        Returns a set which corresponds to the active player's legal moves.
        """
        active = self.button % 2
        continue_cost = self.pips[1 - active] - self.pips[active]

        if continue_cost == 0:  # No additional chips required to stay in the hand
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

    def raise_bounds(self) -> (int, int):
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
        if self.street >= 2:  # After river, proceed to showdown
            return self.showdown()

        # Dealing the next card (flop or river) and advancing the street
        new_street = self.street + 1
        new_hands = self.hands
        if new_street in [1, 2]:  # Dealing a card for flop and river
            for i in range(len(new_hands)):
                new_hands[i].append(self.deck.deal(1))

        return RoundState(
            button=1 - self.button,  # Switching the dealer button
            street=new_street,
            pips=[0, 0],  # Resetting the current round's bet amounts
            stacks=self.stacks,
            hands=new_hands,
            deck=self.deck,
            previous_state=self,
        )

    def proceed(self, action: Action) -> "RoundState":
        """
        Advances the game tree by one action performed by the active player.
        """
        active = self.button % 2
        if isinstance(action, FoldAction):
            # Determine the amount lost by the folding player
            # If this is preflop, the SB loses their blind, and BB wins the SB amount
            if self.street == 0:  # Preflop
                sb_index = (
                    self.button % 2
                )  # SB is the player with the button in heads-up
                bb_index = 1 - sb_index
                delta = SMALL_BLIND if active == sb_index else BIG_BLIND
                deltas = [-delta if i == active else delta for i in range(2)]
            else:
                # Postflop, the pot could contain more than just the blinds
                delta = self.stacks[1 - active] - STARTING_STACK
                deltas = [delta, -delta] if active == 0 else [-delta, delta]
            return TerminalState(deltas, self)

        new_pips = list(self.pips)
        new_stacks = list(self.stacks)

        if isinstance(action, CallAction):
            # Player matches the current highest bet
            contribution = new_pips[1 - active] - new_pips[active]
            new_stacks[active] -= contribution
            new_pips[active] += contribution

        elif isinstance(action, CheckAction):
            # Player chooses not to bet further
            pass  # No change in pips or stacks

        elif isinstance(action, RaiseAction):
            # Player raises the bet
            contribution = action.amount - new_pips[active]
            new_stacks[active] -= contribution
            new_pips[active] += contribution

        # Check if both players have acted and the betting is equal
        if new_pips[0] == new_pips[1]:
            if self.street == 2:  # After river, proceed to showdown
                return self.showdown()
            else:
                # Proceed to the next street
                return self.proceed_street()

        # Update the game state and return
        return RoundState(
            button=1 - self.button,
            street=self.street,
            pips=new_pips,
            stacks=new_stacks,
            hands=self.hands,
            deck=self.deck,
            previous_state=self,
        )


class Player:
    """
    Handles interactions with one player's pokerbot within the Kubernetes cluster.
    """

    def __init__(
        self, name: str, service_dns_name: str, auth_token: Optional[str] = None
    ) -> None:
        """
        Initializes a new Player instance.

        Args:
            name (str): The name of the player.
            service_dns_name (str): The DNS name of the service for gRPC communication.
            auth_token (Optional[str]): An optional authentication token for secure communication.
        """
        self.name: str = name
        self.service_dns_name: str = service_dns_name
        self.auth_token: Optional[str] = auth_token
        self.game_clock: float = STARTING_GAME_CLOCK
        self.bankroll: int = 0

        self.channel = grpc.insecure_channel(self.service_dns_name)
        self.stub = PokerBotStub(self.channel)

    def check_ready(self, player_names: List[str]) -> bool:
        """
        Checks if the pokerbot is ready to start or continue the game.

        Args:
            player_names (List[str]): A list of player names participating in the game.

        Returns:
            bool: True if the bot is ready, False otherwise.
        """
        timeout: float = 5.0
        request = ReadyCheckRequest(player_names=player_names)

        try:
            response = self.stub.ReadyCheck(request, timeout=timeout)
            return response.ready
        except grpc.RpcError as e:
            print(f"An error occurred: {e}")
            return False

    def request_action(
        self, player_hand: List[str], board_cards: List[str], new_actions: Deque[Action]
    ) -> Optional[Action]:
        """
        Requests an action from the pokerbot based on the current game state.

        Args:
            player_hand (List[str]): The cards currently held by the player.
            board_cards (List[str]): The cards visible on the board.
            new_actions (Deque[Action]): A deque of actions taken since the last request.

        Returns:
            Optional[Action]: The action decided by the pokerbot, or None if an error occurred.
        """
        timeout: float = 5.0
        proto_actions = self._convert_actions_to_proto(new_actions)

        request = ActionRequest(
            game_clock=self.game_clock,
            player_hand=player_hand,
            board_cards=board_cards,
            new_actions=proto_actions,
        )

        try:
            response = self.stub.RequestAction(request, timeout=timeout)
            return self._convert_proto_to_action(response.action)
        except grpc.RpcError as e:
            print(f"An error occurred: {e}")
            return None

    def end_round(
        self, opponent_hands: List[str], new_actions: Deque[Action], is_match_over: bool
    ) -> None:
        """
        Signals the end of a round to the pokerbot, including the final state of the game.

        Args:
            opponent_hands (List[str]): The final hands of the opponents.
            new_actions (Deque[Action]): Any actions that occurred after the last action request.
            is_match_over (bool): Indicates whether the match has concluded.
        """
        timeout: float = 5.0
        proto_actions = self._convert_actions_to_proto(new_actions)

        end_round_message = EndRoundMessage(
            opponent_hand=opponent_hands,
            new_actions=proto_actions,
            is_match_over=is_match_over,
        )

        try:
            self.stub.EndRound(end_round_message, timeout=timeout)
        except grpc.RpcError as e:
            print(f"An error occurred: {e}")

    def _convert_actions_to_proto(self, actions: Deque[Action]) -> List[ProtoAction]:
        """
        Converts a deque of Action objects to a list of protobuf Action messages.

        Args:
            actions (Deque[Action]): The actions to convert.

        Returns:
            List[ProtoAction]: The list of converted protobuf Action messages.
        """
        proto_actions = []
        for action in list(actions):
            proto_action = self._convert_action_to_proto(action)
            if proto_action:
                proto_actions.append(proto_action)
        return proto_actions

    def _convert_actions_to_proto(self, actions: Deque[Action]) -> List[ProtoAction]:
        """
        Converts and clears actions from a deque of Action objects to a list of protobuf Action messages.

        This method consumes the `actions` deque, ensuring that each action is only processed once
        and the deque is empty after conversion.

        Args:
            actions (Deque[Action]): The actions to convert and clear.

        Returns:
            List[ProtoAction]: The list of converted protobuf Action messages.
        """
        proto_actions = []
        while actions:
            action = actions.popleft()
            proto_action = self._convert_action_to_proto(action)
            if proto_action:
                proto_actions.append(proto_action)
        return proto_actions

    def _convert_proto_to_action(self, proto_action: ProtoAction) -> Optional[Action]:
        """
        Converts a protobuf Action message back to a Python-native Action object.

        Args:
            proto_action (ProtoAction): The protobuf Action message to convert.

        Returns:
            Optional[Action]: The converted Python-native Action object, or None if conversion is not possible.
        """
        if proto_action.action == ActionType.FOLD:
            return FoldAction()
        elif proto_action.action == ActionType.CALL:
            return CallAction()
        elif proto_action.action == ActionType.CHECK:
            return CheckAction()
        elif proto_action.action == ActionType.RAISE:
            return RaiseAction(amount=proto_action.amount)
        return None


class Game:
    """
    Manages logging and the high-level game procedure.
    """

    def __init__(self) -> None:
        self.players: List[Player] = []
        self.log: List[str] = [
            f"CMU Poker Bot Game - {PLAYER_1_NAME} vs {PLAYER_2_NAME}"
        ]
        self.new_actions: List[List[Action]] = [[], []]

    def log_round_state(self, round_state) -> None:
        """
        Logs the current state of the round.
        """
        # Implementation...

    def log_action(self, player_name: str, action, is_preflop: bool) -> None:
        """
        Logs an action taken by a player.
        """
        # Implementation...
        self.player_messages.append((player_name, action, is_preflop))

    def log_terminal_state(self, round_state) -> None:
        """
        Logs the terminal state of a round, including outcomes.
        """
        # Implementation...

    def run_round(self, last_round: bool) -> None:
        """
        Runs one round of poker (1 hand).
        """
        deck = ShortDeck()
        deck.shuffle()
        hands = [deck.deal(1), deck.deal(1)]
        board = []
        pips = [SMALL_BLIND, BIG_BLIND]
        stacks = [STARTING_STACK - SMALL_BLIND, STARTING_STACK - BIG_BLIND]

        round_state = RoundState(0, 0, pips, stacks, hands, deck, None)
        self.new_actions = [[], []]

        while not isinstance(round_state, TerminalState):
            self.log_round_state(RoundState)
            active = round_state.button % 2
            player = self.players[active]
            action = player.request_action(
                hands[active], board, self.new_actions[active]
            )
            # deal, bets for small blind, etc.
            # send start phase to bots
            # loop through players:
            # action request with previous players action if it exists
            # validate action, otherwise fold
            # add action to action_history
            # log action
            round_state = round_state.proceed()

        for player, delta in zip(self.players, delta):
            player.end_round(last_round)
            player.bankroll += delta
        self.log_terminal_state(round_state)

        # After round ends, log actions
        for action in self.action_history:
            self.log.append(f"Action taken: {action}")

    def run_match(self) -> None:
        """
        Runs one game of poker.
        """
        print("Starting the Poker Game...")
        self.players = [
            Player(PLAYER_1_NAME, PLAYER_1_DNS),
            Player(PLAYER_2_NAME, PLAYER_2_DNS),
        ]

        if not all(player.check_ready() for player in self.players):
            print("One or more bots are not ready. Aborting the match.")
            return

        for round_num in range(1, NUM_ROUNDS + 1):
            self.log.append(f"\nRound #{round_num}")
            self.run_round(self.players, round_num == NUM_ROUNDS)
            self.players = self.players[::-1]  # Alternate the dealer

        self.finalize_log()

    def finalize_log(self) -> None:
        """
        Finalizes the game log, writing it to a file and uploading it.
        """
        log_filename = f"{GAME_LOG_FILENAME}.txt"
        log_index = 1
        while os.path.exists(log_filename):
            log_filename = f"{GAME_LOG_FILENAME}_{log_index}.txt"
            log_index += 1

        print(f"Writing {log_filename}")
        with open(log_filename, "w") as log_file:
            log_file.write("\n".join(self.log))

        # Placeholder for uploading log, adjust as necessary
        # upload_log_to_s3(log_filename)


if __name__ == "__main__":
    Game().run_match()
