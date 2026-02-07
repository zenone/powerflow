"""Tests for daemon functionality."""

import pytest

from powerflow.daemon import (
    parse_interval,
    DEFAULT_INTERVAL_MINUTES,
    RETRY_DELAY_SECONDS,
    MAX_RETRIES,
    send_notification,
)


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


class TestRetryConfig:
    """Tests for retry configuration."""

    def test_retry_delay_is_reasonable(self):
        """Retry delay should be short but not too aggressive."""
        assert 30 <= RETRY_DELAY_SECONDS <= 120

    def test_max_retries_is_reasonable(self):
        """Should retry a few times but not forever."""
        assert 1 <= MAX_RETRIES <= 5


class TestNotifications:
    """Tests for notification functionality."""

    def test_send_notification_does_not_raise(self):
        """Notifications should fail silently."""
        # Should not raise even with weird input
        send_notification("Test", "Message")
        send_notification("", "")
        send_notification("Quote's \"test\"", "Line\nbreak")
