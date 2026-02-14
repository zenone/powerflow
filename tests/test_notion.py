"""Tests for Notion API client."""

from unittest.mock import MagicMock, patch

import requests

from powerflow.notion import NOTION_RETRY_CONFIG, NotionClient


class TestNotionClient:
    """Tests for NotionClient class."""

    def test_init_sets_headers(self):
        """Client should set authorization headers."""
        client = NotionClient("test-api-key")
        assert "Authorization" in client.session.headers
        assert "Bearer test-api-key" in client.session.headers["Authorization"]

    def test_init_sets_notion_version(self):
        """Client should set Notion-Version header."""
        client = NotionClient("test-api-key")
        assert "Notion-Version" in client.session.headers

    def test_init_uses_rate_limiter(self):
        """Client should have a rate limiter."""
        client = NotionClient("test-api-key")
        assert client._rate_limiter is not None

    def test_timeout_default(self):
        """Default timeout should be 30 seconds."""
        client = NotionClient("test-api-key")
        assert client.timeout == 30.0

    def test_timeout_custom(self):
        """Should accept custom timeout."""
        client = NotionClient("test-api-key", timeout=60.0)
        assert client.timeout == 60.0


class TestNotionRetryConfig:
    """Tests for Notion retry configuration."""

    def test_max_attempts(self):
        """Should retry 3 times by default."""
        assert NOTION_RETRY_CONFIG.max_attempts == 3

    def test_retriable_codes(self):
        """Should retry on expected status codes."""
        assert 429 in NOTION_RETRY_CONFIG.retriable_status_codes
        assert 500 in NOTION_RETRY_CONFIG.retriable_status_codes
        assert 502 in NOTION_RETRY_CONFIG.retriable_status_codes
        assert 503 in NOTION_RETRY_CONFIG.retriable_status_codes
        assert 504 in NOTION_RETRY_CONFIG.retriable_status_codes

    def test_404_not_retriable(self):
        """Should not retry on 404."""
        assert 404 not in NOTION_RETRY_CONFIG.retriable_status_codes


class TestNotionClientMethods:
    """Tests for NotionClient API methods."""

    def test_search_databases_pagination(self):
        """Should handle pagination correctly."""
        client = NotionClient("test-key")

        # Mock paginated response
        responses = [
            {"results": [{"id": "db1"}], "has_more": True, "next_cursor": "cursor1"},
            {"results": [{"id": "db2"}], "has_more": False, "next_cursor": None},
        ]
        call_count = [0]

        def mock_request(*args, **kwargs):
            result = responses[call_count[0]]
            call_count[0] += 1
            return result

        client._request = mock_request

        results = client.search_databases()
        assert len(results) == 2
        assert results[0]["id"] == "db1"
        assert results[1]["id"] == "db2"

    def test_get_database_schema(self):
        """Should return properties from database."""
        client = NotionClient("test-key")
        client._request = MagicMock(return_value={
            "id": "db123",
            "properties": {
                "Name": {"type": "title"},
                "Status": {"type": "select"},
            }
        })

        schema = client.get_database_schema("db123")
        assert "Name" in schema
        assert "Status" in schema

    def test_test_connection_success(self):
        """test_connection should return True on success."""
        client = NotionClient("test-key")
        client.search_databases = MagicMock(return_value=[])

        assert client.test_connection() is True

    def test_test_connection_failure(self):
        """test_connection should return False on failure."""
        client = NotionClient("test-key")
        client.search_databases = MagicMock(
            side_effect=requests.RequestException("Connection failed")
        )

        assert client.test_connection() is False

    def test_format_databases_for_display(self):
        """Should format database list for CLI display."""
        client = NotionClient("test-key")
        databases = [
            {
                "id": "db1",
                "title": [{"plain_text": "My Database"}],
                "icon": {"type": "emoji", "emoji": "📚"},
                "url": "https://notion.so/db1",
            },
            {
                "id": "db2",
                "title": [],
                "icon": None,
                "url": "https://notion.so/db2",
            },
        ]

        formatted = client.format_databases_for_display(databases)

        assert len(formatted) == 2
        assert formatted[0]["title"] == "My Database"
        assert formatted[0]["emoji"] == "📚"
        assert formatted[1]["title"] == "Untitled"
        assert formatted[1]["emoji"] == "📄"  # Default

    def test_create_property_unknown_type_warns(self):
        """Should log warning for unknown property type."""
        client = NotionClient("test-key")
        client._request = MagicMock(return_value={})

        with patch("powerflow.notion.logger") as mock_logger:
            client.create_property("db123", "Custom", "unknown_type")
            mock_logger.warning.assert_called()
