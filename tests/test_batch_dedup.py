"""Tests for batch deduplication (v0.3)."""

from unittest.mock import MagicMock

from powerflow.notion import NotionClient


class TestBatchDedup:
    """Tests for batch deduplication feature."""

    def test_batch_check_single_item(self):
        """Single item batch check works."""
        client = NotionClient("fake_key")
        client._request = MagicMock(return_value={
            "results": [
                {
                    "properties": {
                        "Inbox ID": {
                            "rich_text": [{"plain_text": "pocket:123:0"}]
                        }
                    }
                }
            ],
            "has_more": False,
        })

        existing = client.batch_check_existing_pocket_ids(
            "db123",
            ["pocket:123:0"],
            "Inbox ID"
        )

        assert existing == {"pocket:123:0"}

    def test_batch_check_multiple_items(self):
        """Multiple items checked in single query."""
        client = NotionClient("fake_key")
        client._request = MagicMock(return_value={
            "results": [
                {"properties": {"Inbox ID": {"rich_text": [{"plain_text": "pocket:1:0"}]}}},
                {"properties": {"Inbox ID": {"rich_text": [{"plain_text": "pocket:3:0"}]}}},
            ],
            "has_more": False,
        })

        pocket_ids = ["pocket:1:0", "pocket:2:0", "pocket:3:0", "pocket:4:0"]
        existing = client.batch_check_existing_pocket_ids("db123", pocket_ids, "Inbox ID")

        # Only 2 exist
        assert existing == {"pocket:1:0", "pocket:3:0"}

    def test_batch_check_empty_list(self):
        """Empty list returns empty set without API call."""
        client = NotionClient("fake_key")
        client._request = MagicMock()

        existing = client.batch_check_existing_pocket_ids("db123", [], "Inbox ID")

        assert existing == set()
        client._request.assert_not_called()

    def test_batch_check_builds_or_filter(self):
        """Batch check builds correct OR filter."""
        client = NotionClient("fake_key")
        client._request = MagicMock(return_value={"results": [], "has_more": False})

        pocket_ids = ["pocket:1:0", "pocket:2:0"]
        client.batch_check_existing_pocket_ids("db123", pocket_ids, "Inbox ID")

        # Verify the filter structure
        call_args = client._request.call_args
        payload = call_args[1]["json"]

        assert "filter" in payload
        assert "or" in payload["filter"]
        assert len(payload["filter"]["or"]) == 2

        # Each OR clause should be a rich_text equals filter
        for clause in payload["filter"]["or"]:
            assert clause["property"] == "Inbox ID"
            assert "rich_text" in clause
            assert "equals" in clause["rich_text"]

    def test_batch_check_chunks_large_lists(self):
        """Lists >100 items are chunked into multiple queries."""
        client = NotionClient("fake_key")
        call_count = 0

        def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return {"results": [], "has_more": False}

        client._request = mock_request

        # 150 items should result in 2 queries (100 + 50)
        pocket_ids = [f"pocket:{i}:0" for i in range(150)]
        client.batch_check_existing_pocket_ids("db123", pocket_ids, "Inbox ID")

        assert call_count == 2
