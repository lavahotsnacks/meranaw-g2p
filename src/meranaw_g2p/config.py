import os
from typing import Any

import yaml

from meranaw_g2p.errors import ConfigError
from meranaw_g2p.models import LanguageAlphabet, LanguageConfig


def resolve_language_directory(lang_code: str) -> str:
    """Resolve path to a language's bundled data directory (data/{lang_code}/)."""
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(pkg_dir, "data", lang_code)


def _parse_config(raw: dict[str, Any]) -> LanguageConfig:
    """Convert a parsed YAML dict into a structured LanguageConfig."""
    raw_alphabet = raw.get("alphabet", {})
    alphabet = LanguageAlphabet(
        graphemes=raw_alphabet.get("graphemes", []),
        phonemes=raw_alphabet.get("phonemes", []),
        special_symbols=raw_alphabet.get("special_symbols", []),
    )
    return LanguageConfig(
        language=raw.get("language", ""),
        iso=raw.get("iso", ""),
        alphabet=alphabet,
        sets=raw.get("sets", {}),
        pipeline=raw.get("pipeline", []),
    )


def load_config(lang_code: str) -> LanguageConfig:
    """Load and validate a language.yaml file from the bundled data directory.

    Raises ConfigError if the file is missing or cannot be parsed.
    """
    lang_dir = resolve_language_directory(lang_code)
    config_path = os.path.join(lang_dir, "language.yaml")

    if not os.path.exists(config_path):
        raise ConfigError(
            f"Language configuration not found: {config_path}"
        )

    try:
        with open(config_path, encoding="utf-8") as f:
            raw: dict[str, Any] = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse {config_path}: {e}") from e

    if not isinstance(raw, dict):
        raise ConfigError(f"Expected a YAML mapping in {config_path}")

    return _parse_config(raw)
