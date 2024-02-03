from typing import List
import eval7


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
