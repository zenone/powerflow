"""Tests for incremental sync (v0.3)."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from powerflow.models import ActionItem
from powerflow.sync import SyncEngine


class TestIncrementalSync:
    """Tests for incremental sync feature."""

    def test_sync_uses_last_sync_timestamp(self):
        """Sync should pass last_sync to Pocket client."""
        mock_pocket = MagicMock()
        mock_pocket.fetch_action_items_since.return_value = []
        mock_notion = MagicMock()
        mock_config = MagicMock()
        mock_config.is_configured = True
        mock_config.notion.database_id = "db123"
        mock_config.notion.property_map = {"pocket_id": "Inbox ID"}
        mock_config.pocket.last_sync = datetime(2026, 2, 5, 12, 0, 0, tzinfo=timezone.utc)

        engine = SyncEngine(mock_pocket, mock_notion, mock_config)
        engine.sync()

        mock_pocket.fetch_action_items_since.assert_called_once()
        call_args = mock_pocket.fetch_action_items_since.call_args
        assert call_args[0][0] == mock_config.pocket.last_sync

    def test_sync_updates_last_sync_after_success(self):
        """After successful sync, last_sync should be updated."""
        mock_pocket = MagicMock()
        mock_pocket.fetch_action_items_since.return_value = [
            ActionItem(
                label="Test",
                pocket_id="pocket:123:0",
                recording_id="123",
            )
        ]
        mock_notion = MagicMock()
        mock_notion.batch_check_existing_pocket_ids.return_value = set()
        mock_config = MagicMock()
        mock_config.is_configured = True
        mock_config.notion.database_id = "db123"
        mock_config.notion.property_map = {"pocket_id": "Inbox ID", "title": "Name"}
        mock_config.pocket.last_sync = None

        engine = SyncEngine(mock_pocket, mock_notion, mock_config)
        engine.sync()

        mock_config.update_last_sync.assert_called_once()

    def test_sync_does_not_update_last_sync_on_dry_run(self):
        """Dry run should not update last_sync."""
        mock_pocket = MagicMock()
        mock_pocket.fetch_action_items_since.return_value = [
            ActionItem(
                label="Test",
                pocket_id="pocket:123:0",
                recording_id="123",
            )
        ]
        mock_notion = MagicMock()
        mock_config = MagicMock()
        mock_config.is_configured = True
        mock_config.notion.database_id = "db123"
        mock_config.notion.property_map = {"pocket_id": "Inbox ID"}
        mock_config.pocket.last_sync = None

        engine = SyncEngine(mock_pocket, mock_notion, mock_config)
        engine.sync(dry_run=True)

        mock_config.update_last_sync.assert_not_called()

    def test_full_sync_when_no_last_sync(self):
        """When last_sync is None, fetch all recordings."""
        mock_pocket = MagicMock()
        mock_pocket.fetch_action_items_since.return_value = []
        mock_notion = MagicMock()
        mock_config = MagicMock()
        mock_config.is_configured = True
        mock_config.notion.database_id = "db123"
        mock_config.notion.property_map = {"pocket_id": "Inbox ID"}
        mock_config.pocket.last_sync = None  # No previous sync

        engine = SyncEngine(mock_pocket, mock_notion, mock_config)
        engine.sync()

        # Should be called with None (full sync)
        mock_pocket.fetch_action_items_since.assert_called_once_with(None)
