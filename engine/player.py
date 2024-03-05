import time
from typing import Deque, List, Optional
import grpc

from .config import (
    CHECK_READY_TIMEOUT,
    END_ROUND_TIMEOUT,
    ENFORCE_GAME_CLOCK,
    REQUEST_ACTION_TIMEOUT,
    STARTING_GAME_CLOCK,
)
from .engine import Action, CallAction, CheckAction, FoldAction, RaiseAction
from ..shared.pokerbot_pb2_grpc import PokerBotStub
from ..shared.pokerbot_pb2 import (
    ReadyCheckRequest,
    ActionRequest,
    EndRoundMessage,
    ActionType,
    Action as ProtoAction,
)


class Player:
    """
    Handles interactions with one player's pokerbot within the Kubernetes cluster,
    facilitating the communication between the game engine and the pokerbot for action requests and round updates.
    """

    def __init__(
        self, name: str, service_dns_name: str, auth_token: Optional[str] = None
    ) -> None:
        """
        Initializes a new Player instance with necessary details for gRPC communication.

        Args:
            name (str): The name of the player.
            service_dns_name (str): The DNS name of the service for gRPC communication.
            auth_token (Optional[str]): An optional authentication token for secure communication.
        """
        self.name = name
        self.service_dns_name = service_dns_name
        self.auth_token = auth_token
        self.game_clock = STARTING_GAME_CLOCK
        self.bankroll = 0

        self.channel = grpc.insecure_channel(service_dns_name)
        self.stub = PokerBotStub(self.channel)

    def check_ready(self, player_names: List[str]) -> bool:
        """
        Sends a readiness check to the pokerbot to verify if it is ready to start or continue the game.

        Args:
            player_names (List[str]): A list of player names participating in the game.

        Returns:
            bool: True if the bot is ready, False otherwise.
        """
        request = ReadyCheckRequest(player_names=player_names)
        try:
            response = self.stub.ReadyCheck(request, timeout=CHECK_READY_TIMEOUT)
            return response.ready
        except grpc.RpcError as e:
            print(f"An error occurred: {e}")
            return False

    def request_action(
        self, player_hand: List[str], board_cards: List[str], new_actions: Deque[Action]
    ) -> Optional[Action]:
        """
        Requests an action from the pokerbot based on the current game state, including the player's hand, visible board cards, and new actions.

        Args:
            player_hand (List[str]): The cards currently held by the player.
            board_cards (List[str]): The cards visible on the board.
            new_actions (Deque[Action]): A deque of actions taken since the last request.

        Returns:
            Optional[Action]: The action decided by the pokerbot, or None if an error occurred.
        """
        start_time = time.perf_counter()

        proto_actions = self._convert_actions_to_proto(new_actions)

        request = ActionRequest(
            game_clock=self.game_clock,
            player_hand=player_hand,
            board_cards=board_cards,
            new_actions=proto_actions,
        )

        try:
            response = self.stub.RequestAction(request, timeout=REQUEST_ACTION_TIMEOUT)
            action = self._convert_proto_to_action(response.action)
        except grpc.RpcError as e:
            print(f"An error occurred: {e}")
            action = None

        end_time = time.perf_counter()
        duration = end_time - start_time

        if ENFORCE_GAME_CLOCK:
            self.game_clock -= duration
        if self.game_clock <= 0:
            raise TimeoutError("Game clock has run out")

        return action

    def end_round(
        self,
        opponent_hands: List[str],
        new_actions: Deque[Action],
        delta: int,
        is_match_over: bool,
    ) -> None:
        """
        Signals the end of a round to the pokerbot, including the final state of the game and whether the match is over.

        Args:
            opponent_hands (List[str]): The final hands of the opponents.
            new_actions (Deque[Action]): Any actions that occurred after the last action request.
            is_match_over (bool): Indicates whether the match has concluded.
        """
        proto_actions = self._convert_actions_to_proto(new_actions)

        end_round_message = EndRoundMessage(
            opponent_hand=opponent_hands,
            new_actions=proto_actions,
            delta=delta,
            is_match_over=is_match_over,
        )

        try:
            self.stub.EndRound(end_round_message, timeout=END_ROUND_TIMEOUT)
        except grpc.RpcError as e:
            print(f"An error occurred: {e}")

    def _convert_actions_to_proto(self, actions: Deque[Action]) -> List[ProtoAction]:
        """
        Converts a deque of Action objects to a list of protobuf Action messages, clearing the deque in the process.

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
        else:
            return None

    def _convert_action_to_proto(self, action: Action) -> Optional[ProtoAction]:
        """
        Converts a single Action object to its corresponding protobuf Action message.

        Args:
            action (Action): The action to convert.

        Returns:
            Optional[ProtoAction]: The converted protobuf Action message, or None if conversion is not applicable.
        """
        if isinstance(action, FoldAction):
            return ProtoAction(action=ActionType.FOLD)
        elif isinstance(action, CallAction):
            return ProtoAction(action=ActionType.CALL)
        elif isinstance(action, CheckAction):
            return ProtoAction(action=ActionType.CHECK)
        elif isinstance(action, RaiseAction):
            return ProtoAction(action=ActionType.RAISE, amount=action.amount)
        else:
            return None
