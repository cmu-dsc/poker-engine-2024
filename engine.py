"""
CMU Data Science Club Poker Bot Competition Game Engine 2024
"""

"""
the deck consists of 18 cards, ranked 1 to 6, with 3 suits.

each player is dealt 1 card preflop. A round of betting occurs.

there is a flop, of 1 card. A round of betting occurs.

there is a river, of 1 card. A round of betting occurs.

The hand rankings involve 3 cards:
trips (6 combos)
straight flush (12 combos)
flush (48 combos)
straight (96 combos)
pair (270 combos)
high card (384 combos)
TOTAL: 816 combos
"""

from collections import namedtuple
import json
import os
from queue import Queue
import socket
import subprocess
from threading import Thread
import time
from typing import List, Optional, Set, Type, Union
from evaluate import evaluate
import eval7

from config import *

FoldAction = namedtuple("FoldAction", [])
CallAction = namedtuple("CallAction", [])
CheckAction = namedtuple("CheckAction", [])
RaiseAction = namedtuple("RaiseAction", ["amount"])
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


class ShortDeck(eval7.Deck):
    """Custom deck for the poker variant with cards ranked 1 to 6 across 3 suits."""

    def __init__(self):
        card_ranks = "123456"
        card_suits = "shd"  # spades, hearts, diamonds
        self.cards = [
            eval7.Card(rank + suit) for suit in card_suits for rank in card_ranks
        ]
        super().__init__()


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

    def proceed(self, action) -> "RoundState":
        """
        Advances the game tree by one action performed by the active player.
        """
        active = self.button % 2
        if isinstance(action, FoldAction):
            # If a player folds, the other player wins the pot
            delta = self.stacks[1 - active] - STARTING_STACK
            return TerminalState([delta, -delta], self.previous_state)

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
    Handles subprocess and socket interactions with one player's pokerbot.
    """

    def __init__(self, name: str, path: str) -> None:
        self.name: str = name
        self.path: str = path
        self.game_clock: float = STARTING_GAME_CLOCK
        self.bankroll: int = 0
        self.commands: Optional[dict] = None
        self.bot_subprocess: Optional[subprocess.Popen] = None
        self.socketfile = None
        self.bytes_queue: Queue = Queue()

    def build(self) -> None:
        """
        Loads the commands file and builds the pokerbot.
        """
        try:
            with open(os.path.join(self.path, "commands.json"), "r") as json_file:
                commands = json.load(json_file)
            if (
                "build" in commands
                and "run" in commands
                and isinstance(commands["build"], list)
                and isinstance(commands["run"], list)
            ):
                self.commands = commands
            else:
                print(f"{self.name} commands.json missing command")
        except FileNotFoundError:
            print(f"{self.name} commands.json not found - check PLAYER_PATH")
        except json.decoder.JSONDecodeError:
            print(f"{self.name} commands.json misformatted")

        if self.commands and self.commands["build"]:
            try:
                proc = subprocess.run(
                    self.commands["build"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    cwd=self.path,
                    timeout=BUILD_TIMEOUT,
                    check=False,
                )
                self.bytes_queue.put(proc.stdout)
            except subprocess.TimeoutExpired as timeout_expired:
                error_message = f"Timed out waiting for {self.name} to build"
                print(error_message)
                self.bytes_queue.put(timeout_expired.stdout)
                self.bytes_queue.put(error_message.encode())
            except (TypeError, ValueError):
                print(f"{self.name} build command misformatted")
            except OSError:
                print(f'{self.name} build failed - check "build" in commands.json')

    def run(self) -> None:
        """
        Runs the pokerbot and establishes the socket connection.
        """
        if self.commands and "run" in self.commands and self.commands["run"]:
            try:
                # Create a server socket to listen for a connection from the pokerbot
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                with server_socket:
                    server_socket.bind(("", 0))  # Bind to an available port
                    server_socket.settimeout(CONNECT_TIMEOUT)
                    server_socket.listen()
                    port = server_socket.getsockname()[
                        1
                    ]  # Get the dynamically assigned port

                    # Start the pokerbot process
                    self.bot_subprocess = subprocess.Popen(
                        self.commands["run"] + [str(port)],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        cwd=self.path,
                    )

                    # Thread for reading bot's output
                    def enqueue_output(out, queue):
                        for line in iter(out.readline, b""):
                            queue.put(line)
                        out.close()

                    # Start a separate bot listening thread
                    Thread(
                        target=enqueue_output,
                        args=(self.bot_subprocess.stdout, self.bytes_queue),
                        daemon=True,
                    ).start()

                    # Wait for the bot to connect
                    client_socket, _ = server_socket.accept()
                    with client_socket:
                        client_socket.settimeout(CONNECT_TIMEOUT)
                        self.socketfile = client_socket.makefile("rw")
                        print(f"{self.name} connected successfully")

            except (TypeError, ValueError):
                print(f"{self.name} run command misformatted")
            except OSError:
                print(f'{self.name} run failed - check "run" in commands.json')
            except socket.timeout:
                print(f"Timed out waiting for {self.name} to connect")

    def stop(self) -> None:
        """
        Closes the socket connection and stops the pokerbot.
        """
        if self.socketfile is not None:
            try:
                self.socketfile.write("Q\n")
                self.socketfile.flush()  # Ensure the message is sent before closing
                self.socketfile.close()
            except (socket.timeout, OSError) as e:
                print(f"Error while disconnecting {self.name}: {e}")

        if self.bot_subprocess is not None:
            try:
                outs, _ = self.bot_subprocess.communicate(timeout=CONNECT_TIMEOUT)
                self.bytes_queue.put(outs)
            except subprocess.TimeoutExpired:
                print(f"Timed out waiting for {self.name} to quit")
                self.bot_subprocess.kill()
                outs, _ = self.bot_subprocess.communicate()
                self.bytes_queue.put(outs)

        # Write the subprocess output to a log file
        log_file_path = f"{self.name}.txt"
        with open(log_file_path, "wb") as log_file:
            bytes_written = 0
            for output in self.bytes_queue.queue:
                try:
                    bytes_written += log_file.write(output)
                    if bytes_written >= PLAYER_LOG_SIZE_LIMIT:
                        break
                except TypeError:
                    pass

    def query(
        self, round_state: RoundState, player_message: List[str], game_log: List[str]
    ) -> Union[FoldAction, CallAction, CheckAction, RaiseAction]:
        """
        Requests one action from the pokerbot over the socket connection.
        At the end of the round, we request a CheckAction from the pokerbot.
        """
        legal_actions = (
            round_state.legal_actions()
            if isinstance(round_state, RoundState)
            else {CheckAction}
        )
        if self.socketfile is not None and self.game_clock > 0.0:
            try:
                player_message[0] = f"T{self.game_clock:.3f}"
                message = " ".join(player_message) + "\n"
                del player_message[1:]  # do not send redundant action history
                start_time = time.perf_counter()
                self.socketfile.write(message)
                self.socketfile.flush()
                clause = self.socketfile.readline().strip()
                end_time = time.perf_counter()
                if ENFORCE_GAME_CLOCK:
                    self.game_clock -= end_time - start_time
                if self.game_clock <= 0.0:
                    raise socket.timeout

                action_type = DECODE.get(clause[0], None)
                if action_type in legal_actions:
                    if action_type == RaiseAction:
                        amount = int(clause[1:])
                        min_raise, max_raise = round_state.raise_bounds()
                        if min_raise <= amount <= max_raise:
                            return action_type(amount)
                    else:
                        return action_type()
                else:
                    game_log.append(
                        f"{self.name} attempted illegal {action_type.__name__} or unknown action"
                    )

            except socket.timeout:
                error_message = f"{self.name} ran out of time"
                game_log.append(error_message)
                print(error_message)
                self.game_clock = 0.0
            except OSError:
                error_message = f"{self.name} disconnected"
                game_log.append(error_message)
                print(error_message)
                self.game_clock = 0.0
            except (IndexError, KeyError, ValueError) as e:
                game_log.append(f"{self.name} response misformatted: {clause} - {e}")

        return CheckAction() if CheckAction in legal_actions else FoldAction()


class Game:
    """
    Manages logging and the high-level game procedure.
    """

    def __init__(self) -> None:
        pass

    def log_round_state(self, players, round_state) -> None:
        """
        Incorporates RoundState information into the game log and player messages.
        """

    def log_action(self, name, action, bet_override) -> None:
        """
        Incorporates action information into the game log and player messages.
        """

    def log_terminal_state(self, players, round_state) -> None:
        """
        Incorporates TerminalState information into the game log and player messages.
        """

    def run_round(self, players):
        """
        Runs one round of poker (1 hand).
        """

    def run(self):
        """
        Runs one game of poker.
        """


if __name__ == "__main__":
    Game().run()
