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


def test_action_item_to_notion_children_with_context():
    """Test building Notion page body with context."""
    item = ActionItem(
        label="Test action",
        pocket_id="pocket:123:0",
        recording_id="123",
        priority="High",
        context="Important context here",
        recording_title="Morning voice note",
        recording_url="https://pocket.ai/rec/123",
        created_at=datetime(2026, 2, 6, 10, 30),
        duration_seconds=154,
    )

    children = item.to_notion_children()

    # Should have: callout, divider, toggle
    assert len(children) == 3
    
    # First block should be a callout with high priority styling
    callout = children[0]
    assert callout["type"] == "callout"
    assert callout["callout"]["icon"]["emoji"] == "🔥"  # High priority
    assert callout["callout"]["color"] == "red_background"
    
    # Second block should be a divider
    assert children[1]["type"] == "divider"
    
    # Third block should be a toggle with source details
    toggle = children[2]
    assert toggle["type"] == "toggle"
    assert "Source Details" in toggle["toggle"]["rich_text"][0]["text"]["content"]
    
    # Toggle should have children: recording, duration, created, link
    toggle_children = toggle["toggle"]["children"]
    assert len(toggle_children) == 4


def test_action_item_to_notion_children_no_context():
    """Test page body when context is missing."""
    item = ActionItem(
        label="Test action",
        pocket_id="pocket:123:0",
        recording_id="123",
        recording_title="Voice note",
    )

    children = item.to_notion_children()

    # Should have: divider, toggle (no callout since no context)
    assert len(children) == 2
    assert children[0]["type"] == "divider"
    assert children[1]["type"] == "toggle"


def test_action_item_to_notion_children_empty():
    """Test page body when no optional fields are set."""
    item = ActionItem(
        label="Minimal action",
        pocket_id="pocket:123:0",
        recording_id="123",
    )

    children = item.to_notion_children()

    # Should be empty - no context, no source details
    assert len(children) == 0
