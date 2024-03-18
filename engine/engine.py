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
    GAME_LOG_FILENAME,
    LOGS_DIRECTORY,
    NUM_ROUNDS,
    PLAYER_1_DNS,
    PLAYER_1_NAME,
    PLAYER_2_DNS,
    PLAYER_2_NAME,
    SMALL_BLIND,
    STARTING_STACK,
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
            ]
        ]
        self.new_actions: List[Deque[Action]] = [deque(), deque()]

    def log_round_state(self, round_state, num):
        """
        Logs the current state of the round.
        """
        temp1 = []
        temp2 = []

        if round_state.street == 0 and round_state.button == 0:
            self.log.append(f"{self.players[0].name} posts the blind of {SMALL_BLIND}")
            self.log.append(f"{self.players[1].name} posts the blind of {BIG_BLIND}")
            self.log.append(f"{self.players[0].name} dealt {round_state.hands[0]}")
            self.log.append(f"{self.players[1].name} dealt {round_state.hands[1]}")
            temp1.append(num)  # round num
            temp1.append(round_state.street)
            temp1.append(self.players[0].name)
            temp1.append("post blind")
            temp1.append(SMALL_BLIND)
            temp1.append(round_state.hands[0])
            temp1.append(round_state.hands[1])
            temp1.append(round_state.board)
            temp2.append(num)
            temp2.append(round_state.street)
            temp2.append(self.players[1].name)
            temp2.append("post blind")
            temp2.append(BIG_BLIND)
            temp2.append(round_state.hands[0])
            temp2.append(round_state.hands[1])
            temp2.append(round_state.board)
            self.csvlog.append(temp1)
            self.csvlog.append(temp2)

            # new_csv_entry[round_state.street].append(round_state.street)
            # new_csv_entry[round_state.street].append(self.players[0].name)
            # new_csv_entry.append(self.players[1].name)
            # new_csv_entry.append(round_state.hands[0])
            # new_csv_entry.append(round_state.hands[1])
            # new_csv_entry.append([])

        elif round_state.street > 0 and round_state.button == 1:
            # log the pot every street
            self.log.append(
                f"{STREET_NAMES[round_state.street]} Board: {round_state.board} Pot: {STARTING_STACK - round_state.stacks[0] + STARTING_STACK - round_state.stacks[1]}"
            )
            # temp1.append(round_state.street)
            # temp1.append(self.players[0].name)
            # temp1.append(round_state.hands[0])
            # temp1.append(f'nothing')
            # temp2.append(round_state.street)
            # temp2.append(self.players[1].name)
            # temp2.append(round_state.hands[1])
            # temp2.append(f'nothing')
            # self.csvlog.append(temp1)
            # self.csvlog.append(temp2)

    def log_action(
        self, player_name: str, action: Action, round_state: RoundState
    ) -> list:
        """
        Logs an action taken by a player.
        """
        new_csv_entry = []
        if isinstance(action, FoldAction):
            self.log.append(f"{player_name} folds")
            new_csv_entry.append(round_state.street)
            new_csv_entry.append(player_name)
            new_csv_entry.append("fold")
            new_csv_entry.append("")
            new_csv_entry.append(round_state.hands[0])
            new_csv_entry.append(round_state.hands[1])
            new_csv_entry.append(round_state.board)
        elif isinstance(action, CallAction):
            self.log.append(f"{player_name} calls")
            new_csv_entry.append(round_state.street)
            new_csv_entry.append(player_name)
            new_csv_entry.append("call")
            new_csv_entry.append("")
            new_csv_entry.append(round_state.hands[0])
            new_csv_entry.append(round_state.hands[1])
            new_csv_entry.append(round_state.board)
        elif isinstance(action, CheckAction):
            self.log.append(f"{player_name} checks")
            new_csv_entry.append(round_state.street)
            new_csv_entry.append(player_name)
            new_csv_entry.append("check")
            new_csv_entry.append("")
            new_csv_entry.append(round_state.hands[0])
            new_csv_entry.append(round_state.hands[1])
            new_csv_entry.append(round_state.board)
        else:  # isinstance(action, RaiseAction)
            self.log.append(f"{player_name} raises to {str(action.amount)}")
            new_csv_entry.append(round_state.street)
            new_csv_entry.append(player_name)
            new_csv_entry.append("raise")
            new_csv_entry.append(action.amount)
            new_csv_entry.append(round_state.hands[0])
            new_csv_entry.append(round_state.hands[1])
            new_csv_entry.append(round_state.board)

        return new_csv_entry

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

    def run_round(self, last_round: bool, num) -> None:
        """
        Runs one round of poker (1 hand).
        """
        pips = [SMALL_BLIND, BIG_BLIND]
        stacks = [STARTING_STACK - SMALL_BLIND, STARTING_STACK - BIG_BLIND]
        deck = ShortDeck()
        deck.shuffle()
        hands = [deck.deal(1), deck.deal(1)]
        # new_csv_entry = [[],[],[],[],[],[]]
        # new_csv_entry[0].append(num)
        # new_csv_entry[1].append(num)
        # new_csv_entry[2].append(num)

        round_state = RoundState(0, 0, pips, stacks, hands, [], deck, None)
        self.new_actions = [deque(), deque()]

        while not isinstance(round_state, TerminalState):
            self.log_round_state(round_state, num)
            # temp1.insert(0, num)
            # temp2.insert(0, num)
            # new_csv_entry.append(temp1)
            # new_csv_entry.append(temp2)

            active = round_state.button % 2
            player = self.players[active]
            action = player.request_action(
                hands[active], round_state.board, self.new_actions[active]
            )
            action = self._validate_action(action, round_state, player.name)
            temp = self.log_action(player.name, action, round_state)
            temp.insert(0, num)

            self.csvlog.append(temp)
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
        if not all(player.check_ready(player_names) for player in self.players):
            print("One or more bots are not ready. Aborting the match.")
            return
        print("Starting match...")
        for round_num in range(1, NUM_ROUNDS + 1):
            if round_num % 50 == 0:
                print(f"Starting round {round_num}...")
                print(
                    f"{self.players[0].name} remaining time: {self.players[0].game_clock}"
                )
                print(
                    f"{self.players[1].name} remaining time: {self.players[1].game_clock}"
                )
            self.log.append(f"\nRound #{round_num}")

            self.run_round((round_num == NUM_ROUNDS), round_num)
            self.players = self.players[::-1]  # Alternate the dealer

        self.log.append(f"{self.players[0].name} Bankroll: {self.players[0].bankroll}")
        self.log.append(f"{self.players[1].name} Bankroll: {self.players[1].bankroll}")

        self._finalize_log()

    def _finalize_log(self) -> None:
        """
        Finalizes the game log, writing it to a file and uploading it.
        """
        # log_filename = os.path.join(LOGS_DIRECTORY, f"{GAME_LOG_FILENAME}.txt")
        # log_index = 1
        # while os.path.exists(log_filename):
        #     log_filename = os.path.join(
        #         LOGS_DIRECTORY, f"{GAME_LOG_FILENAME}_{log_index}.txt"
        #     )
        #     log_index += 1

        csvlog_filename = os.path.join(LOGS_DIRECTORY, f"{GAME_LOG_FILENAME}.csv")
        csvlog_index = 1
        while os.path.exists(csvlog_filename):
            csvlog_filename = os.path.join(
                LOGS_DIRECTORY, f"{GAME_LOG_FILENAME}_{csvlog_index}.csv"
            )
            csvlog_index += 1

        # print(f"Writing {log_filename}")

        # with open(log_filename, "w") as log_file:
        #     log_file.write("\n".join(self.log))

        # Placeholder for uploading log, adjust as necessary
        # upload_log_to_s3(log_filename)

        with open(csvlog_filename, "w", newline="") as file:
            writer = csv.writer(file)
            # Write the data to the file
            for row in self.csvlog:
                writer.writerow(row)

        print(f'CSV file "{csvlog_filename}" has been created and populated with data.')

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
                self.log.append(
                    f"{player_name} attempted illegal RaiseAction with amount {amount}"
                )
        elif type(action) in legal_actions:
            return action
        else:
            self.log.append(f"{player_name} attempted illegal {type(action).__name__}")

        return CheckAction() if CheckAction in legal_actions else FoldAction()


if __name__ == "__main__":
    Game().run_match()
