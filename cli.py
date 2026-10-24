"""Command-line interface: parse arguments, load a deck, and run the quiz."""

import argparse
import random
import sys
from contextlib import ExitStack
from pathlib import Path
from typing import Any, Callable, Optional, Sequence, TextIO

from display import format_stats, use_color
from export import build_report, write_report
from observers import AnswerLogger
from quiz_engine import MODE_BUILDERS, QuizSession, create_quiz_mode
from quiz_runner import run_quiz
from utils.file_handler import load_flashcards
from utils.flashcard import FlashcardError

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DECK = PROJECT_ROOT / "data" / "glossary.json"
DEFAULT_MODE = "sequential"
DESCRIPTION = "Quiz yourself on flashcards loaded from a JSON deck."

# Each entry is (flags, keyword arguments for add_argument).
OPTIONS: list[tuple[tuple[str, ...], dict[str, Any]]] = [
    (
        ("-f", "--file"),
        {
            "type": Path,
            "default": DEFAULT_DECK,
            "help": "path to a JSON deck (default: data/glossary.json)",
        },
    ),
    (
        ("-m", "--mode"),
        {
            "choices": sorted(MODE_BUILDERS),
            "default": DEFAULT_MODE,
            "help": "order in which cards are asked (default: sequential)",
        },
    ),
    (
        ("--stats",),
        {
            "action": "store_true",
            "help": "print a session summary when the quiz ends",
        },
    ),
    (
        ("--export",),
        {
            "type": Path,
            "metavar": "PATH",
            "help": "save the session summary as a JSON report",
        },
    ),
    (
        ("--log-file",),
        {
            "type": Path,
            "metavar": "PATH",
            "help": "append one line per answer to this log file",
        },
    ),
    (
        ("--no-color",),
        {"action": "store_true", "help": "disable colored output"},
    ),
]


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser with every supported flag."""
    parser = argparse.ArgumentParser(prog="main.py", description=DESCRIPTION)
    for flags, options in OPTIONS:
        parser.add_argument(*flags, **options)
    return parser


def run(
    argv: Optional[Sequence[str]] = None,
    ask: Optional[Callable[[str], str]] = None,
    out: Optional[TextIO] = None,
) -> int:
    """Run the quiz described by the command line and return an exit code.

    Args:
        argv: Arguments to parse. Defaults to the process arguments.
        ask: Function that reads an answer. Defaults to `input`.
        out: Stream for output. Defaults to standard output.
    """
    args = build_parser().parse_args(argv)
    try:
        _play(args, ask, out)
    except (FlashcardError, OSError) as error:
        return _fail(f"Error: {error}")
    return 0


def _play(
    args: argparse.Namespace,
    ask: Optional[Callable[[str], str]],
    out: Optional[TextIO],
) -> None:
    """Load the deck, run the quiz, and produce any requested reports."""
    cards = load_flashcards(args.file)
    output = out if out is not None else sys.stdout
    session = QuizSession(create_quiz_mode(args.mode, cards, random.Random()))
    color = use_color(output) and not args.no_color
    _check_export_target(args.export)
    _run_with_logging(session, args, ask, output, color)
    _report(args, session, output, color)


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
    args: argparse.Namespace,
    ask: Optional[Callable[[str], str]],
    output: TextIO,
    color: bool,
) -> None:
    """Run the quiz, appending each answer to the log file when one is given."""
    with ExitStack() as stack:
        if args.log_file is not None:
            session.add_observer(stack.enter_context(AnswerLogger(args.log_file)))
        run_quiz(session, ask or input, output, color)


def _report(
    args: argparse.Namespace,
    session: QuizSession,
    output: TextIO,
    color: bool,
) -> None:
    """Print the summary and/or save the JSON report, as the flags request."""
    if args.stats:
        output.write(format_stats(session.stats, color) + "\n")
    if args.export is not None:
        report = build_report(session.stats, args.mode, str(args.file))
        write_report(report, args.export)


def _fail(message: str) -> int:
    """Print an error message to standard error and return exit code 1."""
    print(message, file=sys.stderr)
    return 1


def main() -> None:
    """Console entry point: run the CLI and exit with its status code."""
    sys.exit(run())
