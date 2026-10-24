"""Tests for terminal colors, feedback messages, and the stats summary."""

import io
from typing import Optional

import pytest

from display import (
    GREEN,
    RED,
    RESET,
    colorize,
    feedback_message,
    format_stats,
    use_color,
)
from quiz_engine import SessionStats


class FakeStream(io.StringIO):
    """A text stream that reports whether it is attached to a terminal."""

    def __init__(self, tty: bool) -> None:
        """Create an empty stream that claims to be a TTY when `tty` is True."""
        super().__init__()
        self._tty = tty

    def isatty(self) -> bool:
        """Return the configured terminal flag."""
        return self._tty


def test_colorize_wraps_text_when_enabled() -> None:
    assert colorize("hi", GREEN, enabled=True) == f"{GREEN}hi{RESET}"


def test_colorize_returns_plain_text_when_disabled() -> None:
    assert colorize("hi", RED, enabled=False) == "hi"


def test_feedback_for_correct_answer() -> None:
    assert feedback_message(True, "x", enabled=False) == "Correct!"


def test_feedback_for_incorrect_answer_shows_expected_text() -> None:
    message = feedback_message(False, "Central Processing Unit", enabled=False)

    assert message == "Incorrect. The answer is: Central Processing Unit"


def test_feedback_is_green_for_correct_and_red_for_incorrect() -> None:
    assert feedback_message(True, "x", enabled=True).startswith(GREEN)
    assert feedback_message(False, "x", enabled=True).startswith(RED)


def test_format_stats_reports_totals_and_accuracy() -> None:
    stats = SessionStats(correct=2, incorrect=1)

    text = format_stats(stats, enabled=False)

    assert "Attempts: 3" in text
    assert "Correct: 2" in text
    assert "Incorrect: 1" in text
    assert "Accuracy: 66.7%" in text


def test_format_stats_lists_most_missed_cards() -> None:
    stats = SessionStats()
    stats.record("CPU", correct=False)
    stats.record("CPU", correct=False)
    stats.record("API", correct=False)

    text = format_stats(stats, enabled=False)

    assert "Most missed: CPU (2), API (1)" in text


def test_format_stats_without_misses_has_no_missed_line() -> None:
    text = format_stats(SessionStats(correct=1), enabled=False)

    assert "Most missed" not in text


def test_format_stats_with_no_attempts_shows_zero_accuracy() -> None:
    assert "Accuracy: 0.0%" in format_stats(SessionStats(), enabled=False)


def test_format_stats_colors_the_heading_when_enabled() -> None:
    assert format_stats(SessionStats(), enabled=True).startswith("\033[1m")


@pytest.mark.parametrize(
    ("tty", "env_value", "expected"),
    [
        (True, None, True),
        (False, None, False),
        (True, "1", False),
        (True, "", False),
    ],
)
def test_use_color_depends_on_tty_and_no_color(
    monkeypatch: pytest.MonkeyPatch,
    tty: bool,
    env_value: Optional[str],
    expected: bool,
) -> None:
    if env_value is None:
        monkeypatch.delenv("NO_COLOR", raising=False)
    else:
        monkeypatch.setenv("NO_COLOR", env_value)

    assert use_color(FakeStream(tty=tty)) is expected
