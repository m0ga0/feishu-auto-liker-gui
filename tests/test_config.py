"""Tests for config module - tests behavior not internal implementation."""

import yaml
import pytest

from src.config import load_config, save_config, DEFAULT_CONFIG


class TestConfigModule:
    """Test config module behavior through public interface."""

    @pytest.fixture(autouse=True)
    def temp_config(self, tmp_path, monkeypatch):
        """Use temp config file for tests."""
        from src import config

        # Save original paths
        orig_config = config.CONFIG_PATH
        orig_state = config.STATE_PATH

        # Set temp paths
        config.CONFIG_PATH = tmp_path / "config.yaml"
        config.STATE_PATH = tmp_path / "state.json"

        yield

        # Restore
        config.CONFIG_PATH = orig_config
        config.STATE_PATH = orig_state

    def test_load_config_returns_defaults_when_file_not_exists(self, tmp_path):
        """When config.yaml doesn't exist, should return DEFAULT_CONFIG."""
        from src import config

        # Ensure file doesn't exist
        config.CONFIG_PATH = tmp_path / "nonexistent.yaml"
        result = load_config()
        assert result == DEFAULT_CONFIG

    def test_load_config_returns_actual_config_when_file_exists(self, tmp_path):
        """When config.yaml exists, should return its contents."""
        from src import config

        test_config = {"monitor": {"patterns": ["test"]}}
        config.CONFIG_PATH.write_text(yaml.dump(test_config))

        result = load_config()

        assert result == test_config

    def test_save_config_writes_to_file(self, tmp_path):
        """save_config should write to config.yaml."""
        from src import config

        test_config = {"monitor": {"patterns": ["test"]}}

        save_config(test_config)

        assert config.CONFIG_PATH.exists()
        loaded = yaml.safe_load(config.CONFIG_PATH.read_text())
        assert loaded == test_config

    def test_save_and_load_roundtrip(self):
        """save then load should preserve data."""
        test_config = {
            "monitor": {
                "patterns": ["re:.*test.*"],
                "check_interval": 5,
            },
            "anti_detect": {
                "min_delay": 1.0,
                "max_delay": 3.0,
            },
        }

        save_config(test_config)
        loaded = load_config()

        assert loaded["monitor"]["patterns"] == ["re:.*test.*"]
        assert loaded["monitor"]["check_interval"] == 5
        assert loaded["anti_detect"]["min_delay"] == 1.0

    def test_default_config_structure(self):
        """DEFAULT_CONFIG should have expected keys."""
        assert "monitor" in DEFAULT_CONFIG
        assert "notification" in DEFAULT_CONFIG
        assert "anti_detect" in DEFAULT_CONFIG
        assert "browser" in DEFAULT_CONFIG
        assert "log" in DEFAULT_CONFIG

    def test_default_monitor_config(self):
        """Default monitor config should be valid."""
        monitor = DEFAULT_CONFIG["monitor"]
        assert "patterns" in monitor
        assert isinstance(monitor["patterns"], list)
        assert "check_interval" in monitor
        assert isinstance(monitor["check_interval"], int)

    def test_default_anti_detect_config(self):
        """Default anti-detect config should be valid."""
        anti = DEFAULT_CONFIG["anti_detect"]
        assert "min_delay" in anti
        assert "max_delay" in anti
        assert float(anti["min_delay"]) < float(anti["max_delay"])  # type: ignore
