"""Tests for command-line parsing, error handling, and the run entry point."""

import importlib
import io
import runpy
from pathlib import Path
from typing import Callable

import pytest

import cli
from cli import DEFAULT_DECK, build_parser, run


def recording_ask(prompts: list[str]) -> Callable[[str], str]:
    """Return an `ask` function that records each prompt and answers 'one'."""

    def ask(prompt: str) -> str:
        prompts.append(prompt)
        return "one"

    return ask


def write_deck(tmp_path: Path, text: str) -> Path:
    """Write a deck file into the temporary directory and return its path."""
    path = tmp_path / "deck.json"
    path.write_text(text, encoding="utf-8")
    return path


def test_help_lists_every_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        build_parser().parse_args(["--help"])

    help_text = capsys.readouterr().out
    assert exit_info.value.code == 0
    for flag in ("--file", "--mode", "--stats", "--no-color"):
        assert flag in help_text


def test_short_flags_are_accepted() -> None:
    args = build_parser().parse_args(["-f", "a.json", "-m", "adaptive"])

    assert args.file == Path("a.json")
    assert args.mode == "adaptive"


def test_mode_is_unset_so_that_config_can_supply_it() -> None:
    assert build_parser().parse_args([]).mode is None


def test_default_deck_is_the_bundled_glossary() -> None:
    assert DEFAULT_DECK.name == "glossary.json"
    assert DEFAULT_DECK.exists()


def test_unknown_mode_is_rejected_by_argparse() -> None:
    with pytest.raises(SystemExit) as exit_info:
        build_parser().parse_args(["--mode", "hard"])

    assert exit_info.value.code == 2


def test_run_quizzes_the_deck_and_returns_zero(tmp_path: Path) -> None:
    deck = write_deck(tmp_path, '[{"front": "A", "back": "one"}]')
    out = io.StringIO()

    code = run(["-f", str(deck)], ask=lambda prompt: "one", out=out)

    assert code == 0
    assert "Correct!" in out.getvalue()


def test_run_reports_a_bad_deck_without_a_traceback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    deck = write_deck(tmp_path, '[{"front": "A"}]')

    code = run(["-f", str(deck)], ask=lambda prompt: "", out=io.StringIO())

    assert code == 1
    assert "Error:" in capsys.readouterr().err


def test_run_reports_a_missing_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = run(["-f", str(tmp_path / "nope.json")], ask=lambda p: "", out=io.StringIO())

    assert code == 1
    assert "File not found" in capsys.readouterr().err


def test_run_prints_stats_when_requested(tmp_path: Path) -> None:
    deck = write_deck(tmp_path, '[{"front": "A", "back": "one"}]')
    out = io.StringIO()

    run(["-f", str(deck), "--stats"], ask=lambda prompt: "one", out=out)

    assert "Accuracy: 100.0%" in out.getvalue()


def test_run_omits_stats_by_default(tmp_path: Path) -> None:
    deck = write_deck(tmp_path, '[{"front": "A", "back": "one"}]')
    out = io.StringIO()

    run(["-f", str(deck)], ask=lambda prompt: "one", out=out)

    assert "Accuracy" not in out.getvalue()


def test_no_color_flag_disables_colors(tmp_path: Path) -> None:
    deck = write_deck(tmp_path, '[{"front": "A", "back": "one"}]')
    out = io.StringIO()

    run(["-f", str(deck), "--no-color"], ask=lambda prompt: "one", out=out)

    assert "\033[" not in out.getvalue()


def test_export_to_a_directory_fails_before_the_quiz_starts(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    deck = write_deck(tmp_path, '[{"front": "A", "back": "one"}]')
    prompts: list[str] = []

    code = run(
        ["-f", str(deck), "--export", str(tmp_path)],
        ask=recording_ask(prompts),
        out=io.StringIO(),
    )

    assert code == 1
    assert prompts == [], "the quiz must not start when the report cannot be saved"
    assert "Error:" in capsys.readouterr().err


def test_export_into_a_missing_folder_fails_before_the_quiz_starts(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    deck = write_deck(tmp_path, '[{"front": "A", "back": "one"}]')
    prompts: list[str] = []
    target = tmp_path / "no_such_folder" / "report.json"

    code = run(
        ["-f", str(deck), "--export", str(target)],
        ask=recording_ask(prompts),
        out=io.StringIO(),
    )

    assert code == 1
    assert prompts == []
    assert "does not exist" in capsys.readouterr().err


def test_running_main_py_starts_the_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "run", lambda: 0)
    entry_point = Path(__file__).resolve().parent.parent / "main.py"

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(str(entry_point), run_name="__main__")

    assert exit_info.value.code == 0


def test_importing_main_py_does_not_start_the_quiz() -> None:
    module = importlib.import_module("main")

    assert getattr(module, "main") is cli.main


def test_main_exits_with_the_run_status(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "run", lambda: 3)

    with pytest.raises(SystemExit) as exit_info:
        cli.main()

    assert exit_info.value.code == 3
