"""Tests for InternalSettings repositories"""

import pytest
import yaml
from parkbot.dao_impl.config.internal_settings_impl import (
    YamlInternalSettingsRepository,
    InMemoryInternalSettingsRepository,
)
from parkbot.config.models import InternalSettings
from parkbot.core.exceptions import ConfigError


class TestYamlInternalSettingsRepository:
    """Test YAML internal settings repository"""

    @pytest.fixture
    def config_file(self, tmp_path):
        """Create a temporary config file"""
        path = tmp_path / "settings.yaml"
        return path

    def test_get_missing_file_raises_error(self, config_file):
        """Test that missing file raises ConfigError"""
        repo = YamlInternalSettingsRepository(str(config_file))
        with pytest.raises(
            ConfigError, match="YAML file for internal system setting is missing"
        ):
            repo.get()

    def test_get_empty_file_raises_error(self, config_file):
        """Test that empty file raises ConfigError"""
        config_file.write_text("")
        repo = YamlInternalSettingsRepository(str(config_file))
        with pytest.raises(ConfigError, match="data is empty"):
            repo.get()

    def get_full_settings(self):
        return {
            "browser_user_data_dir": "data",
            "browser_win_width": 800,
            "browser_win_height": 600,
            "logging_level": "INFO",
            "logging_dir": "logs",
            "win_title": "Title",
            "win_width": 800,
            "win_height": 600,
            "win_min_width": 400,
            "win_min_height": 300,
            "appearance_mode": "System",
            "color_theme": "blue",
        }

    def test_get_success(self, config_file):
        """Test successful get"""
        data = self.get_full_settings()
        with open(config_file, "w") as f:
            yaml.dump(data, f)

        repo = YamlInternalSettingsRepository(str(config_file))
        settings = repo.get()
        assert settings.browser_user_data_dir == "data"

    def test_save_success(self, config_file):
        """Test save"""
        repo = YamlInternalSettingsRepository(str(config_file))
        settings = InternalSettings(**self.get_full_settings())
        repo.save(settings)

        assert config_file.exists()
        with open(config_file, "r") as f:
            data = yaml.safe_load(f)
            assert data["browser_user_data_dir"] == "data"


class TestInMemoryInternalSettingsRepository:
    """Test In-Memory internal settings repository"""

    @pytest.fixture
    def config_file(self, tmp_path):
        """Create a temporary config file"""
        path = tmp_path / "settings.yaml"
        data = {
            "browser_user_data_dir": "data",
            "browser_win_width": 800,
            "browser_win_height": 600,
            "logging_level": "INFO",
            "logging_dir": "logs",
            "win_title": "Title",
            "win_width": 800,
            "win_height": 600,
            "win_min_width": 400,
            "win_min_height": 300,
            "appearance_mode": "System",
            "color_theme": "blue",
        }
        with open(path, "w") as f:
            yaml.dump(data, f)
        return path

    def test_init_missing_file_raises_error(self):
        """Test init with empty/missing file"""
        with pytest.raises(ConfigError, match="initial yaml setting file missing"):
            InMemoryInternalSettingsRepository("")

    def test_init_success(self, config_file):
        """Test initialization loads settings"""
        repo = InMemoryInternalSettingsRepository(str(config_file))
        settings = repo.get()
        assert settings.browser_user_data_dir == "data"

    def test_save_and_get(self, config_file):
        """Test save and get in-memory"""
        repo = InMemoryInternalSettingsRepository(str(config_file))

        new_data = {
            "browser_user_data_dir": "new_data",
            "browser_win_width": 1000,
            "browser_win_height": 800,
            "logging_level": "DEBUG",
            "logging_dir": "logs",
            "win_title": "New Title",
            "win_width": 1000,
            "win_height": 800,
            "win_min_width": 500,
            "win_min_height": 400,
            "appearance_mode": "Dark",
            "color_theme": "green",
        }
        new_settings = InternalSettings(**new_data)
        repo.save(new_settings)

        settings = repo.get()
        assert settings.browser_user_data_dir == "new_data"
