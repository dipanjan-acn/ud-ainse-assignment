"""AI-assisted deck generation: build the request, then parse the reply.

The network call itself lives in ai_transport.py, so this module can be tested
with a fake transport. Error messages never include the API key.
"""

from typing import Any, Optional

from ai_transport import (
    API_URL,
    TIMEOUT_SECONDS,
    GenerationError,
    Transport,
    auth_headers,
    decode_json,
    post_json,
)
from utils.file_handler import parse_deck
from utils.flashcard import Flashcard, FlashcardError

MODEL = "claude-haiku-5-5"
API_KEY_ENV = "ANTHROPIC_API_KEY"
MAX_TOKENS = 2048
MAX_TOPIC_CHARS = 100
MIN_COUNT = 1
MAX_COUNT = 50
_COUNT_MESSAGE = f"The count must be a whole number from {MIN_COUNT} to {MAX_COUNT}."


def generate_deck(
    topic: str,
    count: int,
    api_key: str,
    transport: Optional[Transport] = None,
) -> list[Flashcard]:
    """Ask the AI service for `count` flashcards about `topic`.

    Raises:
        GenerationError: If the request is invalid, the service cannot be
            reached, or its reply is not a valid deck.
    """
    clean_topic = _checked_topic(topic)
    _checked_count(count)
    if not api_key:
        raise GenerationError(f"Set {API_KEY_ENV} to generate a deck with AI.")
    reply = _request_reply(clean_topic, count, api_key, transport)
    return cards_from_text(extract_text(reply))


def _request_reply(
    topic: str, count: int, api_key: str, transport: Optional[Transport]
) -> dict[str, Any]:
    """Send the request through the transport, or the default HTTP client."""
    send = transport if transport is not None else post_json
    return send(
        API_URL, auth_headers(api_key), build_request(topic, count), TIMEOUT_SECONDS
    )


def build_request(topic: str, count: int) -> dict[str, Any]:
    """Build the Messages API request body for a deck of `count` cards."""
    prompt = _prompt(" ".join(topic.split()), count)
    return {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "messages": [{"role": "user", "content": prompt}],
    }


def _prompt(topic: str, count: int) -> str:
    """Return the instruction that asks for a JSON array of cards."""
    return (
        f"Write {count} flashcards about {topic}. Reply with only a JSON "
        "array of objects, each with a 'front' (a question or term) and a "
        "'back' (the answer). Do not add any other text."
    )


def extract_text(reply: dict[str, Any]) -> str:
    """Join the text blocks of a Messages API reply.

    Raises:
        GenerationError: If the reply has no text blocks.
    """
    texts = _text_blocks(reply.get("content"))
    if not texts:
        raise GenerationError("The AI reply had no text.")
    return "".join(texts)


def _text_blocks(content: Any) -> list[str]:
    """Return the text of each block whose type is 'text'."""
    if not isinstance(content, list):
        return []
    return [
        block.get("text", "")
        for block in content
        if isinstance(block, dict) and block.get("type") == "text"
    ]


def cards_from_text(text: str) -> list[Flashcard]:
    """Parse the model's text as a deck, ignoring a surrounding code fence.

    Raises:
        GenerationError: If the text is not JSON or does not form a valid deck.
    """
    data = decode_json(_strip_fence(text.strip()))
    try:
        return parse_deck(data)
    except FlashcardError as error:
        raise GenerationError(str(error)) from error


def _checked_topic(topic: str) -> str:
    """Trim the topic and check that its length is allowed."""
    clean = " ".join(topic.split())
    if not clean or len(clean) > MAX_TOPIC_CHARS:
        raise GenerationError(f"The topic must be 1 to {MAX_TOPIC_CHARS} characters.")
    return clean


def _checked_count(count: int) -> None:
    """Check that the card count is a whole number in the allowed range."""
    is_whole = isinstance(count, int) and not isinstance(count, bool)
    if not (is_whole and MIN_COUNT <= count <= MAX_COUNT):
        raise GenerationError(_COUNT_MESSAGE)


def _strip_fence(text: str) -> str:
    """Remove a Markdown code fence around JSON, if the model added one."""
    if not text.startswith("```"):
        return text
    lines = text.splitlines()[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines)
