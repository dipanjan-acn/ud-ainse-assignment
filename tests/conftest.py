"""Shared test fixtures."""

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Keep the developer's environment and config file out of the tests."""
    for name in (
        "FLASHCARD_MODE",
        "FLASHCARD_DECK",
        "FLASHCARD_LOG_FILE",
        "ANTHROPIC_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("FLASHCARD_CONFIG", str(tmp_path / "absent.config.json"))
