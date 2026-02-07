"""Tests for daemon functionality."""

import pytest

from powerflow.daemon import parse_interval, DEFAULT_INTERVAL_MINUTES


class TestParseInterval:
    """Tests for interval parsing."""

    def test_minutes_with_suffix(self):
        assert parse_interval("5m") == 5
        assert parse_interval("15m") == 15
        assert parse_interval("30m") == 30

    def test_hours_with_suffix(self):
        assert parse_interval("1h") == 60
        assert parse_interval("2h") == 120

    def test_plain_number_as_minutes(self):
        assert parse_interval("15") == 15
        assert parse_interval("30") == 30

    def test_case_insensitive(self):
        assert parse_interval("15M") == 15
        assert parse_interval("1H") == 60

    def test_with_whitespace(self):
        assert parse_interval("  15m  ") == 15

    def test_default_interval(self):
        assert DEFAULT_INTERVAL_MINUTES == 15
