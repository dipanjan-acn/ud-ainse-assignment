"""Read and validate flashcard decks stored as JSON files."""

import json
from pathlib import Path
from typing import Any

from utils.flashcard import Flashcard, FlashcardError, flashcard_from_dict

SHAPE_ERROR = "The deck must be a list of cards or an object with a 'cards' list."


def load_flashcards(path: str | Path) -> list[Flashcard]:
    """Load and validate every card in a JSON deck file.

    Args:
        path: Path to a deck file in array or object format.

    Returns:
        The validated flashcards, in file order.

    Raises:
        FlashcardError: If the file is missing, unreadable, or invalid.
    """
    deck_path = Path(path)
    return parse_deck(_read_json(deck_path))


def parse_deck(data: Any) -> list[Flashcard]:
    """Convert decoded JSON into flashcards.

    Accepts either a bare list of cards or an object with a 'cards' list.

    Raises:
        FlashcardError: If the structure is wrong or the deck is empty.
    """
    raw_cards = _extract_card_list(data)
    if not raw_cards:
        raise FlashcardError("The deck has no cards.")
    return [
        flashcard_from_dict(item, position)
        for position, item in enumerate(raw_cards, start=1)
    ]


def _extract_card_list(data: Any) -> list[Any]:
    """Return the raw card list from either supported deck shape."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("cards"), list):
        cards: list[Any] = data["cards"]
        return cards
    raise FlashcardError(SHAPE_ERROR)


def _read_json(path: Path) -> Any:
    """Read a file and decode its JSON content."""
    text = _read_text(path)
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise FlashcardError(
            f"Invalid JSON in {path.name} at line {error.lineno}: {error.msg}."
        ) from error


def _read_text(path: Path) -> str:
    """Read a UTF-8 text file, translating read failures into FlashcardError."""
    if path.is_dir():
        raise FlashcardError(f"{path} is not a file.")
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise _read_failure(path, error) from error


def _read_failure(path: Path, error: Exception) -> FlashcardError:
    """Describe why a file could not be read, in plain language."""
    if isinstance(error, FileNotFoundError):
        return FlashcardError(f"File not found: {path}.")
    if isinstance(error, UnicodeDecodeError):
        return FlashcardError(f"{path.name} is not valid UTF-8 text.")
    return FlashcardError(f"Cannot read {path.name}: {error}.")
