"""
The infrastructure for interacting with the engine.
"""

import os
import sys


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(project_root)

from argparse import ArgumentParser
from concurrent import futures
import grpc
from google.protobuf.empty_pb2 import Empty
from shared.pokerbot_pb2 import (
    ReadyCheckRequest,
    ReadyCheckResponse,
    ActionRequest,
    ActionResponse,
    EndRoundMessage,
    ActionType,
    ActionResponse,
)
from shared.pokerbot_pb2 import Action as ProtoAction
from shared.pokerbot_pb2_grpc import PokerBotServicer, add_PokerBotServicer_to_server
from skeleton.actions import Action, FoldAction, CallAction, CheckAction, RaiseAction
from skeleton.states import (
    GameState,
    TerminalState,
    RoundState,
    STARTING_STACK,
    BIG_BLIND,
    SMALL_BLIND,
)
from skeleton.bot import Bot


class Runner(PokerBotServicer):
    """
    Interacts with the engine.
    """

    def __init__(self, pokerbot: Bot):
        """
        Initializes a new instance of the Runner class.

        Args:
            pokerbot (Bot): The pokerbot to use for decision making.
        """
        self.pokerbot: Bot = pokerbot
        self.game_state = GameState(0, 0.0, 1)
        self.round_state = None
        self.active = 0
        self.round_flag = True

    def ReadyCheck(
        self, request: ReadyCheckRequest, context: grpc.ServicerContext
    ) -> ReadyCheckResponse:
        """
        Performs a readiness check.

        Args:
            request (ReadyCheckRequest): The request containing player names.
            context (grpc.ServicerContext): The gRPC context.

        Returns:
            ReadyCheckResponse: The response indicating readiness.
        """
        return ReadyCheckResponse(ready=True)

    def RequestAction(
        self, request: ActionRequest, context: grpc.ServicerContext
    ) -> ActionResponse:
        """
        Requests an action from the pokerbot.

        Args:
            request (ActionRequest): The request containing game state information.
            context (grpc.ServicerContext): The gRPC context.

        Returns:
            ActionResponse: The response containing the chosen action.
        """
        self.game_state = GameState(
            self.game_state.bankroll,
            request.game_clock,
            self.game_state.round_num,
        )

        if self.round_flag:
            self.round_state = RoundState(
                button=0,
                street=0,
                pips=[0, 0],
                stacks=[STARTING_STACK - SMALL_BLIND, STARTING_STACK - BIG_BLIND],
                hands=[request.player_hand, []],
                board=request.board_cards,
                previous_state=None,
            )
            self.active = 0
            self.pokerbot.handle_new_round(
                self.game_state, self.round_state, self.active
            )
            self.round_flag = False
        else:
            assert isinstance(self.round_state, RoundState) # one of these asserts fails
            try:
                self.round_state = RoundState(
                    self.round_state.button,
                    self.round_state.street,
                    self.round_state.pips,
                    self.round_state.stacks,
                    self.round_state.hands,
                    request.board_cards,
                    self.round_state.previous_state
                )
            except Exception as e:
                print("Error setting board cards", e)
            for proto_action in request.new_actions:
                action = self._convert_proto_action(proto_action)
                self.round_state = self.round_state.proceed(action)

        action = self.pokerbot.get_action(
            self.game_state, self.round_state, self.active
        )

        return self._convert_action_to_response(action)

    def EndRound(self, request: EndRoundMessage, context: grpc.ServicerContext) -> None:
        """
        Handles the end of a round.

        Args:
            request (EndRoundMessage): The request containing round results.
            context (grpc.ServicerContext): The gRPC context.
        """
        assert isinstance(self.round_state, RoundState) # this one
        opponent_hand = request.opponent_hand
        hands = list(self.round_state.hands)
        hands[1 - self.active] = opponent_hand
        self.round_state = RoundState(
            button=self.round_state.button,
            street=self.round_state.street,
            pips=self.round_state.pips,
            stacks=self.round_state.stacks,
            hands=hands,
            board=self.round_state.board,
            previous_state=self.round_state.previous_state,
        )

        for proto_action in request.new_actions:
            action = self._convert_proto_action(proto_action)
            self.round_state = self.round_state.proceed(action)

        deltas = [0, 0]
        deltas[self.active] = request.delta
        deltas[1 - self.active] = -request.delta
        self.round_state = TerminalState(deltas, self.round_state.previous_state)

        self.pokerbot.handle_round_over(self.game_state, self.round_state, self.active)

        self.game_state = GameState(
            bankroll=self.game_state.bankroll + request.delta,
            game_clock=self.game_state.game_clock,
            round_num=self.game_state.round_num + 1,
        )

        self.round_flag = True
        
        # if request.is_match_over:
        #     # do something
        
        return Empty()

    def _convert_action_to_response(self, action: Action) -> ActionResponse:
        """
        Converts an Action object to its corresponding ActionResponse.

        Args:
            action (Action): The action to convert.

        Returns:
            ActionResponse: The converted ActionResponse.
        """
        try:
            if isinstance(action, FoldAction):
                return ActionResponse(action=ProtoAction(action=ActionType.FOLD))
            elif isinstance(action, CallAction):
                return ActionResponse(action=ProtoAction(action=ActionType.CALL))
            elif isinstance(action, CheckAction):
                return ActionResponse(action=ProtoAction(action=ActionType.CHECK))
            elif isinstance(action, RaiseAction):
                return ActionResponse(
                    action=ProtoAction(action=ActionType.RAISE, amount=action.amount)
                )
        except Exception as e:
            print("Error converting action to response:", e)

    def _convert_proto_action(self, proto_action) -> Action:
        """
        Converts a proto action to its corresponding Action object.

        Args:
            proto_action: The proto action to convert.

        Returns:
            Action: The converted Action object.
        """
        if proto_action.action == ActionType.FOLD:
            return FoldAction()
        elif proto_action.action == ActionType.CALL:
            return CallAction()
        elif proto_action.action == ActionType.CHECK:
            return CheckAction()
        elif proto_action.action == ActionType.RAISE:
            return RaiseAction(proto_action.amount)


def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--port", type=int, default=50051, help="Port to listen on")
    return parser.parse_args()


def run_bot(pokerbot, args):
    """
    Starts the gRPC server and runs the pokerbot.
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    add_PokerBotServicer_to_server(Runner(pokerbot), server)
    server.add_insecure_port(f"[::]:{args.port}")
    server.start()
    print(f"Pokerbot server started on port {args.port}")
    server.wait_for_termination()


if __name__ == "__main__":
    run_bot()
