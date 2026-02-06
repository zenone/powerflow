"""Tests for data models."""

from datetime import datetime
from powerflow.models import ActionItem, SyncResult


def test_action_item_to_notion_properties():
    """Test converting action item to Notion properties."""
    item = ActionItem(
        label="Test action",
        pocket_id="pocket:123:0",
        recording_id="123",
        priority="High",
        context="Test context",
    )

    property_map = {
        "title": "Name",
        "pocket_id": "Inbox ID",
        "priority": "Priority",
        "context": "Context",
    }

    props = item.to_notion_properties(property_map)

    assert props["Name"]["title"][0]["text"]["content"] == "Test action"
    assert props["Inbox ID"]["rich_text"][0]["text"]["content"] == "pocket:123:0"
    assert props["Priority"]["select"]["name"] == "High"
    assert props["Context"]["rich_text"][0]["text"]["content"] == "Test context"


def test_action_item_truncates_long_context():
    """Test that long context is truncated."""
    long_context = "x" * 3000
    item = ActionItem(
        label="Test",
        pocket_id="pocket:123:0",
        recording_id="123",
        context=long_context,
    )

    props = item.to_notion_properties({"title": "Name", "pocket_id": "ID", "context": "Context"})
    assert len(props["Context"]["rich_text"][0]["text"]["content"]) == 1900


def test_sync_result_total():
    """Test SyncResult total calculation."""
    result = SyncResult(created=5, skipped=3, failed=2)
    assert result.total == 10


def test_sync_result_str():
    """Test SyncResult string representation."""
    result = SyncResult(created=5, skipped=3, failed=2)
    assert "Created: 5" in str(result)
    assert "Skipped: 3" in str(result)
    assert "Failed: 2" in str(result)
