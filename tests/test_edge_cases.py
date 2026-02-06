"""Edge case tests for Power-Flow robustness."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import pytest

from powerflow.models import ActionItem, SyncResult
from powerflow.sync import SyncEngine
from powerflow.pocket import PocketClient
from powerflow.notion import NotionClient


class TestEmptyData:
    """Tests for empty data scenarios."""

    def test_sync_with_no_recordings(self):
        """Sync should handle empty Pocket account gracefully."""
        mock_pocket = MagicMock()
        mock_pocket.fetch_action_items_since.return_value = []
        mock_notion = MagicMock()
        mock_config = MagicMock()
        mock_config.is_configured = True
        mock_config.notion.database_id = "db123"
        mock_config.notion.property_map = {"pocket_id": "Inbox ID"}
        mock_config.pocket.last_sync = None

        engine = SyncEngine(mock_pocket, mock_notion, mock_config)
        result = engine.sync()

        assert result.created == 0
        assert result.skipped == 0
        assert result.failed == 0
        assert len(result.errors) == 0
        # Should NOT call batch_check if no items
        mock_notion.batch_check_existing_pocket_ids.assert_not_called()

    def test_action_item_with_all_none_optional_fields(self):
        """ActionItem should handle all optional fields being None."""
        item = ActionItem(
            label="Test",
            pocket_id="pocket:123:0",
            recording_id="123",
            priority=None,
            due_date=None,
            assignee=None,
            context=None,
            item_type=None,
            recording_title=None,
            recording_url=None,
            created_at=None,
            duration_seconds=None,
            tags=[],
        )

        # Properties should still work
        props = item.to_notion_properties({"title": "Name", "pocket_id": "ID"})
        assert "Name" in props
        assert "ID" in props

        # Children should be empty (no context, no source details)
        children = item.to_notion_children()
        assert children == []


class TestMalformedData:
    """Tests for malformed/unexpected data."""

    def test_action_item_with_whitespace_only_label(self):
        """Should handle whitespace-only label."""
        item = ActionItem(
            label="   ",
            pocket_id="pocket:123:0",
            recording_id="123",
        )
        props = item.to_notion_properties({"title": "Name", "pocket_id": "ID"})
        assert props["Name"]["title"][0]["text"]["content"] == "   "

    def test_tags_with_empty_strings(self):
        """Empty string tags should be filtered out."""
        item = ActionItem(
            label="Test",
            pocket_id="pocket:123:0",
            recording_id="123",
            tags=["", "valid", "  ", "also_valid"],
        )
        props = item.to_notion_properties({"title": "Name", "pocket_id": "ID", "tags": "Tags"})
        
        tag_names = [t["name"] for t in props["Tags"]["multi_select"]]
        assert "" not in tag_names
        assert "valid" in tag_names
        assert "also_valid" in tag_names

    def test_pocket_client_handles_missing_action_items_key(self):
        """Should handle recordings without action items gracefully."""
        client = PocketClient("fake_key")
        
        # Recording with no summarizations
        recording = {
            "id": "123",
            "title": "Test",
            "createdAt": "2026-02-06T10:00:00Z",
        }
        
        items = client._extract_action_items(recording, "123")
        assert items == []

    def test_pocket_client_handles_empty_actions_array(self):
        """Should handle empty actions array."""
        client = PocketClient("fake_key")
        
        recording = {
            "id": "123",
            "summarizations": {
                "v2_action_items": {
                    "actions": []
                }
            }
        }
        
        items = client._extract_action_items(recording, "123")
        assert items == []


class TestConfigErrors:
    """Tests for configuration error handling."""

    def test_sync_before_setup(self):
        """Sync should fail gracefully if not configured."""
        mock_pocket = MagicMock()
        mock_notion = MagicMock()
        mock_config = MagicMock()
        mock_config.is_configured = False

        engine = SyncEngine(mock_pocket, mock_notion, mock_config)
        result = engine.sync()

        assert result.created == 0
        assert "Not configured" in result.errors[0]
        # Should not call any API
        mock_pocket.fetch_action_items_since.assert_not_called()


class TestAPIErrors:
    """Tests for API error handling."""

    def test_sync_handles_pocket_api_failure(self):
        """Sync should handle Pocket API errors gracefully."""
        mock_pocket = MagicMock()
        mock_pocket.fetch_action_items_since.side_effect = Exception("Connection refused")
        mock_notion = MagicMock()
        mock_config = MagicMock()
        mock_config.is_configured = True
        mock_config.notion.database_id = "db123"
        mock_config.notion.property_map = {"pocket_id": "Inbox ID"}
        mock_config.pocket.last_sync = None

        engine = SyncEngine(mock_pocket, mock_notion, mock_config)
        result = engine.sync()

        assert result.created == 0
        assert "Failed to fetch from Pocket" in result.errors[0]

    def test_sync_handles_notion_batch_check_failure(self):
        """Sync should handle Notion dedup check errors gracefully."""
        mock_pocket = MagicMock()
        mock_pocket.fetch_action_items_since.return_value = [
            ActionItem(label="Test", pocket_id="pocket:1:0", recording_id="1")
        ]
        mock_notion = MagicMock()
        mock_notion.batch_check_existing_pocket_ids.side_effect = Exception("Rate limited")
        mock_config = MagicMock()
        mock_config.is_configured = True
        mock_config.notion.database_id = "db123"
        mock_config.notion.property_map = {"pocket_id": "Inbox ID"}
        mock_config.pocket.last_sync = None

        engine = SyncEngine(mock_pocket, mock_notion, mock_config)
        result = engine.sync()

        assert "Failed to check existing items" in result.errors[0]

    def test_sync_continues_after_single_item_failure(self):
        """Sync should continue if one item fails to create."""
        mock_pocket = MagicMock()
        mock_pocket.fetch_action_items_since.return_value = [
            ActionItem(label="Item 1", pocket_id="pocket:1:0", recording_id="1"),
            ActionItem(label="Item 2", pocket_id="pocket:2:0", recording_id="2"),
            ActionItem(label="Item 3", pocket_id="pocket:3:0", recording_id="3"),
        ]
        mock_notion = MagicMock()
        mock_notion.batch_check_existing_pocket_ids.return_value = set()
        
        # Second item fails to create
        call_count = [0]
        def create_page_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("Notion error on item 2")
            return {}
        
        mock_notion.create_page.side_effect = create_page_side_effect
        
        mock_config = MagicMock()
        mock_config.is_configured = True
        mock_config.notion.database_id = "db123"
        mock_config.notion.property_map = {"pocket_id": "Inbox ID", "title": "Name"}
        mock_config.pocket.last_sync = None

        engine = SyncEngine(mock_pocket, mock_notion, mock_config)
        result = engine.sync()

        assert result.created == 2  # Items 1 and 3 succeeded
        assert result.failed == 1   # Item 2 failed
        assert "Item 2" in result.errors[0]


class TestDryRun:
    """Tests for dry-run accuracy."""

    def test_dry_run_counts_correctly(self):
        """Dry run should report what WOULD be created."""
        mock_pocket = MagicMock()
        mock_pocket.fetch_action_items_since.return_value = [
            ActionItem(label="New 1", pocket_id="pocket:1:0", recording_id="1"),
            ActionItem(label="New 2", pocket_id="pocket:2:0", recording_id="2"),
            ActionItem(label="Exists", pocket_id="pocket:3:0", recording_id="3"),
        ]
        mock_notion = MagicMock()
        mock_notion.batch_check_existing_pocket_ids.return_value = {"pocket:3:0"}
        mock_config = MagicMock()
        mock_config.is_configured = True
        mock_config.notion.database_id = "db123"
        mock_config.notion.property_map = {"pocket_id": "Inbox ID", "title": "Name"}
        mock_config.pocket.last_sync = None

        engine = SyncEngine(mock_pocket, mock_notion, mock_config)
        result = engine.sync(dry_run=True)

        assert result.created == 2   # Would create 2
        assert result.skipped == 1   # Would skip 1
        mock_notion.create_page.assert_not_called()  # Never actually called


class TestTimezoneHandling:
    """Tests for timezone handling in dates."""

    def test_incremental_sync_compares_utc_correctly(self):
        """Incremental sync should handle timezone-aware comparisons."""
        client = PocketClient("fake_key")
        
        # Mock get_recordings to return recordings with different times
        client.get_recordings = MagicMock(return_value=[
            {"id": "1", "createdAt": "2026-02-06T10:00:00Z"},  # Before cutoff
            {"id": "2", "createdAt": "2026-02-06T14:00:00Z"},  # After cutoff
        ])
        client.get_recording = MagicMock(return_value={
            "id": "2",
            "summarizations": {
                "v2_action_items": {
                    "actions": [{"label": "New item"}]
                }
            }
        })
        
        since = datetime(2026, 2, 6, 12, 0, 0, tzinfo=timezone.utc)
        items = client.fetch_action_items_since(since)
        
        # Should only return items after the cutoff
        assert len(items) == 1
        assert items[0].label == "New item"
