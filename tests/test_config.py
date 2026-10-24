"""Tests for settings precedence: flags, environment, config file, defaults."""

import json
from pathlib import Path
from typing import Any

import pytest

from config import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_DECK,
    ConfigError,
    config_path_from_env,
    load_config_file,
    resolve_settings,
)

NO_FLAGS = {"mode": None, "deck": None, "log_file": None}


def test_defaults_apply_when_nothing_is_set() -> None:
    settings = resolve_settings(NO_FLAGS, {}, {})

    assert settings == {
        "mode": "sequential",
        "deck": str(DEFAULT_DECK),
        "log_file": None,
    }


def test_default_deck_is_the_bundled_glossary() -> None:
    assert DEFAULT_DECK.name == "glossary.json"
    assert DEFAULT_DECK.exists()


def test_config_file_overrides_defaults() -> None:
    settings = resolve_settings(NO_FLAGS, {}, {"mode": "random"})

    assert settings["mode"] == "random"


def test_environment_overrides_config_file() -> None:
    settings = resolve_settings(
        NO_FLAGS, {"FLASHCARD_MODE": "adaptive"}, {"mode": "random"}
    )

    assert settings["mode"] == "adaptive"


def test_flags_override_environment() -> None:
    flags = {**NO_FLAGS, "mode": "sequential"}

    settings = resolve_settings(flags, {"FLASHCARD_MODE": "adaptive"}, {})

    assert settings["mode"] == "sequential"


def test_unset_flags_do_not_hide_lower_sources() -> None:
    settings = resolve_settings(NO_FLAGS, {"FLASHCARD_DECK": "mine.json"}, {})

    assert settings["deck"] == "mine.json"


def test_log_file_can_be_set_by_environment_and_file() -> None:
    from_env = resolve_settings(NO_FLAGS, {"FLASHCARD_LOG_FILE": "a.log"}, {})
    from_file = resolve_settings(NO_FLAGS, {}, {"log_file": "b.log"})

    assert from_env["log_file"] == "a.log"
    assert from_file["log_file"] == "b.log"


@pytest.mark.parametrize(
    ("source", "value"),
    [
        ("flag", "hard"),
        ("env", "hard"),
        ("file", "hard"),
    ],
)
def test_invalid_mode_is_rejected_from_every_source(source: str, value: str) -> None:
    flags: dict[str, Any] = dict(NO_FLAGS)
    env: dict[str, str] = {}
    file_settings: dict[str, object] = {}
    if source == "flag":
        flags["mode"] = value
    elif source == "env":
        env["FLASHCARD_MODE"] = value
    else:
        file_settings["mode"] = value

    with pytest.raises(ConfigError, match="Unknown mode 'hard'"):
        resolve_settings(flags, env, file_settings)


def test_load_config_file_returns_empty_dict_when_missing(tmp_path: Path) -> None:
    assert load_config_file(tmp_path / "absent.json") == {}


def test_load_config_file_reads_a_valid_object(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"mode": "adaptive"}), encoding="utf-8")

    assert load_config_file(path) == {"mode": "adaptive"}


def test_load_config_file_rejects_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(ConfigError, match="Cannot read config"):
        load_config_file(path)


def test_load_config_file_rejects_a_non_object(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text("[1, 2]", encoding="utf-8")

    with pytest.raises(ConfigError, match="must be a JSON object"):
        load_config_file(path)


def test_load_config_file_rejects_unknown_keys(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"colour": "red"}), encoding="utf-8")

    with pytest.raises(ConfigError, match="Unknown config keys: colour"):
        load_config_file(path)


def test_load_config_file_reports_an_unreadable_path(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="Cannot read config"):
        load_config_file(tmp_path)


def test_config_path_comes_from_environment_or_default() -> None:
    assert config_path_from_env({"FLASHCARD_CONFIG": "x.json"}) == Path("x.json")
    assert config_path_from_env({}) == DEFAULT_CONFIG_PATH
    assert DEFAULT_CONFIG_PATH.name == "flashcard.config.json"
