"""Flashcard model and validation of a single card."""

from dataclasses import dataclass
from typing import Any

# Longest allowed front or back text, after trimming spaces.
MAX_CARD_CHARS = 500


class FlashcardError(ValueError):
    """Raised when a deck cannot be loaded or a card is invalid."""


@dataclass(frozen=True)
class Flashcard:
    """A question (front) and its expected answer (back)."""

    front: str
    back: str


def flashcard_from_dict(data: Any, position: int) -> Flashcard:
    """Build a Flashcard from one decoded JSON object.

    Args:
        data: The decoded card. Must be a dict with 'front' and 'back'.
        position: The card's 1-based position, used in error messages.

    Raises:
        FlashcardError: If the card is not an object or a field is invalid.
    """
    if not isinstance(data, dict):
        raise FlashcardError(f"Card {position} must be an object.")
    return Flashcard(
        front=_required_text(data, "front", position),
        back=_required_text(data, "back", position),
    )


def _required_text(data: dict[str, Any], key: str, position: int) -> str:
    """Return the stripped text under `key`, rejecting bad values."""
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise FlashcardError(f"Card {position} needs a non-empty '{key}' text.")
    text = value.strip()
    if len(text) > MAX_CARD_CHARS:
        raise _too_long(position, key)
    return text


def _too_long(position: int, key: str) -> FlashcardError:
    """Describe a card field that exceeds MAX_CARD_CHARS."""
    return FlashcardError(
        f"Card {position} '{key}' is longer than {MAX_CARD_CHARS} characters."
    )
