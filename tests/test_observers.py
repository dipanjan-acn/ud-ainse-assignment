"""Tests for the answer observers: the session notifies them after each answer."""

from pathlib import Path

import pytest

from observers import AnswerLogger
from quiz_engine import AnswerEvent, QuizSession
from quiz_modes import SequentialMode
from utils.flashcard import Flashcard

API = Flashcard("API", "Application Programming Interface")


def test_session_notifies_every_observer_with_the_answer_event() -> None:
    received: list[AnswerEvent] = []
    session = QuizSession(SequentialMode([API]))
    session.add_observer(received.append)

    session.submit(API, "wrong")

    assert received == [
        AnswerEvent(
            front="API",
            expected="Application Programming Interface",
            answer="wrong",
            correct=False,
        )
    ]


def test_session_works_without_observers() -> None:
    session = QuizSession(SequentialMode([API]))

    assert session.submit(API, API.back) is True


def test_answer_logger_writes_one_line_per_answer(tmp_path: Path) -> None:
    log_path = tmp_path / "answers.log"
    logger = AnswerLogger(log_path)

    logger(AnswerEvent("API", "Application Programming Interface", "x", False))
    logger(
        AnswerEvent("CPU", "Central Processing Unit", "Central Processing Unit", True)
    )
    logger.close()

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert "API" in lines[0] and "incorrect" in lines[0]
    assert "CPU" in lines[1] and "correct" in lines[1] and "incorrect" not in lines[1]


def test_answer_logger_records_the_typed_answer(tmp_path: Path) -> None:
    log_path = tmp_path / "answers.log"
    logger = AnswerLogger(log_path)

    logger(AnswerEvent("API", "Application Programming Interface", "guess", False))
    logger.close()

    assert "answer='guess'" in log_path.read_text(encoding="utf-8")


def test_answer_logger_appends_across_instances(tmp_path: Path) -> None:
    log_path = tmp_path / "answers.log"
    event = AnswerEvent("API", "Application Programming Interface", "x", False)

    first = AnswerLogger(log_path)
    first(event)
    first.close()
    second = AnswerLogger(log_path)
    second(event)
    second.close()

    assert len(log_path.read_text(encoding="utf-8").splitlines()) == 2


def test_answer_logger_can_be_used_as_a_context_manager(tmp_path: Path) -> None:
    log_path = tmp_path / "answers.log"

    with AnswerLogger(log_path) as logger:
        logger(AnswerEvent("API", "x", "x", True))

    assert log_path.read_text(encoding="utf-8").count("\n") == 1


def test_answer_logger_rejects_an_unwritable_path(tmp_path: Path) -> None:
    with pytest.raises(OSError):
        AnswerLogger(tmp_path)
