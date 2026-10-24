"""Flashcard model and validation of a single card."""

from dataclasses import dataclass
from typing import Any


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
    """Return the stripped text under `key`, rejecting blank or non-text values."""
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise FlashcardError(f"Card {position} needs a non-empty '{key}' text.")
    return value.strip()
