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

from random import shuffle
from typing import List


class ShortDeck:
    """Custom deck for the poker variant with cards ranked 1 to 6 across 3 suits."""

    def __init__(self):
        self.cards = [f"{rank}{suit}" for rank in "123456" for suit in "shd"]

    def shuffle(self):
        """Shuffles the deck."""
        shuffle(self.cards)

    def deal(self, n):
        """Deals n cards from the deck."""
        return [self.cards.pop() for _ in range(n)]


def is_trips(hand: List[str]) -> bool:
    return len(set(card[0] for card in hand)) == 1


def is_straight_flush(hand: List[str]) -> bool:
    return is_straight(hand) and is_flush(hand)


def is_flush(hand: List[str]) -> bool:
    return len(set(card[1] for card in hand)) == 1


def is_straight(hand: List[str]) -> bool:
    """Assumes hand is sorted."""
    ranks = sorted(int(card[0]) for card in hand)
    return ranks in [list(range(i, i + 3)) for i in range(1, 5)]


def is_pair(hand: List[str]) -> bool:
    ranks = [card[0] for card in hand]
    return len(set(ranks)) == 2


def high_card_value(hand: List[str]) -> int:
    return sum(
        int(card[0]) * (10**i) for i, card in enumerate(sorted(hand, reverse=True))
    )


def evaluate(hand: List[str], board: List[str]) -> int:
    combined_hand = sorted(hand + board, key=lambda x: int(x[0]), reverse=True)
    if is_trips(combined_hand):
        return 6000 + high_card_value(combined_hand)
    elif is_straight_flush(combined_hand):
        return 5000 + high_card_value(combined_hand)
    elif is_flush(combined_hand):
        return 4000 + high_card_value(combined_hand)
    elif is_straight(combined_hand):
        return 3000 + high_card_value(combined_hand)
    elif is_pair(combined_hand):
        return 2000 + high_card_value(combined_hand)
    else:
        return 1000 + high_card_value(combined_hand)
