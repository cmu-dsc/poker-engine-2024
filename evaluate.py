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

from random import random
from typing import List
import eval7


class ShortDeck:
    """Custom deck for the poker variant with cards ranked 1 to 6 across 3 suits."""

    def __init__(self):
        card_ranks = "234567"
        card_suits = "shd"  # spades, hearts, diamonds
        self.cards = [
            eval7.Card(rank + suit) for suit in card_suits for rank in card_ranks
        ]

    def shuffle(self):
        """Shuffles the deck."""
        random.shuffle(self.cards)

    def deal(self, n):
        """Deals n cards from the deck."""
        return [self.cards.pop() for _ in range(n)]

    def peek(self, n):
        """Peeks at the top n cards of the deck without removing them."""
        return self.cards[:n]


def is_trips(hand: List[eval7.Card]) -> bool:
    ranks = [card.rank for card in hand]
    return len(set(ranks)) == 1


def score_for_trips(hand: List[eval7.Card]) -> int:
    return 5000 + high_card_value(hand)


def is_straight_flush(hand: List[eval7.Card]) -> bool:
    return is_straight(hand) and is_flush(hand)


def score_for_straight_flush(hand: List[eval7.Card]) -> int:
    return 4000 + high_card_value(hand)


def is_flush(hand: List[eval7.Card]) -> bool:
    suits = [card.suit for card in hand]
    return len(set(suits)) == 1


def score_for_flush(hand: List[eval7.Card]) -> int:
    return 3000 + high_card_value(hand)


def is_straight(hand: List[eval7.Card]) -> bool:
    ranks = sorted([rank_value(card.rank) for card in hand])
    return ranks[0] + 1 == ranks[1] and ranks[1] + 1 == ranks[2]


def score_for_straight(hand: List[eval7.Card]) -> int:
    return 2000 + high_card_value(hand)


def is_pair(hand: List[eval7.Card]) -> bool:
    ranks = [card.rank for card in hand]
    return len(set(ranks)) == 2


def score_for_pair(hand: List[eval7.Card]) -> int:
    ranks = sorted([rank_value(card.rank) for card in hand])
    if ranks[0] == ranks[1]:
        return 1000 + 110 * ranks[0] + ranks[2]
    else:
        return 1000 + 110 * ranks[2] + ranks[0]


def high_card_value(hand: List[eval7.Card]) -> int:
    ranks = sorted([rank_value(card.rank) for card in hand], reverse=True)
    return 100 * ranks[0] + 10 * ranks[1] + 1 * ranks[2]


def evaluate(hand: List[eval7.Card]) -> int:
    assert len(hand) == 3, "hand must be complete"
    if is_trips(hand):
        return score_for_trips(hand)
    elif is_straight_flush(hand):
        return score_for_straight_flush(hand)
    elif is_flush(hand):
        return score_for_flush(hand)
    elif is_straight(hand):
        return score_for_straight(hand)
    elif is_pair(hand):
        return score_for_pair(hand)
    else:
        return high_card_value(hand)


def rank_value(rank: str) -> int:
    return int(rank)
