"""HTTP transport for the AI service, built on urllib from the standard library.

Tests replace `post_json` with a fake, so they never reach the real service.
Error messages never include the API key.
"""

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"
TIMEOUT_SECONDS = 30.0

Transport = Callable[[str, dict[str, str], dict[str, Any], float], dict[str, Any]]


class GenerationError(Exception):
    """Raised when a deck cannot be generated."""


def auth_headers(api_key: str) -> dict[str, str]:
    """Return the authentication and version headers for the API."""
    return {"x-api-key": api_key, "anthropic-version": API_VERSION}


def decode_json(text: str) -> Any:
    """Decode JSON text, turning a decoding failure into GenerationError."""
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise GenerationError("The AI reply was not valid JSON.") from error


def post_json(
    url: str, headers: dict[str, str], body: dict[str, Any], timeout: float
) -> dict[str, Any]:
    """POST a JSON body with urllib and return the decoded JSON reply.

    Raises:
        GenerationError: On HTTP errors, network failures, timeouts, or a
            reply that is not a JSON object.
    """
    _require_https(url)
    request = _http_request(url, headers, body)
    return _decode_reply(_read_body(request, timeout))


def _require_https(url: str) -> None:
    """Refuse any URL that is not HTTPS.

    _read_body opens the URL only after this check, so file: and other schemes
    never reach urlopen.
    """
    if urllib.parse.urlsplit(url).scheme != "https":
        raise GenerationError("The AI service URL must use HTTPS.")


def _http_request(
    url: str, headers: dict[str, str], body: dict[str, Any]
) -> urllib.request.Request:
    """Build a POST request carrying a JSON body."""
    return urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={**headers, "content-type": "application/json"},
        method="POST",
    )


def _read_body(request: urllib.request.Request, timeout: float) -> str:
    """Send the request and return the reply text, translating failures."""
    try:
        with urllib.request.urlopen(request, timeout=timeout) as reply:  # nosec B310
            return _text_of(reply)
    except urllib.error.HTTPError as error:
        raise GenerationError(f"The AI service returned HTTP {error.code}.") from error
    except (urllib.error.URLError, TimeoutError) as error:
        raise GenerationError(f"Could not reach the AI service: {error}") from error


def _text_of(reply: Any) -> str:
    """Read the whole reply body as UTF-8 text."""
    raw: str = reply.read().decode("utf-8")
    return raw


def _decode_reply(raw: str) -> dict[str, Any]:
    """Decode a service reply, which must be a JSON object."""
    data = decode_json(raw)
    if not isinstance(data, dict):
        raise GenerationError("The AI reply was not a JSON object.")
    return data
