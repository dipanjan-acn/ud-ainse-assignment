"""Quiz settings from flags, environment variables, a config file, and defaults.

Precedence, highest first: command-line flags, environment variables, the JSON
config file, then the built-in defaults. A flag that was not given is None and
does not hide the lower sources.
"""

import json
from pathlib import Path
from typing import Any, Mapping

from quiz_engine import MODE_BUILDERS

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DECK = PROJECT_ROOT / "data" / "glossary.json"
DEFAULT_CONFIG_PATH = Path("flashcard.config.json")
CONFIG_PATH_ENV = "FLASHCARD_CONFIG"
DEFAULTS: dict[str, Any] = {
    "mode": "sequential",
    "deck": str(DEFAULT_DECK),
    "log_file": None,
}
ENV_NAMES = {
    "FLASHCARD_MODE": "mode",
    "FLASHCARD_DECK": "deck",
    "FLASHCARD_LOG_FILE": "log_file",
}


class ConfigError(ValueError):
    """Raised when a setting or the config file is invalid."""


def config_path_from_env(env: Mapping[str, str]) -> Path:
    """Return the config file path, from FLASHCARD_CONFIG or the default."""
    if CONFIG_PATH_ENV in env:
        return Path(env[CONFIG_PATH_ENV])
    return DEFAULT_CONFIG_PATH


def load_config_file(path: Path) -> dict[str, Any]:
    """Read the JSON config file. A missing file means no file settings.

    Raises:
        ConfigError: If the file is unreadable, not a JSON object, or has
            keys the app does not know.
    """
    if not path.exists():
        return {}
    data = _read_config(path)
    unknown = sorted(set(data) - set(DEFAULTS))
    if unknown:
        raise ConfigError(f"Unknown config keys: {', '.join(unknown)}.")
    return data


def _read_config(path: Path) -> dict[str, Any]:
    """Decode the config file and check that it holds a JSON object."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ConfigError(f"Cannot read config {path.name}: {error}") from error
    if not isinstance(data, dict):
        raise ConfigError(f"Config {path.name} must be a JSON object.")
    return data


def resolve_settings(
    flags: Mapping[str, Any],
    env: Mapping[str, str],
    file_settings: Mapping[str, Any],
) -> dict[str, Any]:
    """Combine the four sources into one settings dictionary.

    Raises:
        ConfigError: If the resulting quiz mode is not registered.
    """
    settings = {**DEFAULTS, **file_settings}
    settings.update({key: env[name] for name, key in ENV_NAMES.items() if name in env})
    settings.update({key: value for key, value in flags.items() if value is not None})
    _check_mode(settings["mode"])
    return settings


def _check_mode(mode: str) -> None:
    """Reject a quiz mode that the factory does not know."""
    if mode not in MODE_BUILDERS:
        choices = ", ".join(MODE_BUILDERS)
        raise ConfigError(f"Unknown mode '{mode}'. Choose from: {choices}.")
