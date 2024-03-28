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
4-straight (468): 6h 7h 8d 9d
3-straight (2907): 6h 7h 8d
pair (6237): 2h 2d
high card (7020): everything else
TOTAL: 17550 combos
"""

from random import shuffle
from typing import List
from itertools import combinations


class ShortDeck:
    """Custom deck for the poker variant with cards ranked 1 to 9 across 3 suits."""

    def __init__(self):
        self.cards = [f"{rank}{suit}" for rank in "123456789" for suit in "shd"]

    def shuffle(self):
        """Shuffles the deck."""
        shuffle(self.cards)

    def deal(self, n):
        """Deals n cards from the deck."""
        return [self.cards.pop() for _ in range(n)]


def is_straight_flush(hand: List[str]) -> bool:
    return is_4flush(hand) and is_4straight(hand)


def is_trips(hand: List[str]) -> bool:
    return num_pairs(hand) == 3


def is_two_pair(hand: List[str]) -> bool:
    return num_pairs(hand) == 2


def is_4flush(hand: List[str]) -> bool:
    suits = [card[1] for card in hand]
    return len(set(suits)) == 1


def is_4straight(hand: List[str]) -> bool:
    ranks = [int(card[0]) for card in hand]
    return max(ranks) - min(ranks) == 3 and len(set(ranks)) == 4
    

def is_3straight(hand: List[str]) -> bool:
    ranks = sorted(int(card[0]) for card in hand)
    for combo in combinations(ranks, 3):
        if combo[0] == combo[1] - 1 and combo[1] == combo[2] - 1:
            return True
    return False


def is_pair(hand: List[str]) -> bool:
    return num_pairs(hand) == 1


def num_pairs(hand: List[str]) -> int:
    ans = 0
    for combo in combinations(hand, 2):
        if combo[0][0] == combo[1][0]:
            ans += 1
    return ans


def high_card_value(hand: List[str]) -> int:
    return sum(int(card[0]) * (10**i) for i, card in enumerate(sorted(hand)))


def frequent_card_value(hand: List[str]) -> int:
    ranks = [int(card[0]) for card in hand]
    counts = {x: ranks.count(x) for x in ranks}
    ranks.sort(key=lambda x: 10 * counts[x] + x)
    return sum(rank * (10**i) for i, rank in enumerate(ranks))


def find_straight(hand: List[str]) -> List[str]:
    s1 = list(sorted(hand))[1:4]
    s2 = list(sorted(hand))[0:3]
    ranks = list(sorted([int(card[0]) for card in hand]))
    if ranks[2] - ranks[0] == 2:
        return s1
    else:
        return s2


def evaluate(hand: List[str], board: List[str]) -> int:
    combined_hand = sorted(hand + board, key=lambda x: int(x[0]), reverse=True)
    if is_straight_flush(combined_hand):
        return 80000 + high_card_value(combined_hand)
    elif is_trips(combined_hand):
        return 70000 + frequent_card_value(combined_hand)
    elif is_two_pair(combined_hand):
        return 60000 + high_card_value(combined_hand)
    elif is_4flush(combined_hand):
        return 50000 + high_card_value(combined_hand)
    elif is_4straight(combined_hand):
        return 40000 + high_card_value(combined_hand)
    elif is_3straight(combined_hand):
        return 30000 + high_card_value(find_straight(combined_hand))
    elif is_pair(combined_hand):
        return 20000 + frequent_card_value(combined_hand)
    else:
        return 10000 + high_card_value(combined_hand)