"""Command-line flags: the parser definition, kept apart from the run logic."""

import argparse
from pathlib import Path
from typing import Any

from ai_generator import API_KEY_ENV
from quiz_engine import MODE_BUILDERS

DESCRIPTION = "Quiz yourself on flashcards loaded from a JSON deck."
DEFAULT_COUNT = 10

# Each entry is (flags, keyword arguments for add_argument).
OPTIONS: list[tuple[tuple[str, ...], dict[str, Any]]] = [
    (
        ("-f", "--file"),
        {
            "type": Path,
            "help": "JSON deck to quiz on (default: config, then data/glossary.json)",
        },
    ),
    (
        ("-m", "--mode"),
        {
            "choices": sorted(MODE_BUILDERS),
            "help": "order in which cards are asked (default: sequential)",
        },
    ),
    (
        ("--stats",),
        {"action": "store_true", "help": "print a session summary when the quiz ends"},
    ),
    (
        ("--export",),
        {"type": Path, "metavar": "PATH", "help": "save the session summary as JSON"},
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
    (
        ("--generate",),
        {
            "metavar": "TOPIC",
            "help": f"create a deck about TOPIC with AI, using {API_KEY_ENV}; "
            "needs --save",
        },
    ),
    (
        ("--count",),
        {
            "type": int,
            "default": DEFAULT_COUNT,
            "metavar": "N",
            "help": f"cards to generate (default: {DEFAULT_COUNT})",
        },
    ),
    (
        ("--save",),
        {"type": Path, "metavar": "PATH", "help": "file to write a generated deck to"},
    ),
]


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser with every supported flag."""
    parser = argparse.ArgumentParser(prog="main.py", description=DESCRIPTION)
    for flags, options in OPTIONS:
        parser.add_argument(*flags, **options)
    return parser
