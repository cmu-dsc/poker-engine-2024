"""
CMU Poker Bot Competition Game Engine 2024
"""

from collections import deque
import os
from typing import Deque, List
import csv

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


class Game:
    """
    Manages logging and the high-level game procedure.
    """

    def __init__(self) -> None:
        self.players: List[Client] = []
        self.log: List[str] = [
            f"CMU Poker Bot Game - {PLAYER_1_NAME} vs {PLAYER_2_NAME}"
        ]
        self.csvlog: List[str] = [
            [
                "Round",
                "Street",
                "Team",
                "Action",
                "ActionAmt",
                "Team1Cards",
                "Team2Cards",
                "AllCards",
                "Bankroll",
            ]
        ]
        self.new_actions: List[Deque[Action]] = [deque(), deque()]
        self.round_num = 0

    def log_round_state(self, round_state: RoundState):
        """
        Logs the current state of the round.
        """

        if round_state.street == 0 and round_state.button == 0:
            self.log.append(f"{self.players[0].name} posts the blind of {SMALL_BLIND}")
            self.log.append(f"{self.players[1].name} posts the blind of {BIG_BLIND}")
            self.log.append(f"{self.players[0].name} dealt {round_state.hands[0]}")
            self.log.append(f"{self.players[1].name} dealt {round_state.hands[1]}")

            self._create_csv_row(round_state, self.players[0].name, "posts blind", SMALL_BLIND)
            self._create_csv_row(round_state, self.players[1].name, "posts blind", BIG_BLIND)

        elif round_state.street > 0 and round_state.button == 1:
            # log the pot every street
            pot = STARTING_STACK - round_state.stacks[0] + STARTING_STACK - round_state.stacks[1]
            self.log.append(f"{STREET_NAMES[round_state.street]} Board: {round_state.board} Pot: {pot}")

    def log_action(
        self, player_name: str, action: Action, round_state: RoundState
    ) -> None:
        """
        Logs an action taken by a player.
        """
        if isinstance(action, FoldAction):
            self.log.append(f"{player_name} folds")
            self._create_csv_row(round_state, player_name, "fold", None)
        elif isinstance(action, CallAction):
            self.log.append(f"{player_name} calls")
            self._create_csv_row(round_state, player_name, "call", None)
        elif isinstance(action, CheckAction):
            self.log.append(f"{player_name} checks")
            self._create_csv_row(round_state, player_name, "check", None)
        else:  # isinstance(action, RaiseAction)
            self.log.append(f"{player_name} bets {str(action.amount)}")
            self._create_csv_row(round_state, player_name, "bets", action.amount)

    def log_terminal_state(self, round_state: TerminalState) -> None:
        """
        Logs the terminal state of a round, including outcomes.
        """
        previous_state = round_state.previous_state
        if FoldAction not in previous_state.legal_actions():  # idk why this is needed
            self.log.append(f"{self.players[0].name} shows {previous_state.hands[0]}")
            self.log.append(f"{self.players[1].name} shows {previous_state.hands[1]}")
        self.log.append(f"{self.players[0].name} awarded {round_state.deltas[0]}")
        self.log.append(f"{self.players[1].name} awarded {round_state.deltas[1]}")
        self.log.append(f"{self.players[0].name} Bankroll: {self.players[0].bankroll}")
        self.log.append(f"{self.players[1].name} Bankroll: {self.players[1].bankroll}")

    def run_round(self, last_round: bool) -> None:
        """
        Runs one round of poker (1 hand).
        """
        pips = [SMALL_BLIND, BIG_BLIND]
        stacks = [STARTING_STACK - SMALL_BLIND, STARTING_STACK - BIG_BLIND]
        deck = ShortDeck()
        deck.shuffle()
        hands = [deck.deal(2), deck.deal(2)]

        round_state = RoundState(0, 0, pips, stacks, hands, [], deck, None)
        self.new_actions = [deque(), deque()]

        while not isinstance(round_state, TerminalState):
            self.log_round_state(round_state)

            active = round_state.button % 2
            player = self.players[active]

            if player.game_clock <= 0:
                self.log.append(f"{player.name} ran out of time.")
                action = FoldAction()
            else:
                try:
                    action = player.request_action(
                        hands[active], round_state.board, self.new_actions[active]
                    )
                except TimeoutError:
                    self.log.append(f"{player.name} timed out.")
                    action = FoldAction()
                except Exception as e:
                    player.log.append(f"{[player.name]} raised an exception: {e}")
                    self.log.append(f"{player.name} raised an exception.")
                    action = FoldAction()

            action = self._validate_action(action, round_state, player.name)
            self.log_action(player.name, action, round_state)

            self.new_actions[1 - active].append(action)
            round_state = round_state.proceed(action)

        board = round_state.previous_state.board
        for index, (player, delta) in enumerate(zip(self.players, round_state.deltas)):
            player.end_round(
                hands[index],
                hands[1 - index],
                board,
                self.new_actions[index],
                delta,
                last_round,
            )
            player.bankroll += delta
        self.log_terminal_state(round_state)

    def run_match(self) -> None:
        """
        Runs one match of poker.
        """
        print("Starting the Poker Game...")
        self.players = [
            Client(PLAYER_1_NAME, PLAYER_1_DNS),
            Client(PLAYER_2_NAME, PLAYER_2_DNS),
        ]
        player_names = [PLAYER_1_NAME, PLAYER_2_NAME]

        print("Checking ready...")
        ready = [player.check_ready(player_names) for player in self.players]
        if not all(ready):
            print("One or more bots are not ready. Aborting the match.")
            self.log.append("One or more bots are not ready. Aborting the match.")
            if not any(ready):
                self.log.append("Both players forfeited the match.")
            else:
                forfeiter = ready.index(False)
                self.log.append("Player {} forfeited the match.".format(player_names[forfeiter]))
                # Fold 1000 rounds = 1*500 small blind + 2*500 big blind = 1500
                self.players[1 - forfeiter].bankroll += 1500
                self.players[forfeiter].bankroll -= 1500
        else:
            print("Starting match...")
            self.original_players = self.players.copy()
            for self.round_num in range(1, NUM_ROUNDS + 1):
                if self.round_num % 50 == 0:
                    print(f"Starting round {self.round_num}...")
                    print(f"{self.players[0].name} remaining time: {self.players[0].game_clock}")
                    print(f"{self.players[1].name} remaining time: {self.players[1].game_clock}")
                self.log.append(f"\nRound #{self.round_num}")

                self.run_round((self.round_num == NUM_ROUNDS))
                self.players = self.players[::-1]  # Alternate the dealer

        self.log.append(f"{self.original_players[0].name} Bankroll: {self.original_players[0].bankroll}")
        self.log.append(f"{self.original_players[1].name} Bankroll: {self.original_players[1].bankroll}")

        self._finalize_log()
        add_match_entry(self.original_players[0].bankroll, self.original_players[1].bankroll)

    def _finalize_log(self) -> None:
        """
        Finalizes the game log, writing it to a file and uploading it.
        """
        csv_filename = f"{GAME_LOG_FILENAME}.csv"
        self._upload_or_write_file(self.csvlog, csv_filename, is_csv=True)

        log_filename = f"{GAME_LOG_FILENAME}.txt"
        self._upload_or_write_file(self.log, log_filename)

        for player in self.players:
            log_filename = os.path.join(player.name, f"{BOT_LOG_FILENAME}.txt")
            self._upload_or_write_file(player.log, log_filename)

    def _upload_or_write_file(self, content, base_filename, is_csv=False):
        filename = self._get_unique_filename(base_filename)
        if not upload_logs(content, filename):
            filename = os.path.join(LOGS_DIRECTORY, filename)
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            print(f"Writing {filename}")
            mode = "w"
            newline = "" if is_csv else None
            with open(filename, mode, newline=newline) as file:
                if is_csv:
                    writer = csv.writer(file)
                    writer.writerows(content)
                else:
                    file.write("\n".join(content))

    @staticmethod
    def _get_unique_filename(base_filename):
        file_idx = 1
        filename, ext = os.path.splitext(base_filename)
        unique_filename = base_filename
        while os.path.exists(unique_filename):
            unique_filename = f"{filename}_{file_idx}{ext}"
            file_idx += 1
        return unique_filename

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
            active = round_state.button % 2
            continue_cost = round_state.pips[1 - active] - round_state.pips[active]
            if RaiseAction in legal_actions and min_raise <= amount <= max_raise:
                return action
            elif CallAction in legal_actions and amount > continue_cost:
                self.log.append(f"{player_name} attempted illegal RaiseAction with amount {amount}")
                return CallAction()
            else:
                self.log.append(f"{player_name} attempted illegal RaiseAction with amount {amount}")
        elif type(action) in legal_actions:
            return action
        else:
            self.log.append(f"{player_name} attempted illegal {type(action).__name__}")

        return CheckAction() if CheckAction in legal_actions else FoldAction()

    def _create_csv_row(
        self, round_state: RoundState, player_name: str, action: str, action_amt: int
    ) -> None:
        self.csvlog.append([
            self.round_num,
            round_state.street,
            player_name,
            action,
            action_amt if action_amt else "",
            " ".join(round_state.hands[0] if self.round_num % 2 == 1 else round_state.hands[1]),
            " ".join(round_state.hands[1] if self.round_num % 2 == 1 else round_state.hands[0]),
            " ".join(round_state.board),
            self.original_players[0].bankroll,
        ])


if __name__ == "__main__":
    Game().run_match()
