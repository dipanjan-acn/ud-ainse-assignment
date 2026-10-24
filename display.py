"""Terminal output: ANSI colors, answer feedback, and the session summary."""

import os
from collections import Counter
from typing import TextIO

from quiz_engine import SessionStats

GREEN = "\033[32m"
RED = "\033[31m"
BOLD = "\033[1m"
RESET = "\033[0m"


def colorize(text: str, color: str, enabled: bool) -> str:
    """Wrap text in an ANSI color code when color is enabled."""
    return f"{color}{text}{RESET}" if enabled else text


def feedback_message(correct: bool, expected: str, enabled: bool) -> str:
    """Return the message shown after an answer: green if right, red if wrong."""
    if correct:
        return colorize("Correct!", GREEN, enabled)
    return colorize(f"Incorrect. The answer is: {expected}", RED, enabled)


def format_stats(stats: SessionStats, enabled: bool) -> str:
    """Render the session summary, including the most missed cards."""
    heading = colorize("Session summary", BOLD, enabled)
    lines = [heading, *_summary_lines(stats)]
    if stats.misses:
        lines.append(f"Most missed: {_format_misses(stats.misses)}")
    return "\n".join(lines)


def use_color(stream: TextIO) -> bool:
    """Return True when colors should be used for this output stream.

    Colors are off when NO_COLOR is set, or when the stream is not a terminal.
    """
    if "NO_COLOR" in os.environ:
        return False
    return stream.isatty()


def _summary_lines(stats: SessionStats) -> list[str]:
    """Return the totals and accuracy lines of the summary."""
    return [
        f"Attempts: {stats.attempts}",
        f"Correct: {stats.correct}",
        f"Incorrect: {stats.incorrect}",
        f"Accuracy: {stats.accuracy:.1f}%",
    ]


def _format_misses(misses: Counter[str]) -> str:
    """Format missed-card counts, most missed first."""
    return ", ".join(f"{front} ({count})" for front, count in misses.most_common())
