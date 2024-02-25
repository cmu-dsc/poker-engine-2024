"""
CMU Poker Bot Competition Game Engine 2024
"""

import grpc
from collections import namedtuple
from typing import List, Optional, Set, Type, Union

from pokerbot_pb2_grpc import PokerBotServiceStub
from pokerbot_pb2 import ReadyCheckRequest, ActionRequest, EndGameRequest, ActionType
from evaluate import evaluate, ShortDeck
from config import *

FoldAction = namedtuple("FoldAction", [])
CallAction = namedtuple("CallAction", [])
CheckAction = namedtuple("CheckAction", [])
# we coalesce BetAction and RaiseAction for convenience
RaiseAction = namedtuple("RaiseAction", ["amount"])
Action = Union[FoldAction, CallAction, CheckAction, RaiseAction]
TerminalState = namedtuple("TerminalState", ["deltas", "previous_state"])

DECODE = {"F": FoldAction, "C": CallAction, "K": CheckAction, "R": RaiseAction}

CCARDS = lambda cards: ",".join(map(str, cards))
PCARDS = lambda cards: "[{}]".format(" ".join(map(str, cards)))
PVALUE = lambda name, value: ", {} ({})".format(name, value)
STATUS = lambda players: "".join([PVALUE(p.name, p.bankroll) for p in players])

# Socket encoding scheme:
#
# T#.### - the player's game clock
# P# - the player's index
# H**,** - the player's hand in common format
# F - a fold action in the round history
# C - a call action in the round history
# K - a check action in the round history
# R### - a raise action in the round history
# B**,**,**,**,** - the board cards in common format
# O**,** - the opponent's hand in common format
# D### - the player's bankroll delta from the round
# Q - game over
#
# Clauses are separated by spaces.
# Messages end with '\n'.
# The engine expects a response of K at the end of the round as an ack,
# otherwise a response which encodes the player's action.
# Action history is sent once, including the player's actions.


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
                new_hands[i].append(self.deck.pop())

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
        self.name: str = name
        self.service_dns_name: str = service_dns_name
        self.auth_token: Optional[str] = auth_token
        self.game_clock: float = STARTING_GAME_CLOCK
        self.bankroll: int = 0

    def run(self) -> None:
        """
        Establishes a gRPC connection to the pokerbot and checks if it's ready.
        """
        # Assuming TLS/SSL is not required for internal communication
        channel = grpc.insecure_channel(self.service_dns_name)

        self.bot_stub = PokerBotServiceStub(channel)

        request = ReadyCheckRequest(player_name=self.name)

        try:
            response = self.bot_stub.CheckReady(request, timeout=10)
            print(f"Bot {self.name} is ready: {response.ready}")
        except grpc.RpcError as e:
            print(f"Failed to communicate with bot {self.name}: {e.status()}")

    def reset(self) -> None:
        """
        Notifies the bot that the game has ended and its state should be reset for a new game.
        """
        try:
            response = self.bot_stub.EndGame(
                EndGameRequest(player_name=self.name), timeout=5
            )
            print(f"Bot {self.name} reset successful: {response.ack}")
        except grpc.RpcError as e:
            print(f"Failed to reset bot {self.name}: {e.code()}")

    def query(self, round_state: RoundState, game_log: List[str]) -> Action:
        """
        Requests one action from the pokerbot over gRPC
        """
        request = ActionRequest(
            player_name=self.name,
            game_clock=round_state.game_clock,
            bankroll=self.bankroll,
        )

        try:
            response = self.bot_stub.RequestAction(request, timeout=10)

            if response.action == ActionType.FOLD:
                return FoldAction()
            elif response.action == ActionType.CALL:
                return CallAction()
            elif response.action == ActionType.CHECK:
                return CheckAction()
            elif response.action == ActionType.RAISE:
                min_raise, max_raise = round_state.raise_bounds()
                if min_raise <= response.amount <= max_raise:
                    return RaiseAction(response.amount)
                else:
                    # Handle illegal raise amount
                    return FoldAction()  # Or another default action
        except grpc.RpcError as e:
            error_message = f"Failed to query action from bot {self.name}: {e.code()}"
            game_log.append(error_message)
            print(error_message)
            return FoldAction()  # Default action on communication error


class Game:
    """
    Manages logging and the high-level game procedure.
    """

    def __init__(self) -> None:
        self.log = [f"CMU Poker Bot Game - {PLAYER_1_NAME} vs {PLAYER_2_NAME}"]
        self.player_messages = [[], []]
        self.preflop_bets = {PLAYER_1_NAME: 0, PLAYER_2_NAME: 0}
        self.flop_bets = {PLAYER_1_NAME: 0, PLAYER_2_NAME: 0}
        self.river_bets = {PLAYER_1_NAME: 0, PLAYER_2_NAME: 0}
        # EV bets tracking, if necessary

    def log_round_state(self, players: List[Player], round_state: RoundState) -> None:
        """
        Incorporates RoundState information into the game log and player messages.
        """
        if round_state.street == 0:  # Pre-flop
            self.log.append(f"{players[0].name} posts the blind of {SMALL_BLIND}")
            self.log.append(f"{players[1].name} posts the blind of {BIG_BLIND}")
            self.log.append(f"{players[0].name} dealt {PCARDS(round_state.hands[0])}")
            self.log.append(f"{players[1].name} dealt {PCARDS(round_state.hands[1])}")
            self.player_messages[0] = ["T0.", "P0", "H" + CCARDS(round_state.hands[0])]
            self.player_messages[1] = ["T0.", "P1", "H" + CCARDS(round_state.hands[1])]
        elif round_state.street == 1:  # Flop
            flop_card = round_state.deck.peek(1)
            self.log.append(f"Flop {PCARDS(flop_card)}")
            compressed_flop = "B" + CCARDS(flop_card)
            self.player_messages[0].append(compressed_flop)
            self.player_messages[1].append(compressed_flop)
        elif round_state.street == 2:  # River
            river_card = round_state.deck.peek(1)
            self.log.append(f"River {PCARDS(river_card)}")
            compressed_river = "B" + CCARDS(river_card)
            self.player_messages[0].append(compressed_river)
            self.player_messages[1].append(compressed_river)

        self.log.append(
            f"Bets: {self.preflop_bets[players[0].name]}, {self.preflop_bets[players[1].name]}"
        )
        self.log.append(f"Stacks: {round_state.stacks[0]}, {round_state.stacks[1]}")

    def log_action(self, name: str, action: Action, bet_override: bool) -> None:
        """
        Incorporates action information into the game log and player messages.
        """
        if isinstance(action, FoldAction):
            phrasing = " folds"
            code = "F"
        elif isinstance(action, CallAction):
            phrasing = " calls"
            code = "C"
        elif isinstance(action, CheckAction):
            phrasing = " checks"
            code = "K"
        elif isinstance(action, RaiseAction):
            phrasing = (" bets " if bet_override else " raises to ") + str(
                action.amount
            )
            code = "R" + str(action.amount)
        else:
            raise ValueError("Unrecognized action type")

        self.log.append(f"{name}{phrasing}")
        self.player_messages[0].append(code)
        self.player_messages[1].append(code)

    def log_terminal_state(
        self, players: List[Player], round_state: TerminalState
    ) -> None:
        """
        Incorporates TerminalState information into the game log and player messages.
        """
        previous_state = round_state.previous_state
        if previous_state is None:
            return
        if FoldAction not in previous_state.legal_actions():
            # If the round didn't end in a fold, log the hands shown
            self.log.append(
                f"{players[0].name} shows {PCARDS(previous_state.hands[0])}"
            )
            self.log.append(
                f"{players[1].name} shows {PCARDS(previous_state.hands[1])}"
            )
            self.player_messages[0].append("O" + CCARDS(previous_state.hands[1]))
            self.player_messages[1].append("O" + CCARDS(previous_state.hands[0]))

        # Log the deltas (amounts won or lost)
        self.log.append(f"{players[0].name} awarded {round_state.deltas[0]}")
        self.log.append(f"{players[1].name} awarded {round_state.deltas[1]}")

        # Append deltas to player messages
        self.player_messages[0].append("D" + str(round_state.deltas[0]))
        self.player_messages[1].append("D" + str(round_state.deltas[1]))

    def run_round(self, players: List[Player]) -> None:
        """
        Runs one round of poker (1 hand).
        """
        deck = ShortDeck()
        deck.shuffle()

        # Deal one card to each player
        hands = [deck.deal(1), deck.deal(1)]
        pips = [SMALL_BLIND, BIG_BLIND]
        stacks = [STARTING_STACK - SMALL_BLIND, STARTING_STACK - BIG_BLIND]

        round_state = RoundState(0, 0, pips, stacks, hands, deck, None)

        # Reset bet tracking
        self.preflop_bets = {players[0].name: SMALL_BLIND, players[1].name: BIG_BLIND}

        while not isinstance(round_state, TerminalState):
            self.log_round_state(players, round_state)
            active = round_state.button % 2
            player = players[active]
            action = player.query(round_state, self.player_messages[active], self.log)
            bet_override = round_state.pips == [0, 0]
            self.log_action(player.name, action, bet_override)
            round_state = round_state.proceed(action)

        self.log_terminal_state(players, round_state)

        # Update bankrolls after the round
        for player, delta in zip(players, round_state.deltas):
            player.bankroll += delta

    def run(self) -> None:
        """
        Runs one game of poker.
        """
        print("   _____ __  __ _    _   _____      _             ")
        print("  / ____|  \/  | |  | | |  __ \    | |            ")
        print(" | |    | \  / | |  | | | |__) |__ | | _____ _ __ ")
        print(" | |    | |\/| | |  | | |  ___/ _ \| |/ / _ \ '__|")
        print(" | |____| |  | | |__| | | |  | (_) |   <  __/ |   ")
        print("  \_____|_|  |_|\____/  |_|   \___/|_|\_\___|_|   ")
        print()
        print("Starting the Poker Game...")

        players = [
            Player(PLAYER_1_NAME, PLAYER_1_PATH),
            Player(PLAYER_2_NAME, PLAYER_2_PATH),
        ]
        for player in players:
            player.build()
            player.run()

        for round_num in range(1, NUM_ROUNDS + 1):
            self.log.append("")
            self.log.append("Round #" + str(round_num) + STATUS(players))
            self.run_round(players)
            players = players[::-1]  # Alternate the dealer

        self.log.append("")
        self.log.append("Final" + STATUS(players))
        for player in players:
            player.stop()

        # Write game log to a file
        log_filename = GAME_LOG_FILENAME + ".txt"
        print("Writing", log_filename)
        with open(log_filename, "w") as log_file:
            log_file.write("\n".join(self.log))


if __name__ == "__main__":
    Game().run()
