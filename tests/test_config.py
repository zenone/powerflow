"""Tests for configuration management."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from powerflow.config import Config, NotionConfig, PocketConfig


class TestConfig:
    """Tests for Config class."""

    def test_default_config(self):
        """New config should have sensible defaults."""
        config = Config()
        assert config.notion is not None
        assert config.pocket is not None
        # created_at is None until saved

    def test_is_configured_false_without_database(self):
        """Config should not be configured without database_id."""
        config = Config()
        assert config.is_configured is False

    def test_is_configured_true_with_database(self):
        """Config should be configured with database_id."""
        config = Config()
        config.notion.database_id = "test-db-id"
        assert config.is_configured is True

    def test_save_and_load(self):
        """Config should save and load correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"

            with patch("powerflow.config.CONFIG_FILE", config_file):
                # Create and save config
                config = Config()
                config.notion.database_id = "test-db-123"
                config.notion.database_name = "Test DB"
                config.save()

                # Load and verify
                loaded = Config.load()
                assert loaded.notion.database_id == "test-db-123"
                assert loaded.notion.database_name == "Test DB"

    def test_load_missing_file_returns_default(self):
        """Loading missing config should return defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "nonexistent.json"

            with patch("powerflow.config.CONFIG_FILE", config_file):
                config = Config.load()
                assert config.is_configured is False

    def test_update_last_sync(self):
        """update_last_sync should set timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"

            with patch("powerflow.config.CONFIG_FILE", config_file):
                config = Config()
                assert config.pocket.last_sync is None

                config.update_last_sync()
                assert config.pocket.last_sync is not None

    def test_property_map_defaults(self):
        """Property map should have expected defaults."""
        config = Config()
        prop_map = config.notion.property_map

        assert "title" in prop_map
        assert "pocket_id" in prop_map


class TestNotionConfig:
    """Tests for NotionConfig dataclass."""

    def test_default_property_map(self):
        """Should have default property mappings."""
        notion = NotionConfig()
        assert notion.property_map is not None
        assert isinstance(notion.property_map, dict)

    def test_database_id_none_by_default(self):
        """database_id should be None by default."""
        notion = NotionConfig()
        assert notion.database_id is None


class TestPocketConfig:
    """Tests for PocketConfig dataclass."""

    def test_last_sync_none_by_default(self):
        """last_sync should be None by default."""
        pocket = PocketConfig()
        assert pocket.last_sync is None
