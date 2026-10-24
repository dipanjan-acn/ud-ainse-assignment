"""Tests for AI-assisted deck generation, with the network replaced by fakes."""

import io
import json
import urllib.error
import urllib.request
from email.message import Message
from pathlib import Path
from typing import Any

import pytest

import ai_generator
import ai_transport
from ai_generator import (
    build_request,
    cards_from_text,
    extract_text,
    generate_deck,
)
from ai_transport import API_URL, GenerationError, post_json
from utils.file_handler import load_flashcards, save_deck
from utils.flashcard import Flashcard

SECRET = "sk-test-secret-value"
CARDS_JSON = json.dumps([{"front": "TCP", "back": "Transmission Control Protocol"}])


def reply(text: str) -> dict[str, Any]:
    """Build a Messages API reply that contains one text block."""
    return {"content": [{"type": "text", "text": text}]}


class FakeTransport:
    """Records the request it receives and returns a canned reply."""

    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, str], dict[str, Any], float]] = []

    def __call__(
        self, url: str, headers: dict[str, str], body: dict[str, Any], timeout: float
    ) -> dict[str, Any]:
        self.calls.append((url, headers, body, timeout))
        return self.response


def test_generate_deck_returns_cards_from_the_reply() -> None:
    transport = FakeTransport(reply(CARDS_JSON))

    cards = generate_deck("networking", 1, SECRET, transport)

    assert cards == [Flashcard("TCP", "Transmission Control Protocol")]


def test_generate_deck_sends_the_key_in_a_header_not_the_body() -> None:
    transport = FakeTransport(reply(CARDS_JSON))

    generate_deck("networking", 1, SECRET, transport)

    url, headers, body, timeout = transport.calls[0]
    assert url == API_URL
    assert headers["x-api-key"] == SECRET
    assert SECRET not in json.dumps(body)
    assert timeout == ai_transport.TIMEOUT_SECONDS


def test_request_body_names_the_model_and_the_topic() -> None:
    body = build_request("  Linux   networking ", 5)

    assert body["model"] == ai_generator.MODEL
    assert (
        "Write 5 flashcards about Linux networking." in body["messages"][0]["content"]
    )


def test_missing_key_error_names_the_variable_but_not_a_value() -> None:
    with pytest.raises(GenerationError, match="ANTHROPIC_API_KEY"):
        generate_deck("networking", 1, "", FakeTransport(reply(CARDS_JSON)))


@pytest.mark.parametrize("topic", ["", "   ", "x" * 101])
def test_blank_or_long_topic_is_rejected(topic: str) -> None:
    with pytest.raises(GenerationError, match="topic"):
        generate_deck(topic, 1, SECRET, FakeTransport(reply(CARDS_JSON)))


@pytest.mark.parametrize("count", [0, 51, "5", True])
def test_count_outside_the_allowed_range_is_rejected(count: Any) -> None:
    with pytest.raises(GenerationError, match="count"):
        generate_deck("networking", count, SECRET, FakeTransport(reply(CARDS_JSON)))


def test_reply_without_text_is_rejected() -> None:
    with pytest.raises(GenerationError, match="no text"):
        extract_text({"content": [{"type": "tool_use"}]})


def test_reply_with_no_content_list_is_rejected() -> None:
    with pytest.raises(GenerationError, match="no text"):
        extract_text({"content": "oops"})


def test_text_blocks_are_joined_in_order() -> None:
    response = {
        "content": [
            {"type": "text", "text": "[{"},
            {"type": "text", "text": "}]"},
        ]
    }

    assert extract_text(response) == "[{}]"


def test_non_json_reply_is_rejected() -> None:
    with pytest.raises(GenerationError, match="not valid JSON"):
        cards_from_text("Sure! Here are your cards:")


def test_code_fenced_json_is_accepted() -> None:
    fenced = f"```json\n{CARDS_JSON}\n```"

    assert cards_from_text(fenced) == [
        Flashcard("TCP", "Transmission Control Protocol")
    ]


def test_reply_can_be_an_object_with_a_cards_list() -> None:
    text = json.dumps({"cards": json.loads(CARDS_JSON)})

    assert len(cards_from_text(text)) == 1


def test_empty_list_from_the_model_is_rejected() -> None:
    with pytest.raises(GenerationError, match="no cards"):
        cards_from_text("[]")


def test_invalid_card_from_the_model_is_reported() -> None:
    with pytest.raises(GenerationError, match="'back'"):
        cards_from_text(json.dumps([{"front": "TCP"}]))


def test_post_json_returns_the_decoded_reply(monkeypatch: pytest.MonkeyPatch) -> None:
    class Reply(io.BytesIO):
        def __enter__(self) -> "Reply":
            return self

        def __exit__(self, *args: object) -> None:
            return None

    monkeypatch.setattr(
        urllib.request, "urlopen", lambda *a, **k: Reply(b'{"ok": true}')
    )

    assert post_json(API_URL, {}, {}, 1.0) == {"ok": True}


def test_post_json_reports_an_http_error_without_the_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def refuse(*args: object, **kwargs: object) -> None:
        raise urllib.error.HTTPError(API_URL, 401, "unauthorized", Message(), None)

    monkeypatch.setattr(urllib.request, "urlopen", refuse)

    with pytest.raises(GenerationError, match="HTTP 401") as info:
        post_json(API_URL, {"x-api-key": SECRET}, {}, 1.0)

    assert SECRET not in str(info.value)


def test_post_json_reports_a_network_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def offline(*args: object, **kwargs: object) -> None:
        raise urllib.error.URLError("no route")

    monkeypatch.setattr(urllib.request, "urlopen", offline)

    with pytest.raises(GenerationError, match="Could not reach"):
        post_json(API_URL, {}, {}, 1.0)


def test_post_json_reports_a_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def slow(*args: object, **kwargs: object) -> None:
        raise TimeoutError("timed out")

    monkeypatch.setattr(urllib.request, "urlopen", slow)

    with pytest.raises(GenerationError, match="Could not reach"):
        post_json(API_URL, {}, {}, 1.0)


def test_post_json_rejects_a_reply_that_is_not_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Reply(io.BytesIO):
        def __enter__(self) -> "Reply":
            return self

        def __exit__(self, *args: object) -> None:
            return None

    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: Reply(b"<html>"))

    with pytest.raises(GenerationError, match="not valid JSON"):
        post_json(API_URL, {}, {}, 1.0)


def test_save_deck_writes_a_deck_that_loads_back(tmp_path: Path) -> None:
    cards = [Flashcard("TCP", "Transmission Control Protocol")]
    path = tmp_path / "generated.json"

    save_deck(cards, path)

    assert load_flashcards(path) == cards


def test_fence_without_closing_marker_is_still_parsed() -> None:
    unclosed = f"```json\n{CARDS_JSON}"

    assert len(cards_from_text(unclosed)) == 1


def test_service_reply_that_is_not_an_object_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Reply(io.BytesIO):
        def __enter__(self) -> "Reply":
            return self

        def __exit__(self, *args: object) -> None:
            return None

    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: Reply(b"[1, 2]"))

    with pytest.raises(GenerationError, match="not a JSON object"):
        post_json(API_URL, {}, {}, 1.0)


@pytest.mark.parametrize(
    "url", ["http://api.example.com", "file:///etc/passwd", "ftp://x"]
)
def test_post_json_refuses_non_https_urls(
    url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    def must_not_open(*args: object, **kwargs: object) -> None:
        raise AssertionError("urlopen must not be called")

    monkeypatch.setattr(urllib.request, "urlopen", must_not_open)

    with pytest.raises(GenerationError, match="must use HTTPS"):
        post_json(url, {}, {}, 1.0)
