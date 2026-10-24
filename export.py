"""Export the session summary as a JSON report."""

import json
from pathlib import Path
from typing import Any

from quiz_engine import SessionStats


def build_report(stats: SessionStats, mode: str, deck: str) -> dict[str, Any]:
    """Describe one quiz session as a JSON-ready dictionary."""
    report: dict[str, Any] = {"deck": deck, "mode": mode}
    report.update(_totals(stats))
    return report


def _totals(stats: SessionStats) -> dict[str, Any]:
    """Return the counts, accuracy, and missed cards for a session."""
    return {
        "attempts": stats.attempts,
        "correct": stats.correct,
        "incorrect": stats.incorrect,
        "accuracy_percent": round(stats.accuracy, 1),
        "most_missed": dict(stats.misses.most_common()),
    }


def write_report(report: dict[str, Any], path: Path) -> None:
    """Save the report as indented JSON.

    Raises:
        OSError: If the file cannot be written.
    """
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
