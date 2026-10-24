"""Tests for size limits on deck files and individual cards."""

import json
from pathlib import Path

import pytest

from utils import file_handler
from utils.file_handler import load_flashcards
from utils.flashcard import FlashcardError, flashcard_from_dict


def test_deck_file_over_the_byte_limit_is_rejected_before_parsing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(file_handler, "MAX_DECK_BYTES", 40)
    path = tmp_path / "big.json"
    path.write_text(json.dumps([{"front": "a" * 30, "back": "b"}]))

    with pytest.raises(FlashcardError, match="too large"):
        load_flashcards(path)


def test_deck_file_at_the_byte_limit_is_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text = json.dumps([{"front": "a", "back": "b"}])
    monkeypatch.setattr(file_handler, "MAX_DECK_BYTES", len(text.encode()))
    path = tmp_path / "exact.json"
    path.write_text(text)

    assert len(load_flashcards(path)) == 1


def test_default_byte_limit_is_one_megabyte() -> None:
    assert file_handler.MAX_DECK_BYTES == 1_000_000


def test_card_text_over_the_character_limit_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("utils.flashcard.MAX_CARD_CHARS", 10)

    with pytest.raises(FlashcardError, match="10 characters"):
        flashcard_from_dict({"front": "x" * 11, "back": "ok"}, 1)


def test_back_text_over_the_character_limit_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("utils.flashcard.MAX_CARD_CHARS", 10)

    with pytest.raises(FlashcardError, match="'back'"):
        flashcard_from_dict({"front": "ok", "back": "y" * 11}, 1)


def test_card_text_at_the_character_limit_is_accepted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("utils.flashcard.MAX_CARD_CHARS", 10)

    card = flashcard_from_dict({"front": "x" * 10, "back": "y"}, 1)

    assert card.front == "x" * 10


def test_default_character_limit_is_500() -> None:
    from utils.flashcard import MAX_CARD_CHARS

    assert MAX_CARD_CHARS == 500
