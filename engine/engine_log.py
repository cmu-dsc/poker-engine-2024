import csv
import os
from collections import deque
from typing import Deque, List

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
    NUM_ROUNDS,
    PLAYER_1_DNS,
    PLAYER_1_NAME,
    PLAYER_2_DNS,
    PLAYER_2_NAME,
    SMALL_BLIND,
    STARTING_STACK,
)
from .evaluate import ShortDeck
from .player import Player
from .roundstate import RoundState



# Assume all necessary imports are done here

class Game:
    def __init__(self) -> None:
        self.players: List[Player] = []
        self.csv_logs: List[dict] = []  # Use a list of dictionaries to store log information
        self.new_actions: List[Deque[Action]] = [deque(), deque()]

    # Modify existing logging methods to append dictionaries to self.csv_logs
    # Example modification for log_action (similar modifications needed for other methods):
    def log_action(self, player_name: str, action: Action, round_state: RoundState, round_num: int) -> None:
        action_type = type(action).__name__
        log_entry = {
            "Round": round_num,
            "Player": player_name,
            "Action": action_type,
            # Pot and Player Hand might not always be relevant or available for all actions
            "Pot": STARTING_STACK * 2 - sum(round_state.stacks),
            "Player Hand": round_state.hands[self.players.index(player_name)],
            "Board": round_state.board
        }
        self.csv_logs.append(log_entry)






    def _finalize_log(self) -> None:
        log_filename = f"{GAME_LOG_FILENAME}.csv"
        log_index = 1
        while os.path.exists(log_filename):
            log_filename = f"{GAME_LOG_FILENAME}_{log_index}.csv"
            log_index += 1

        fieldnames = self.csv_logs[0].keys()  # Get field names from the first log entry
        with open(log_filename, mode='w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for log_entry in self.csv_logs:
                writer.writerow(log_entry)
        print(f"Game logs written to {log_filename}")

    def log_round_state(self, round_state: RoundState, round_num: int) -> None:
        if round_state.street == 0:
            self.csv_logs.append({
                "Round": round_num,
                "Action": "PostBlinds",
                "Player1": self.players[0].name,
                "Player2": self.players[1].name,
                "Player1 Hand": round_state.hands[0],
                "Player2 Hand": round_state.hands[1],
                "Board": round_state.board,
                "Pot": STARTING_STACK * 2 - sum(round_state.stacks),
            })
        else:
            self.csv_logs.append({
                "Round": round_num,
                "Action": STREET_NAMES[round_state.street] + " Board",
                "Board": round_state.board,
                "Pot": STARTING_STACK * 2 - sum(round_state.stacks),
            })

    def log_terminal_state(self, round_state: TerminalState, round_num: int) -> None:
    # Log the final board and pot size
        self.csv_logs.append({
            "Round": round_num,
            "Action": "Final Board",
            "Board": round_state.previous_state.board,
            "Pot": STARTING_STACK * 2 - sum(round_state.previous_state.stacks),
        })
        # Log the outcome for each player
        for index, player in enumerate(self.players):
            self.csv_logs.append({
                "Round": round_num,
                "Player": player.name,
                "Action": "Showdown",
                "Player Hand": round_state.previous_state.hands[index],
                "Outcome": round_state.deltas[index],
            })

    def run_round(self, round_num: int, last_round: bool) -> None:
    # Initialization code remains the same...
        """
        Runs one round of poker (1 hand).
        """
        pips = [SMALL_BLIND, BIG_BLIND]
        stacks = [STARTING_STACK - SMALL_BLIND, STARTING_STACK - BIG_BLIND]
        deck = ShortDeck()
        deck.shuffle()
        hands = [deck.deal(1), deck.deal(1)]
        board = []

        round_state = RoundState(0, 0, pips, stacks, hands, board, deck, None)
        self.new_actions = [deque(), deque()]
    
        while not isinstance(round_state, TerminalState):
            self.log_round_state(round_state, round_num)  # Pass round_num to log_round_state
            active = round_state.button % 2
            player = self.players[active]
            action = player.request_action(
                hands[active], round_state.board, self.new_actions[active]
            )
            action = self._validate_action(action, round_state, player.name, round_num)


            self.log_action(player.name, action, round_state, round_num)  # Modify to pass round_state and round_num
            self.new_actions[1 - active].append(action)
            round_state = round_state.proceed(action)

        # Final loop to handle end of round logic remains unchanged...
        for index, (player, delta) in enumerate(zip(self.players, round_state.deltas)):
            player.end_round(
                hands[1 - index], self.new_actions[index], delta, last_round
            )
            player.bankroll += delta
        self.log_terminal_state(round_state, round_num)  # Pass round_num to log_terminal_state

    def run_match(self) -> None:
        # Initialization code remains the same...
        """
        Runs one match of poker.
        """
        print("Starting the Poker Game...")
        self.players = [
            Player(PLAYER_1_NAME, PLAYER_1_DNS),
            Player(PLAYER_2_NAME, PLAYER_2_DNS),
        ]
        player_names = [PLAYER_1_NAME, PLAYER_2_NAME]

        print("Checking ready...")
        if not all(player.check_ready(player_names) for player in self.players):
            print("One or more bots are not ready. Aborting the match.")
            return
        print("Starting match...")
        
        for round_num in range(1, NUM_ROUNDS + 1):
            self.csv_logs.append({"Round": round_num, "Action": "StartRound"})  # Log start of round
            self.run_round(round_num, (round_num == NUM_ROUNDS))  # Pass round_num to run_round
        
    def _finalize_log(self) -> None:
        """
        Finalizes the game log, writing it to a CSV file.
        """

        log_filename = f"{GAME_LOG_FILENAME}.csv"
        log_index = 1
        while os.path.exists(log_filename):
            log_filename = f"{GAME_LOG_FILENAME}_{log_index}.csv"
            log_index += 1

        print(f"Writing {log_filename}")
        with open(log_filename, "w", newline='') as csvfile:
            fieldnames = ['Round', 'Action', 'Player', 'Player Hand', 'Board', 'Pot', 'Outcome']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for log_entry in self.csv_logs:
                writer.writerow(log_entry)

        # Placeholder for uploading log, adjust as necessary
        # upload_log_to_s3(log_filename)
                
    def _validate_action(
    self, action: Action, round_state: RoundState, player_name: str, round_num: int
) -> Action:
        legal_actions = round_state.legal_actions() if isinstance(round_state, RoundState) else {CheckAction}
        if isinstance(action, RaiseAction):
            amount = int(action.amount)
            min_raise, max_raise = round_state.raise_bounds()
            if RaiseAction in legal_actions and min_raise <= amount <= max_raise:
                return action
            else:
                self.csv_logs.append({
                    "Round": round_num,
                    "Player": player_name,
                    "Action": "Attempted Illegal Raise",
                    "Amount": amount,
                    "Legal Actions": ", ".join([a.__name__ for a in legal_actions]),
                })
        elif type(action) not in legal_actions:
            self.csv_logs.append({
                "Round": round_num,
                "Player": player_name,
                "Action": "Attempted Illegal Action",
                "Attempted Action": type(action).__name__,
                "Legal Actions": ", ".join([a.__name__ for a in legal_actions]),
            })
        
        # Choose a default legal action
        return CheckAction() if CheckAction in legal_actions else FoldAction()


if __name__ == "__main__":
    Game().run_match()
    # Other methods remain the same or are modified similarly to handle structured logging
