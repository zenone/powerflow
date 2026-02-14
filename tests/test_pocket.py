"""Tests for Pocket API client."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import requests

from powerflow.pocket import POCKET_RETRY_CONFIG, PocketClient, parse_datetime


class TestPocketClient:
    """Tests for PocketClient class."""

    def test_init_sets_headers(self):
        """Client should set authorization headers."""
        client = PocketClient("test-api-key")
        assert "Authorization" in client.session.headers
        assert "Bearer test-api-key" in client.session.headers["Authorization"]

    def test_init_uses_rate_limiter(self):
        """Client should have a rate limiter."""
        client = PocketClient("test-api-key")
        assert client._rate_limiter is not None

    def test_timeout_default(self):
        """Default timeout should be 30 seconds."""
        client = PocketClient("test-api-key")
        assert client.timeout == 30.0

    def test_timeout_custom(self):
        """Should accept custom timeout."""
        client = PocketClient("test-api-key", timeout=60.0)
        assert client.timeout == 60.0


class TestPocketRetryConfig:
    """Tests for Pocket retry configuration."""

    def test_max_attempts(self):
        """Should retry 3 times by default."""
        assert POCKET_RETRY_CONFIG.max_attempts == 3

    def test_retriable_codes(self):
        """Should retry on expected status codes."""
        assert 429 in POCKET_RETRY_CONFIG.retriable_status_codes
        assert 500 in POCKET_RETRY_CONFIG.retriable_status_codes


class TestParseDatetime:
    """Tests for parse_datetime helper."""

    def test_parse_iso_format(self):
        """Should parse standard ISO format."""
        result = parse_datetime("2026-02-14T10:30:00Z")
        assert result is not None
        assert result.year == 2026
        assert result.month == 2
        assert result.day == 14
        assert result.tzinfo is not None

    def test_parse_with_timezone(self):
        """Should handle explicit timezone."""
        result = parse_datetime("2026-02-14T10:30:00+00:00")
        assert result is not None
        assert result.tzinfo is not None

    def test_parse_none_returns_none(self):
        """Should return None for None input."""
        assert parse_datetime(None) is None

    def test_parse_empty_returns_none(self):
        """Should return None for empty string."""
        assert parse_datetime("") is None

    def test_parse_invalid_returns_none(self):
        """Should return None for invalid format."""
        assert parse_datetime("not-a-date") is None


class TestPocketClientMethods:
    """Tests for PocketClient API methods."""

    def test_get_recordings_list(self):
        """Should return recordings list."""
        client = PocketClient("test-key")
        client._request = MagicMock(return_value={
            "data": [
                {"id": "rec1", "title": "Recording 1"},
                {"id": "rec2", "title": "Recording 2"},
            ]
        })

        results = client.get_recordings_list(limit=10)
        assert len(results) == 2
        client._request.assert_called_once()

    def test_get_recording_details(self):
        """Should return recording details."""
        client = PocketClient("test-key")
        client._request = MagicMock(return_value={
            "data": {
                "id": "rec1",
                "title": "Test Recording",
                "summarizations": {
                    "v2_summary": {"markdown": "Test summary"},
                }
            }
        })

        result = client.get_recording_details("rec1")
        assert result["id"] == "rec1"

    def test_test_connection_success(self):
        """test_connection should return True on success."""
        client = PocketClient("test-key")
        client.get_recordings_list = MagicMock(return_value=[])

        assert client.test_connection() is True

    def test_test_connection_failure(self):
        """test_connection should return False on failure."""
        client = PocketClient("test-key")
        client.get_recordings_list = MagicMock(
            side_effect=requests.RequestException("Connection failed")
        )

        assert client.test_connection() is False

    def test_fetch_recordings_filters_by_since(self):
        """Should filter recordings by since timestamp."""
        client = PocketClient("test-key")

        # Mock list returns 2 recordings
        client.get_recordings_list = MagicMock(return_value=[
            {"id": "rec1", "createdAt": "2026-02-10T10:00:00Z"},
            {"id": "rec2", "createdAt": "2026-02-15T10:00:00Z"},
        ])

        # Mock details
        client.get_recording_details = MagicMock(return_value={
            "id": "rec2",
            "title": "New Recording",
            "createdAt": "2026-02-15T10:00:00Z",
            "summarizations": {"v2_summary": {"markdown": "Summary"}},
        })

        since = datetime(2026, 2, 12, 0, 0, 0, tzinfo=timezone.utc)
        recordings = client.fetch_recordings(since=since)

        # Should only return the newer recording
        assert len(recordings) == 1
        assert recordings[0].id == "rec2"

    def test_parse_recording_handles_missing_fields(self):
        """Should handle recordings with missing optional fields."""
        client = PocketClient("test-key")
        data = {
            "id": "rec1",
            "createdAt": "2026-02-14T10:00:00Z",
        }

        recording = client._parse_recording(data)

        assert recording is not None
        assert recording.id == "rec1"
        assert recording.title is None
        assert recording.summary is None
        assert recording.action_items == []

    def test_parse_recording_extracts_action_items(self):
        """Should extract action items from summarizations."""
        client = PocketClient("test-key")
        data = {
            "id": "rec1",
            "createdAt": "2026-02-14T10:00:00Z",
            "summarizations": {
                "v2_action_items": {
                    "actions": [
                        {"label": "Task 1", "priority": "High"},
                        {"label": "Task 2", "priority": "Low"},
                    ]
                }
            }
        }

        recording = client._parse_recording(data)

        assert len(recording.action_items) == 2
        assert recording.action_items[0].label == "Task 1"
        assert recording.action_items[0].priority == "High"
