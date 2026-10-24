"""Integration tests: a whole quiz session from deck file to final stats."""

import io
import json
from pathlib import Path
from typing import Callable

import pytest

from cli import run

DECK_JSON = (
    '{"cards": ['
    '{"front": "API", "back": "Application Programming Interface"},'
    '{"front": "CPU", "back": "Central Processing Unit"},'
    '{"front": "DNS", "back": "Domain Name System"}'
    "]}"
)


@pytest.fixture
def deck_path(tmp_path: Path) -> Path:
    """Write the three-card deck to a temporary file and return its path."""
    path = tmp_path / "deck.json"
    path.write_text(DECK_JSON, encoding="utf-8")
    return path


def scripted(answers: list[str]) -> Callable[[str], str]:
    """Return an `ask` function that replays the given answers in order."""
    iterator = iter(answers)
    return lambda prompt: next(iterator)


def test_full_session_with_three_answers_reports_correct_stats(
    deck_path: Path,
) -> None:
    out = io.StringIO()
    answers = [
        "application programming interface",
        "wrong answer",
        "Domain Name System",
    ]

    code = run(
        ["-f", str(deck_path), "--stats", "--no-color"],
        ask=scripted(answers),
        out=out,
    )

    text = out.getvalue()
    assert code == 0
    assert "Attempts: 3" in text
    assert "Correct: 2" in text
    assert "Incorrect: 1" in text
    assert "Accuracy: 66.7%" in text
    assert "Most missed: CPU (1)" in text


def test_adaptive_session_repeats_missed_card_until_correct(
    deck_path: Path,
) -> None:
    out = io.StringIO()
    answers = [
        "x",
        "Central Processing Unit",
        "Domain Name System",
        "Application Programming Interface",
    ]

    run(
        ["-f", str(deck_path), "-m", "adaptive", "--stats", "--no-color"],
        ask=scripted(answers),
        out=out,
    )

    text = out.getvalue()
    assert "Attempts: 4" in text
    assert "Correct: 3" in text
    assert "Incorrect: 1" in text


def test_export_and_log_file_capture_the_session(
    deck_path: Path, tmp_path: Path
) -> None:
    report_path = tmp_path / "report.json"
    log_path = tmp_path / "answers.log"

    run(
        [
            "-f",
            str(deck_path),
            "--export",
            str(report_path),
            "--log-file",
            str(log_path),
            "--no-color",
        ],
        ask=scripted(["Application Programming Interface", "wrong", "exit"]),
        out=io.StringIO(),
    )

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["attempts"] == 2
    assert report["correct"] == 1
    assert len(log_path.read_text(encoding="utf-8").splitlines()) == 2


def test_exit_mid_session_still_reports_stats(deck_path: Path) -> None:
    out = io.StringIO()

    run(
        ["-f", str(deck_path), "--stats", "--no-color"],
        ask=scripted(["Application Programming Interface", "exit"]),
        out=out,
    )

    text = out.getvalue()
    assert "Leaving the quiz early." in text
    assert "Attempts: 1" in text
