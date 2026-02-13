"""Tests for incremental sync functionality."""

from unittest.mock import MagicMock

from powerflow.models import Recording
from powerflow.sync import SyncEngine


class TestIncrementalSync:
    """Tests for incremental sync using last_sync timestamp."""

    def test_sync_uses_last_sync_timestamp(self):
        """Sync should pass last_sync to Pocket client."""
        mock_pocket = MagicMock()
        mock_pocket.fetch_recordings.return_value = []
        mock_notion = MagicMock()
        mock_config = MagicMock()
        mock_config.is_configured = True
        mock_config.notion.database_id = "db123"
        mock_config.notion.property_map = {"pocket_id": "Inbox ID"}
        mock_config.pocket.last_sync = "2026-02-06T10:00:00+00:00"

        engine = SyncEngine(mock_pocket, mock_notion, mock_config)
        engine.sync()

        # Should have called fetch_recordings
        mock_pocket.fetch_recordings.assert_called_once()
        call_args = mock_pocket.fetch_recordings.call_args

        # Get the 'since' kwarg
        since = call_args.kwargs.get("since")

        assert since is not None, "since should be passed to fetch_recordings"
        assert since.tzinfo is not None, "since should be timezone-aware"
        assert since.year == 2026
        assert since.month == 2
        assert since.day == 6

    def test_sync_updates_last_sync_after_success(self):
        """Sync should update last_sync timestamp after successful sync."""
        mock_pocket = MagicMock()
        mock_pocket.fetch_recordings.return_value = [
            Recording(id="1", title="Test", summary="Test summary"),  # Summary makes it complete
        ]
        mock_notion = MagicMock()
        mock_notion.batch_check_existing_pocket_ids.return_value = set()
        mock_notion.create_page.return_value = {"id": "page123"}
        mock_config = MagicMock()
        mock_config.is_configured = True
        mock_config.notion.database_id = "db123"
        mock_config.notion.property_map = {"pocket_id": "Inbox ID", "title": "Name"}
        mock_config.pocket.last_sync = None

        engine = SyncEngine(mock_pocket, mock_notion, mock_config)
        result = engine.sync()

        assert result.created == 1
        mock_config.update_last_sync.assert_called_once()

    def test_sync_does_not_update_last_sync_on_dry_run(self):
        """Dry run should not update last_sync."""
        mock_pocket = MagicMock()
        mock_pocket.fetch_recordings.return_value = [
            Recording(id="1", title="Test", summary="Test summary"),  # Summary makes it complete
        ]
        mock_notion = MagicMock()
        mock_notion.batch_check_existing_pocket_ids.return_value = set()
        mock_config = MagicMock()
        mock_config.is_configured = True
        mock_config.notion.database_id = "db123"
        mock_config.notion.property_map = {"pocket_id": "Inbox ID", "title": "Name"}
        mock_config.pocket.last_sync = None

        engine = SyncEngine(mock_pocket, mock_notion, mock_config)
        result = engine.sync(dry_run=True)

        assert result.created == 1
        mock_config.update_last_sync.assert_not_called()

    def test_full_sync_when_no_last_sync(self):
        """Should fetch all recordings when last_sync is None."""
        mock_pocket = MagicMock()
        mock_pocket.fetch_recordings.return_value = [
            # Summary makes recordings complete for sync
            Recording(id="1", title="Old Recording", summary="Summary 1"),
            Recording(id="2", title="New Recording", summary="Summary 2"),
        ]
        mock_notion = MagicMock()
        mock_notion.batch_check_existing_pocket_ids.return_value = set()
        mock_notion.create_page.return_value = {"id": "page123"}
        mock_config = MagicMock()
        mock_config.is_configured = True
        mock_config.notion.database_id = "db123"
        mock_config.notion.property_map = {"pocket_id": "Inbox ID", "title": "Name"}
        mock_config.pocket.last_sync = None

        engine = SyncEngine(mock_pocket, mock_notion, mock_config)
        result = engine.sync()

        # Should sync all recordings
        assert result.created == 2

        # Should have called with since=None
        mock_pocket.fetch_recordings.assert_called_once()
        call_args = mock_pocket.fetch_recordings.call_args
        since = call_args.kwargs.get("since")
        assert since is None
