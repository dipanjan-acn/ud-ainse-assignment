"""Tests for building and writing the JSON session report."""

import json
from pathlib import Path

from export import build_report, write_report
from quiz_engine import SessionStats


def sample_stats() -> SessionStats:
    """Return statistics for two correct answers and two misses on one card."""
    stats = SessionStats()
    stats.record("API", correct=True)
    stats.record("CPU", correct=False)
    stats.record("CPU", correct=False)
    stats.record("DNS", correct=True)
    return stats


def test_build_report_includes_deck_mode_and_totals() -> None:
    report = build_report(sample_stats(), mode="adaptive", deck="data/x.json")

    assert report["deck"] == "data/x.json"
    assert report["mode"] == "adaptive"
    assert report["attempts"] == 4
    assert report["correct"] == 2
    assert report["incorrect"] == 2


def test_build_report_rounds_accuracy_to_one_decimal() -> None:
    stats = SessionStats(correct=2, incorrect=1)

    report = build_report(stats, mode="random", deck="d.json")

    assert report["accuracy_percent"] == 66.7


def test_build_report_lists_missed_cards_most_missed_first() -> None:
    report = build_report(sample_stats(), mode="sequential", deck="d.json")

    assert report["most_missed"] == {"CPU": 2}


def test_build_report_for_an_empty_session() -> None:
    report = build_report(SessionStats(), mode="sequential", deck="d.json")

    assert report["attempts"] == 0
    assert report["accuracy_percent"] == 0.0
    assert report["most_missed"] == {}


def test_write_report_saves_valid_json(tmp_path: Path) -> None:
    path = tmp_path / "report.json"
    report = build_report(sample_stats(), mode="sequential", deck="d.json")

    write_report(report, path)

    assert json.loads(path.read_text(encoding="utf-8")) == report
