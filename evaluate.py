from typing import List
import eval7


def is_trips(hand: List[eval7.Card]) -> bool:
    ranks = [card.rank for card in hand]
    return len(set(ranks)) == 1


def score_for_trips(hand: List[eval7.Card]) -> int:
    rank = hand[0].rank
    return 600 + rank_value(rank)


def is_straight_flush(hand: List[eval7.Card]) -> bool:
    return is_straight(hand) and is_flush(hand)


def score_for_straight_flush(hand: List[eval7.Card]) -> int:
    return 500 + high_card_value(hand)


def is_flush(hand: List[eval7.Card]) -> bool:
    suits = [card.suit for card in hand]
    return len(set(suits)) == 1


def score_for_flush(hand: List[eval7.Card]) -> int:
    return 400 + high_card_value(hand)


def is_straight(hand: List[eval7.Card]) -> bool:
    ranks = sorted([rank_value(card.rank) for card in hand])
    return ranks in [list(range(start, start + 3)) for start in range(1, 5)]


def score_for_straight(hand: List[eval7.Card]) -> int:
    return 300 + high_card_value(hand)


def is_pair(hand: List[eval7.Card]) -> bool:
    ranks = [card.rank for card in hand]
    return len(set(ranks)) == 2


def score_for_pair(hand: List[eval7.Card]) -> int:
    ranks = [card.rank for card in hand]
    pair_rank = max(set(hand), key=lambda c: ranks.count(c.rank)).rank
    return 200 + rank_value(pair_rank)


def high_card_value(hand: List[eval7.Card]) -> int:
    return max(rank_value(card.rank) for card in hand)


def evaluate(hand: List[eval7.Card]) -> int:
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
    return eval7.RANK_TO_INT[rank]
