"""Tests for the quiz mode strategies and the mode factory."""

import random
from typing import Sequence

import pytest

from quiz_engine import create_quiz_mode
from quiz_modes import AdaptiveMode, QuizMode, RandomMode, SequentialMode
from utils.flashcard import Flashcard

DECK: list[Flashcard] = [
    Flashcard("one", "1"),
    Flashcard("two", "2"),
    Flashcard("three", "3"),
]


def drain(mode: QuizMode, correct: bool = True) -> list[Flashcard]:
    """Ask every card, answering all of them with `correct`, and return the order."""
    asked: list[Flashcard] = []
    card = mode.next_card()
    while card is not None:
        asked.append(card)
        mode.record_answer(card, correct)
        card = mode.next_card()
    return asked


def test_sequential_mode_keeps_file_order() -> None:
    assert drain(SequentialMode(DECK)) == DECK


def test_sequential_mode_empty_deck_returns_none() -> None:
    assert SequentialMode([]).next_card() is None


def test_sequential_mode_ignores_wrong_answers() -> None:
    assert drain(SequentialMode(DECK), correct=False) == DECK


def test_random_mode_asks_every_card_once() -> None:
    asked = drain(RandomMode(DECK, random.Random(3)))

    assert sorted(asked, key=lambda c: c.front) == sorted(DECK, key=lambda c: c.front)


def test_random_mode_uses_the_supplied_generator() -> None:
    expected = list(DECK)
    random.Random(7).shuffle(expected)

    assert drain(RandomMode(DECK, random.Random(7))) == expected


def test_random_mode_does_not_reorder_the_input_list() -> None:
    original = list(DECK)

    drain(RandomMode(DECK, random.Random(1)))

    assert DECK == original


def test_random_mode_empty_deck_returns_none() -> None:
    assert RandomMode([], random.Random(1)).next_card() is None


def test_adaptive_mode_behavior() -> None:
    mode = AdaptiveMode(DECK)

    first = mode.next_card()
    assert first == DECK[0]
    mode.record_answer(first, correct=False)

    assert mode.remaining() == 3, "a wrong card should be queued again"

    asked = drain(mode)

    assert asked == [DECK[1], DECK[2], DECK[0]]


def test_adaptive_mode_repeats_only_incorrect_cards() -> None:
    mode = AdaptiveMode(DECK)

    assert mode.next_card() == DECK[0]
    mode.record_answer(DECK[0], correct=True)
    assert mode.next_card() == DECK[1]
    mode.record_answer(DECK[1], correct=False)
    assert mode.next_card() == DECK[2]
    mode.record_answer(DECK[2], correct=True)

    assert mode.next_card() == DECK[1]
    mode.record_answer(DECK[1], correct=True)
    assert mode.next_card() is None


def test_adaptive_mode_keeps_repeating_until_answered_correctly() -> None:
    mode = AdaptiveMode([Flashcard("hard", "x")])
    card = mode.next_card()
    for _ in range(3):
        assert card is not None
        mode.record_answer(card, correct=False)
        card = mode.next_card()

    assert card is not None
    mode.record_answer(card, correct=True)

    assert mode.next_card() is None


def test_adaptive_mode_empty_deck_returns_none() -> None:
    assert AdaptiveMode([]).next_card() is None


def test_quiz_mode_is_abstract() -> None:
    with pytest.raises(TypeError):
        QuizMode(DECK)  # type: ignore[abstract]


def test_quiz_mode_factory() -> None:
    expected_types = {
        "sequential": SequentialMode,
        "random": RandomMode,
        "adaptive": AdaptiveMode,
    }

    for name, expected_type in expected_types.items():
        mode = create_quiz_mode(name, DECK, random.Random(0))
        assert type(mode) is expected_type


def test_factory_passes_the_cards_to_the_mode() -> None:
    cards: Sequence[Flashcard] = DECK

    mode = create_quiz_mode("sequential", cards)

    assert drain(mode) == list(cards)


def test_factory_rejects_unknown_mode_name() -> None:
    with pytest.raises(ValueError, match="Unknown quiz mode 'hard'"):
        create_quiz_mode("hard", DECK)
