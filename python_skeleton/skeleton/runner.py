"""
The infrastructure for interacting with the engine.
"""

from concurrent import futures
import grpc
from ...shared.pokerbot_pb2 import (
    ReadyCheckRequest,
    ReadyCheckResponse,
    ActionRequest,
    ActionResponse,
    EndRoundMessage,
)
from ...shared.pokerbot_pb2_grpc import PokerBotServicer, add_PokerBotServicer_to_server
from .actions import Action, FoldAction, CallAction, CheckAction, RaiseAction
from .states import GameState, TerminalState, RoundState
from .states import STARTING_STACK, BIG_BLIND, SMALL_BLIND
from .bot import Bot


class Runner(PokerBotServicer):
    """
    Interacts with the engine.
    """

    def __init__(self, pokerbot: Bot):
        self.pokerbot: Bot = pokerbot

    def ReadyCheck(
        self, request: ReadyCheckRequest, context: grpc.ServicerContext
    ) -> ReadyCheckResponse:
        return ReadyCheckResponse(ready=True)

    def RequestAction(
        self, request: ActionRequest, context: grpc.ServicerContext
    ) -> ActionResponse:
        return super().RequestAction(request, context)

    def EndRound(self, request: EndRoundMessage, context: grpc.ServicerContext) -> None:
        return super().EndRound(request, context)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_PokerBotServicer_to_server(Runner(Bot()), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
