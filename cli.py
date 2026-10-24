"""Command-line interface: parse arguments, resolve settings, and run the quiz."""

import argparse
import os
import sys
from contextlib import ExitStack
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence, TextIO

from ai_generator import API_KEY_ENV, generate_deck
from ai_transport import GenerationError
from arguments import build_parser
from config import (
    DEFAULT_DECK,
    ConfigError,
    config_path_from_env,
    load_config_file,
    resolve_settings,
)
from display import format_stats, use_color
from export import build_report, write_report
from observers import AnswerLogger
from quiz_engine import QuizSession, create_quiz_mode, new_generator
from quiz_runner import run_quiz
from utils.file_handler import load_flashcards, save_deck
from utils.flashcard import FlashcardError

__all__ = ["DEFAULT_DECK", "build_parser", "main", "run"]


def run(
    argv: Optional[Sequence[str]] = None,
    ask: Optional[Callable[[str], str]] = None,
    out: Optional[TextIO] = None,
) -> int:
    """Run the command described by the arguments and return an exit code.

    Args:
        argv: Arguments to parse. Defaults to the process arguments.
        ask: Function that reads an answer. Defaults to `input`.
        out: Stream for output. Defaults to standard output.
    """
    args = build_parser().parse_args(argv)
    try:
        return _dispatch(args, ask, out)
    except (ConfigError, FlashcardError, GenerationError, OSError) as error:
        return _fail(f"Error: {error}")


def _dispatch(
    args: argparse.Namespace,
    ask: Optional[Callable[[str], str]],
    out: Optional[TextIO],
) -> int:
    """Generate a deck when asked, otherwise run the quiz."""
    if args.generate is not None:
        return _generate(args, out)
    _play(args, ask, out)
    return 0


def _generate(args: argparse.Namespace, out: Optional[TextIO]) -> int:
    """Create a deck with AI, save it, and report how many cards were written."""
    if args.save is None:
        raise GenerationError("--generate needs --save PATH to write the deck.")
    cards = generate_deck(args.generate, args.count, os.environ.get(API_KEY_ENV, ""))
    save_deck(cards, args.save)
    output = out if out is not None else sys.stdout
    output.write(f"Saved {len(cards)} cards to {args.save}\n")
    return 0


def _settings(args: argparse.Namespace) -> dict[str, Any]:
    """Resolve settings: flags, then environment, then config file, then defaults."""
    flags = {"mode": args.mode, "deck": args.file, "log_file": args.log_file}
    config = load_config_file(config_path_from_env(os.environ))
    return resolve_settings(flags, os.environ, config)


def _play(
    args: argparse.Namespace,
    ask: Optional[Callable[[str], str]],
    out: Optional[TextIO],
) -> None:
    """Load the deck, run the quiz, and produce any requested reports."""
    settings = _settings(args)
    session = _new_session(settings)
    output = out if out is not None else sys.stdout
    color = use_color(output) and not args.no_color
    _check_export_target(args.export)
    _run_with_logging(session, settings, ask, output, color)
    _report(args, settings, session, output, color)


def _new_session(settings: Mapping[str, Any]) -> QuizSession:
    """Load the deck named in the settings and start a quiz session on it."""
    cards = load_flashcards(settings["deck"])
    return QuizSession(create_quiz_mode(settings["mode"], cards, new_generator()))


def _check_export_target(path: Optional[Path]) -> None:
    """Fail before the quiz starts if the report could not be saved there."""
    if path is None:
        return
    if path.is_dir():
        raise IsADirectoryError(f"{path} is a folder, not a file")
    if not path.parent.is_dir():
        raise FileNotFoundError(f"folder does not exist: {path.parent}")


def _run_with_logging(
    session: QuizSession,
    settings: Mapping[str, Any],
    ask: Optional[Callable[[str], str]],
    output: TextIO,
    color: bool,
) -> None:
    """Run the quiz, appending each answer to the log file when one is set."""
    with ExitStack() as stack:
        if settings["log_file"] is not None:
            logger = AnswerLogger(Path(settings["log_file"]))
            session.add_observer(stack.enter_context(logger))
        run_quiz(session, ask or input, output, color)


def _report(
    args: argparse.Namespace,
    settings: Mapping[str, Any],
    session: QuizSession,
    output: TextIO,
    color: bool,
) -> None:
    """Print the summary and/or save the JSON report, as the flags request."""
    if args.stats:
        output.write(format_stats(session.stats, color) + "\n")
    if args.export is not None:
        report = build_report(session.stats, settings["mode"], str(settings["deck"]))
        write_report(report, args.export)


def _fail(message: str) -> int:
    """Print an error message to standard error and return exit code 1."""
    print(message, file=sys.stderr)
    return 1


def main() -> None:
    """Console entry point: run the CLI and exit with its status code."""
    sys.exit(run())
