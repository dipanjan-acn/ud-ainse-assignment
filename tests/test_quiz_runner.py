"""Tests for the interactive quiz loop."""

import io

from quiz_engine import QuizSession
from quiz_modes import SequentialMode
from quiz_runner import Asker, run_quiz
from utils.flashcard import Flashcard

DECK = [
    Flashcard("API", "Application Programming Interface"),
    Flashcard("CPU", "Central Processing Unit"),
]


def scripted(answers: list[str]) -> Asker:
    """Return an `ask` function that replays the given answers in order."""
    iterator = iter(answers)
    return lambda prompt: next(iterator)


def make_session() -> QuizSession:
    """Create a fresh sequential session over the test deck."""
    return QuizSession(SequentialMode(DECK))


def test_run_quiz_returns_true_when_every_card_is_answered() -> None:
    finished = run_quiz(
        make_session(),
        scripted(["Application Programming Interface", "wrong"]),
        io.StringIO(),
        color=False,
    )

    assert finished is True


def test_run_quiz_prints_feedback_for_each_answer() -> None:
    out = io.StringIO()

    run_quiz(
        make_session(),
        scripted(["Application Programming Interface", "wrong"]),
        out,
        color=False,
    )

    text = out.getvalue()
    assert "Correct!" in text
    assert "Incorrect. The answer is: Central Processing Unit" in text


def test_run_quiz_shows_each_card_front_as_prompt() -> None:
    prompts: list[str] = []
    answers = scripted(["x", "y"])

    def ask(prompt: str) -> str:
        prompts.append(prompt)
        return answers(prompt)

    run_quiz(make_session(), ask, io.StringIO(), color=False)

    assert prompts[0].startswith("API")
    assert prompts[1].startswith("CPU")


def test_exit_word_stops_the_quiz_early() -> None:
    out = io.StringIO()
    session = make_session()

    finished = run_quiz(session, scripted(["exit"]), out, color=False)

    assert finished is False
    assert session.stats.attempts == 0
    assert "Leaving the quiz early." in out.getvalue()


def test_exit_word_is_case_and_space_insensitive() -> None:
    finished = run_quiz(make_session(), scripted(["  EXIT "]), io.StringIO(), False)

    assert finished is False


def test_ctrl_c_stops_gracefully_without_traceback() -> None:
    out = io.StringIO()

    def interrupt(prompt: str) -> str:
        raise KeyboardInterrupt

    finished = run_quiz(make_session(), interrupt, out, color=False)

    assert finished is False
    assert "Quiz stopped. Goodbye!" in out.getvalue()


def test_end_of_input_stops_gracefully() -> None:
    def closed(prompt: str) -> str:
        raise EOFError

    out = io.StringIO()

    assert run_quiz(make_session(), closed, out, color=False) is False
    assert "Quiz stopped" in out.getvalue()


def test_feedback_is_colored_when_color_is_enabled() -> None:
    out = io.StringIO()

    run_quiz(
        make_session(),
        scripted(["Application Programming Interface", "x"]),
        out,
        color=True,
    )

    assert "\033[32m" in out.getvalue()
    assert "\033[31m" in out.getvalue()
