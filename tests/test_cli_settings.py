"""Tests for generation, configuration precedence, and config errors in the CLI."""

import io
import json
from pathlib import Path

import pytest

import cli
from ai_transport import GenerationError
from cli import run
from utils.flashcard import Flashcard


def write_deck(folder: Path, name: str, cards: list[dict[str, str]]) -> Path:
    """Write a deck file and return its path."""
    path = folder / name
    path.write_text(json.dumps(cards), encoding="utf-8")
    return path


@pytest.fixture
def deck(tmp_path: Path) -> Path:
    """A one-card deck with the answer 'one'."""
    return write_deck(tmp_path, "deck.json", [{"front": "A", "back": "one"}])


def test_generate_without_save_is_an_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = run(["--generate", "networking"], out=io.StringIO())

    assert code == 1
    assert "--save" in capsys.readouterr().err


def test_generate_writes_the_deck_and_does_not_quiz(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[str, int, str]] = []

    def fake_generate(topic: str, count: int, key: str) -> list[Flashcard]:
        calls.append((topic, count, key))
        return [Flashcard("TCP", "Transmission Control Protocol")] * 2

    monkeypatch.setattr(cli, "generate_deck", fake_generate)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "key-from-env")
    target = tmp_path / "net.json"
    out = io.StringIO()

    code = run(
        ["--generate", "networking", "--count", "2", "--save", str(target)],
        ask=lambda p: pytest.fail("the quiz must not start"),
        out=out,
    )

    assert code == 0
    assert calls == [("networking", 2, "key-from-env")]
    assert "Saved 2 cards" in out.getvalue()
    assert json.loads(target.read_text(encoding="utf-8"))[0]["back"] == (
        "Transmission Control Protocol"
    )


def test_generation_errors_are_reported_without_a_traceback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def refuse(topic: str, count: int, key: str) -> list[Flashcard]:
        raise GenerationError("The AI service returned HTTP 401.")

    monkeypatch.setattr(cli, "generate_deck", refuse)

    code = run(
        ["--generate", "x", "--save", str(tmp_path / "o.json")],
        out=io.StringIO(),
    )

    assert code == 1
    assert "HTTP 401" in capsys.readouterr().err


def test_environment_mode_is_used_when_no_flag_is_given(
    deck: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FLASHCARD_MODE", "adaptive")
    out = io.StringIO()

    code = run(["-f", str(deck), "--stats", "--no-color"], ask=lambda p: "one", out=out)

    assert code == 0
    assert "Attempts: 1" in out.getvalue()


def test_flag_beats_an_invalid_environment_value(
    deck: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FLASHCARD_MODE", "not-a-mode")

    code = run(
        ["-f", str(deck), "-m", "random", "--no-color"],
        ask=lambda p: "one",
        out=io.StringIO(),
    )

    assert code == 0


def test_invalid_environment_mode_is_reported(
    deck: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("FLASHCARD_MODE", "not-a-mode")

    code = run(["-f", str(deck)], ask=lambda p: "one", out=io.StringIO())

    assert code == 1
    assert "Unknown mode 'not-a-mode'" in capsys.readouterr().err


def test_config_file_supplies_the_deck_when_no_flag_is_given(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    deck_path = write_deck(
        tmp_path, "from_config.json", [{"front": "Q", "back": "yes"}]
    )
    config = tmp_path / "flashcard.config.json"
    config.write_text(json.dumps({"deck": str(deck_path)}), encoding="utf-8")
    monkeypatch.setenv("FLASHCARD_CONFIG", str(config))
    prompts: list[str] = []

    def ask(prompt: str) -> str:
        prompts.append(prompt)
        return "yes"

    code = run(["--no-color"], ask=ask, out=io.StringIO())

    assert code == 0
    assert prompts and prompts[0].startswith("Q")


def test_config_file_log_file_receives_answers(
    deck: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    log = tmp_path / "answers.log"
    config = tmp_path / "flashcard.config.json"
    config.write_text(json.dumps({"log_file": str(log)}), encoding="utf-8")
    monkeypatch.setenv("FLASHCARD_CONFIG", str(config))

    run(["-f", str(deck), "--no-color"], ask=lambda p: "one", out=io.StringIO())

    assert "correct" in log.read_text(encoding="utf-8")


def test_broken_config_file_is_reported(
    deck: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config = tmp_path / "flashcard.config.json"
    config.write_text("{broken", encoding="utf-8")
    monkeypatch.setenv("FLASHCARD_CONFIG", str(config))

    code = run(["-f", str(deck)], ask=lambda p: "one", out=io.StringIO())

    assert code == 1
    assert "Cannot read config" in capsys.readouterr().err
