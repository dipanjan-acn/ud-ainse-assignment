"""Tests for loading and validating flashcard decks."""

import json
from pathlib import Path

import pytest

from utils.file_handler import load_flashcards, parse_deck
from utils.flashcard import Flashcard, FlashcardError


def write_deck(tmp_path: Path, content: str, name: str = "deck.json") -> Path:
    """Write raw deck text to a temporary file and return its path."""
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_load_valid_flashcards_array(tmp_path: Path) -> None:
    deck = [{"front": "API", "back": "Application Programming Interface"}]
    path = write_deck(tmp_path, json.dumps(deck))

    cards = load_flashcards(path)

    assert cards == [Flashcard("API", "Application Programming Interface")]


def test_load_valid_flashcards_object_wrapper(tmp_path: Path) -> None:
    deck = {"cards": [{"front": "def", "back": "Defines a function"}]}
    path = write_deck(tmp_path, json.dumps(deck))

    cards = load_flashcards(path)

    assert cards == [Flashcard("def", "Defines a function")]


def test_load_invalid_json_raises_friendly_error(tmp_path: Path) -> None:
    path = write_deck(tmp_path, '[{"front": "A", "back": }]')

    with pytest.raises(FlashcardError, match="Invalid JSON"):
        load_flashcards(path)


def test_load_invalid_json_message_includes_line_number(tmp_path: Path) -> None:
    path = write_deck(tmp_path, '[\n  {"front": "A",\n')

    with pytest.raises(FlashcardError, match="line"):
        load_flashcards(path)


def test_load_missing_required_field_back_is_rejected(tmp_path: Path) -> None:
    path = write_deck(tmp_path, json.dumps([{"front": "A"}]))

    with pytest.raises(FlashcardError, match="'back'"):
        load_flashcards(path)


def test_load_missing_required_field_front_is_rejected(tmp_path: Path) -> None:
    path = write_deck(tmp_path, json.dumps([{"back": "B"}]))

    with pytest.raises(FlashcardError, match="'front'"):
        load_flashcards(path)


def test_error_message_names_the_bad_card_position(tmp_path: Path) -> None:
    deck = [{"front": "A", "back": "1"}, {"front": "B"}]
    path = write_deck(tmp_path, json.dumps(deck))

    with pytest.raises(FlashcardError, match="Card 2"):
        load_flashcards(path)


def test_missing_file_raises_friendly_error(tmp_path: Path) -> None:
    with pytest.raises(FlashcardError, match="File not found"):
        load_flashcards(tmp_path / "does_not_exist.json")


def test_directory_path_raises_friendly_error(tmp_path: Path) -> None:
    with pytest.raises(FlashcardError, match="not a file"):
        load_flashcards(tmp_path)


def test_non_utf8_file_raises_friendly_error(tmp_path: Path) -> None:
    path = tmp_path / "binary.json"
    path.write_bytes(b"\xff\xfe\x00bad")

    with pytest.raises(FlashcardError, match="not valid UTF-8"):
        load_flashcards(path)


def test_unreadable_file_raises_friendly_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = write_deck(tmp_path, "[]")

    def deny(self: Path, encoding: str) -> str:
        raise PermissionError("denied")

    monkeypatch.setattr(Path, "read_text", deny)

    with pytest.raises(FlashcardError, match="Cannot read"):
        load_flashcards(path)


def test_empty_array_is_rejected(tmp_path: Path) -> None:
    path = write_deck(tmp_path, "[]")

    with pytest.raises(FlashcardError, match="no cards"):
        load_flashcards(path)


def test_object_with_empty_cards_list_is_rejected(tmp_path: Path) -> None:
    path = write_deck(tmp_path, json.dumps({"cards": []}))

    with pytest.raises(FlashcardError, match="no cards"):
        load_flashcards(path)


def test_top_level_scalar_is_rejected(tmp_path: Path) -> None:
    path = write_deck(tmp_path, "42")

    with pytest.raises(FlashcardError, match="list of cards"):
        load_flashcards(path)


def test_object_without_cards_key_is_rejected(tmp_path: Path) -> None:
    path = write_deck(tmp_path, json.dumps({"items": []}))

    with pytest.raises(FlashcardError, match="list of cards"):
        load_flashcards(path)


def test_object_with_non_list_cards_is_rejected(tmp_path: Path) -> None:
    path = write_deck(tmp_path, json.dumps({"cards": "nope"}))

    with pytest.raises(FlashcardError, match="list of cards"):
        load_flashcards(path)


def test_card_that_is_not_an_object_is_rejected() -> None:
    with pytest.raises(FlashcardError, match="Card 1 must be an object"):
        parse_deck(["just a string"])


@pytest.mark.parametrize("bad_value", ["", "   ", None, 7, ["list"]])
def test_blank_or_non_text_field_is_rejected(bad_value: object) -> None:
    with pytest.raises(FlashcardError, match="'back'"):
        parse_deck([{"front": "A", "back": bad_value}])


def test_text_fields_are_trimmed() -> None:
    cards = parse_deck([{"front": "  API  ", "back": " Interface \n"}])

    assert cards == [Flashcard("API", "Interface")]


def test_extra_fields_are_ignored() -> None:
    cards = parse_deck([{"front": "A", "back": "1", "difficulty": "hard"}])

    assert cards == [Flashcard("A", "1")]


def test_flashcard_is_immutable() -> None:
    card = Flashcard("A", "1")

    with pytest.raises(AttributeError):
        card.front = "B"  # type: ignore[misc]


def test_parse_deck_accepts_array_and_wrapper_equally() -> None:
    card = {"front": "A", "back": "1"}

    assert parse_deck([card]) == parse_deck({"cards": [card]})
