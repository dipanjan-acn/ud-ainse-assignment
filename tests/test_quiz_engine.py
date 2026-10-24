"""Tests for answer matching, session statistics, and the quiz session."""

import pytest

from quiz_engine import QuizSession, SessionStats, is_correct
from quiz_modes import AdaptiveMode, SequentialMode
from utils.flashcard import Flashcard

API = Flashcard("API", "Application Programming Interface")
CPU = Flashcard("CPU", "Central Processing Unit")


@pytest.mark.parametrize(
    "answer",
    [
        "Application Programming Interface",
        "application programming interface",
        "  APPLICATION   programming\tinterface  ",
    ],
)
def test_is_correct_ignores_case_and_extra_whitespace(answer: str) -> None:
    assert is_correct(answer, API.back)


@pytest.mark.parametrize(
    "answer", ["", "   ", "Application", "Application Programming"]
)
def test_is_correct_rejects_wrong_or_partial_answers(answer: str) -> None:
    assert not is_correct(answer, API.back)


def test_stats_start_at_zero() -> None:
    stats = SessionStats()

    assert (stats.correct, stats.incorrect, stats.attempts) == (0, 0, 0)


def test_accuracy_is_zero_before_any_attempt() -> None:
    assert SessionStats().accuracy == 0.0


def test_accuracy_is_a_percentage_of_attempts() -> None:
    stats = SessionStats()
    stats.record("API", correct=True)
    stats.record("CPU", correct=False)
    stats.record("CPU", correct=True)

    assert stats.accuracy == pytest.approx(66.666, rel=1e-3)


def test_misses_are_counted_per_card_front() -> None:
    stats = SessionStats()
    stats.record("CPU", correct=False)
    stats.record("CPU", correct=False)
    stats.record("API", correct=True)

    assert stats.misses == {"CPU": 2}


def test_session_submit_returns_correctness() -> None:
    session = QuizSession(SequentialMode([API, CPU]))

    assert session.submit(API, "application programming interface") is True
    assert session.submit(CPU, "wrong") is False


def test_session_submit_updates_the_stats() -> None:
    session = QuizSession(SequentialMode([API, CPU]))

    session.submit(API, API.back)
    session.submit(CPU, "wrong")

    assert session.stats.correct == 1
    assert session.stats.incorrect == 1
    assert session.stats.misses == {"CPU": 1}


def test_session_hands_out_cards_from_its_mode() -> None:
    session = QuizSession(SequentialMode([API, CPU]))

    assert session.next_card() == API
    assert session.next_card() == CPU
    assert session.next_card() is None


def test_session_passes_answers_to_the_mode() -> None:
    session = QuizSession(AdaptiveMode([API]))
    session.next_card()

    session.submit(API, "wrong")

    assert session.next_card() == API
