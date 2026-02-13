"""Tests for daemon fixes (parse_interval validation, atomic state writes)."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from powerflow.daemon import DEFAULT_INTERVAL_MINUTES, load_state, parse_interval, save_state


class TestParseInterval:
    """Tests for parse_interval validation."""

    def test_valid_minutes_with_suffix(self):
        """Should parse '5m' as 5 minutes."""
        assert parse_interval("5m") == 5

    def test_valid_hours_with_suffix(self):
        """Should parse '2h' as 120 minutes."""
        assert parse_interval("2h") == 120

    def test_valid_plain_number(self):
        """Should parse '30' as 30 minutes."""
        assert parse_interval("30") == 30

    def test_empty_string_returns_default(self):
        """Empty string should return default interval."""
        assert parse_interval("") == DEFAULT_INTERVAL_MINUTES

    def test_whitespace_stripped(self):
        """Should strip whitespace from input."""
        assert parse_interval("  15m  ") == 15

    def test_case_insensitive(self):
        """Should handle uppercase suffixes."""
        assert parse_interval("5M") == 5
        assert parse_interval("1H") == 60

    def test_invalid_format_raises(self):
        """Should raise ValueError for invalid format."""
        with pytest.raises(ValueError, match="Invalid interval"):
            parse_interval("abc")

    def test_invalid_suffix_raises(self):
        """Should raise ValueError for invalid suffix."""
        with pytest.raises(ValueError, match="Invalid interval"):
            parse_interval("5x")

    def test_minimum_one_minute(self):
        """Should reject intervals less than 1 minute."""
        with pytest.raises(ValueError, match="at least 1 minute"):
            parse_interval("0m")

    def test_maximum_24_hours(self):
        """Should reject intervals more than 24 hours."""
        with pytest.raises(ValueError, match="at most 1440"):
            parse_interval("1441m")

    def test_25_hours_rejected(self):
        """Should reject 25 hours."""
        with pytest.raises(ValueError, match="at most 1440"):
            parse_interval("25h")


class TestAtomicStateWrites:
    """Tests for atomic state file writes."""

    def test_save_state_creates_file(self):
        """Should create state file if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            with (
                patch("powerflow.daemon.STATE_FILE", state_file),
                patch("powerflow.daemon.CONFIG_DIR", Path(tmpdir)),
            ):
                save_state({"status": "running"})

            assert state_file.exists()
            data = json.loads(state_file.read_text())
            assert data["status"] == "running"

    def test_save_state_no_temp_file_left(self):
        """Temp file should be cleaned up after save."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            tmp_file = state_file.with_suffix(".tmp")
            with (
                patch("powerflow.daemon.STATE_FILE", state_file),
                patch("powerflow.daemon.CONFIG_DIR", Path(tmpdir)),
            ):
                save_state({"test": "data"})

            # Temp file should not exist after successful save
            assert not tmp_file.exists()
            assert state_file.exists()

    def test_load_state_returns_empty_if_missing(self):
        """Should return empty dict if state file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "nonexistent.json"
            with patch("powerflow.daemon.STATE_FILE", state_file):
                state = load_state()

            assert state == {}

    def test_load_state_handles_corrupt_json(self):
        """Should return empty dict for corrupt JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            state_file.write_text("not valid json{{{")

            with patch("powerflow.daemon.STATE_FILE", state_file):
                state = load_state()

            assert state == {}
