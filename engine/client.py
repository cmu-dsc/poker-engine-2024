from collections import deque
import json
import grpc
import os
import sys
import time
from typing import Deque, List, Optional

from .actions import Action, CallAction, CheckAction, FoldAction, RaiseAction
from .config import (
    CONNECT_TIMEOUT,
    CONNECT_RETRIES,
    READY_CHECK_TIMEOUT,
    READY_CHECK_RETRIES,
    ACTION_REQUEST_TIMEOUT,
    ACTION_REQUEST_RETRIES,
    ENFORCE_GAME_CLOCK,
    STARTING_GAME_CLOCK,
    PLAYER_LOG_SIZE_LIMIT,
)

shared_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "shared"))
sys.path.append(shared_path)

from shared.pokerbot_pb2_grpc import PokerBotStub  # noqa: E402
from shared.pokerbot_pb2 import (  # noqa: E402
    ReadyCheckRequest,
    ActionRequest,
    EndRoundMessage,
    ActionType,
    Action as ProtoAction,
)


class Client:
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
        self.channel = None
        self.stub = None
        self.log = deque()
        self.log_size = 0

        self._connect_with_retries()

    def _connect_with_retries(self) -> None:
        """
        Establishes a connection to the gRPC server with retries.
        """
        retry_options = {
            "initial_backoff_ms": CONNECT_TIMEOUT * 1000,
            "max_backoff_ms": CONNECT_TIMEOUT * 1000,
            "max_attempts": CONNECT_RETRIES,
            "retry_codes": [grpc.StatusCode.UNAVAILABLE.value],
        }
        channel_options = [
            ("grpc.enable_retries", 1),
            ("grpc.max_receive_message_length", -1),
            ("grpc.max_send_message_length", -1),
            ("grpc.lb_policy_name", "round_robin"),
            ("grpc.service_config", json.dumps({"retryPolicy": retry_options})),
        ]
        self.channel = grpc.insecure_channel(
            self.service_dns_name, options=channel_options
        )
        self.stub = PokerBotStub(self.channel)

        try:
            grpc.channel_ready_future(self.channel).result()
            print(f"Connected to {self.service_dns_name}")
        except grpc.FutureTimeoutError:
            raise RuntimeError(
                f"Failed to connect to {self.service_dns_name} after {CONNECT_RETRIES} attempts"
            )

    def check_ready(self, player_names: List[str]) -> bool:
        """
        Sends a readiness check to the pokerbot to verify if it is ready to start or continue the game.

        Args:
            player_names (List[str]): A list of player names participating in the game.

        Returns:
            bool: True if the bot is ready, False otherwise.
        """
        retry_options = {
            "initial_backoff_ms": READY_CHECK_TIMEOUT * 1000,
            "max_backoff_ms": READY_CHECK_TIMEOUT * 1000,
            "max_attempts": READY_CHECK_RETRIES,
            "retry_codes": [grpc.StatusCode.UNAVAILABLE.value],
        }
        channel_options = [
            ("grpc.enable_retries", 1),
            ("grpc.max_receive_message_length", -1),
            ("grpc.max_send_message_length", -1),
            ("grpc.lb_policy_name", "round_robin"),
            ("grpc.service_config", json.dumps({"retryPolicy": retry_options})),
        ]
        with grpc.insecure_channel(
            self.service_dns_name, options=channel_options
        ) as channel:
            stub = PokerBotStub(channel)
            request = ReadyCheckRequest(player_names=player_names)
            try:
                response = stub.ReadyCheck(request)
                return response.ready
            except grpc.RpcError as e:
                print(f"Bot {self.name} is not ready: {e}")
                return False

    def request_action(
        self, player_hand: List[str], board_cards: List[str], new_actions: Deque[Action]
    ) -> Optional[Action]:
        """
        Requests an action from the pokerbot based on the current game state, including the player's hand,
        visible board cards, and new actions.

        Args:
            player_hand (List[str]): The cards currently held by the player.
            board_cards (List[str]): The cards visible on the board.
            new_actions (Deque[Action]): A deque of actions taken since the last request.

        Returns:
            Optional[Action]: The action decided by the pokerbot, or None if an error occurred.
        """
        retry_options = {
            "initial_backoff_ms": ACTION_REQUEST_TIMEOUT * 1000,
            "max_backoff_ms": ACTION_REQUEST_TIMEOUT * 1000,
            "max_attempts": ACTION_REQUEST_RETRIES,
            "retry_codes": [grpc.StatusCode.UNAVAILABLE.value],
        }
        channel_options = [
            ("grpc.enable_retries", 1),
            ("grpc.max_receive_message_length", -1),
            ("grpc.max_send_message_length", -1),
            ("grpc.lb_policy_name", "round_robin"),
            ("grpc.service_config", json.dumps({"retryPolicy": retry_options})),
        ]
        with grpc.insecure_channel(
            self.service_dns_name, options=channel_options
        ) as channel:
            stub = PokerBotStub(channel)
            proto_actions = self._convert_actions_to_proto(new_actions)

            request = ActionRequest(
                game_clock=self.game_clock,
                player_hand=player_hand,
                board_cards=board_cards,
                new_actions=proto_actions,
            )

            start_time = time.perf_counter()

            try:
                response = stub.RequestAction(request)
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
        player_hand: List[str],
        opponent_hand: List[str],
        board_cards: List[str],
        new_actions: Deque[Action],
        delta: int,
        is_match_over: bool,
    ) -> None:
        """
        Signals the end of a round to the pokerbot, including the final state of the game and whether the match is over.

        Args:
            player_hand (List[str]): The final hand of the player.
            opponent_hand (List[str]): The final hand of the opponent.
            board_cards (List[str]): The cards visible on the board.
            new_actions (Deque[Action]): Any actions that occurred after the last action request.
            delta (int): The change in the player's bankroll after the round.
            is_match_over (bool): Indicates whether the match has concluded.
        """
        proto_actions = self._convert_actions_to_proto(new_actions)

        end_round_message = EndRoundMessage(
            player_hand=player_hand,
            opponent_hand=opponent_hand,
            board_cards=board_cards,
            new_actions=proto_actions,
            delta=delta,
            is_match_over=is_match_over,
        )

        try:
            new_logs = self.stub.EndRound(end_round_message).logs
            for log_entry in new_logs:
                entry_bytes = log_entry.encode("utf-8")
                entry_size = len(entry_bytes)

                if self.log_size + entry_size <= PLAYER_LOG_SIZE_LIMIT:
                    self.log.append(log_entry)
                    self.log_size += entry_size
                else:
                    if self.log_size < PLAYER_LOG_SIZE_LIMIT:
                        self.log.append(
                            "Log size limit reached. No further entries will be added."
                        )
                        self.log_size = PLAYER_LOG_SIZE_LIMIT
                    break
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

    @staticmethod
    def _convert_proto_to_action(proto_action: ProtoAction) -> Optional[Action]:
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

    @staticmethod
    def _convert_action_to_proto(action: Action) -> Optional[ProtoAction]:
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
