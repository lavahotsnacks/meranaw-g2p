import pytest

from meranaw_g2p.config import load_config
from meranaw_g2p.errors import ConfigError


def test_load_config_returns_valid_config():
    config = load_config("meranaw")
    assert config.language == "Meranaw"
    assert config.iso == "mrw"
    assert len(config.alphabet.graphemes) > 0
    assert len(config.alphabet.phonemes) > 0
    assert len(config.pipeline) > 0
    assert "vowel" in config.sets
    assert "consonant" in config.sets


def test_load_config_missing_language_raises():
    with pytest.raises(ConfigError):
        load_config("nonexistent")
