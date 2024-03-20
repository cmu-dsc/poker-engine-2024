"""
the deck consists of 27 cards, ranked 1 to 9, with 3 suits.

each player is dealt 2 cards preflop. A round of betting occurs.

there is a flop, of 1 card. A round of betting occurs.

there is a river, of 1 card. A round of betting occurs.

The hand rankings involve 4 cards:
straight flush (18): 2d 3d 4d 5d
trips (216): 6d 6s 6h
two pair (324): 4s 4h 9d 9h
4-flush (360): 2h 5h 6h 7h
3-straight (3186): 6h 7h 8d
3-flush (3588): 2h 7h 9h
pair (4998): 2h 2d
high card (4998): everything else
TOTAL: 17550 combos
"""

from random import shuffle
from typing import List, Tuple

RANKS = "123456789"
SUITS = "shd"


class ShortDeck:
    """Custom deck for the poker variant with cards ranked 1 to 6 across 3 suits."""

    def __init__(self):
        self.cards = {f"{rank}{suit}" for rank in RANKS for suit in SUITS}

    def shuffle(self):
        """Shuffles the deck."""
        self.cards = list(self.cards)
        shuffle(self.cards)
        self.cards = set(self.cards)

    def deal(self, n):
        """Deals n cards from the deck."""
        dealt_cards = set(self.cards.pop() for _ in range(n))
        self.cards -= dealt_cards
        return dealt_cards


def is_straight_flush(ranks: Tuple[int], suits: Tuple[str]) -> bool:
    return len(set(suits)) == 1 and is_straight(ranks)


def is_trips(ranks: Tuple[int]) -> bool:
    return len(set(ranks)) == 2 and any(ranks.count(r) == 3 for r in ranks)


def is_two_pair(ranks: Tuple[int]) -> bool:
    return len(set(ranks)) == 3 and all(ranks.count(r) >= 2 for r in set(ranks))


def is_4flush(suits: Tuple[str]) -> bool:
    return len(set(suits)) == 2


def is_straight(ranks: Tuple[int]) -> bool:
    return len(set(ranks)) == 4 and max(ranks) - min(ranks) == 3


def is_3flush(suits: Tuple[str]) -> bool:
    return len(set(suits)) == 2


def is_pair(ranks: Tuple[int]) -> bool:
    return len(set(ranks)) == 3


def high_card_value(ranks: Tuple[int]) -> int:
    return sum(rank * (10**i) for i, rank in enumerate(sorted(ranks, reverse=True)))


def frequent_card_value(ranks: Tuple[int]) -> int:
    counts = {x: ranks.count(x) for x in ranks}
    sorted_ranks = sorted(ranks, key=lambda x: (counts[x], x), reverse=True)
    return sum(rank * (10**i) for i, rank in enumerate(sorted_ranks))


def evaluate(hand: List[str], board: List[str]) -> int:
    combined_cards = sorted(hand + board, key=lambda x: RANKS.index(x[0]), reverse=True)
    ranks = tuple(RANKS.index(card[0]) for card in combined_cards)
    suits = tuple(card[1] for card in combined_cards)

    if is_straight_flush(ranks, suits):
        return 8000 + high_card_value(ranks)
    elif is_trips(ranks):
        return 7000 + frequent_card_value(ranks)
    elif is_two_pair(ranks):
        return 6000 + high_card_value(ranks)
    elif is_4flush(suits):
        return 4000 + high_card_value(ranks)
    elif is_straight(ranks):
        return 3000 + high_card_value(ranks)
    elif is_3flush(suits):
        return 3000 + high_card_value(ranks)
    elif is_pair(ranks):
        return 2000 + frequent_card_value(ranks)
    else:
        return 1000 + high_card_value(ranks)
