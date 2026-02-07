"""Tests for data models."""

import pytest
from datetime import datetime, timezone

from powerflow.models import ActionItem, Recording, SyncResult


class TestActionItem:
    """Tests for ActionItem model."""

    def test_basic_action_item(self):
        """Test creating a basic action item."""
        item = ActionItem(label="Test task")
        assert item.label == "Test task"
        assert item.priority is None
        assert item.due_date is None

    def test_action_item_with_all_fields(self):
        """Test action item with all fields populated."""
        due = datetime(2026, 2, 10, tzinfo=timezone.utc)
        item = ActionItem(
            label="Call John",
            priority="High",
            due_date=due,
            assignee="Steve",
            context="About the project",
            item_type="CreateReminder",
        )
        assert item.label == "Call John"
        assert item.priority == "High"
        assert item.due_date == due
        assert item.assignee == "Steve"

    def test_to_checklist_text_basic(self):
        """Test checklist text formatting."""
        item = ActionItem(label="Buy groceries")
        assert item.to_checklist_text() == "☐ Buy groceries"

    def test_to_checklist_text_with_priority(self):
        """Test checklist text with priority."""
        item = ActionItem(label="Buy groceries", priority="High")
        assert item.to_checklist_text() == "☐ Buy groceries [High]"


class TestRecording:
    """Tests for Recording model."""

    def test_basic_recording(self):
        """Test creating a basic recording."""
        rec = Recording(id="abc123")
        assert rec.id == "abc123"
        assert rec.pocket_id == "pocket:recording:abc123"

    def test_display_title_uses_title(self):
        """Test display_title prefers title."""
        rec = Recording(id="abc", title="My Recording")
        assert rec.display_title == "My Recording"

    def test_display_title_falls_back_to_summary(self):
        """Test display_title falls back to summary first sentence."""
        rec = Recording(id="abc", title=None, summary="This is the summary. More text here.")
        assert rec.display_title == "This is the summary"

    def test_display_title_truncates_long_summary(self):
        """Test display_title truncates long summaries."""
        long_summary = "A" * 100 + ". More text."
        rec = Recording(id="abc", title=None, summary=long_summary)
        assert len(rec.display_title) <= 60
        assert rec.display_title.endswith("...")

    def test_display_title_default(self):
        """Test display_title default."""
        rec = Recording(id="abc")
        assert rec.display_title == "Untitled Recording"

    def test_to_notion_properties_basic(self):
        """Test converting recording to Notion properties."""
        rec = Recording(
            id="abc123",
            title="Test Recording",
            pocket_url="https://heypocket.com/recordings/abc123",
            tags=["work", "meeting"],
        )
        property_map = {
            "title": "Name",
            "pocket_id": "Inbox ID",
            "source_url": "Source",
            "tags": "Tags",
        }
        props = rec.to_notion_properties(property_map)
        
        assert "Name" in props
        assert props["Name"]["title"][0]["text"]["content"] == "Test Recording"
        
        assert "Inbox ID" in props
        assert props["Inbox ID"]["rich_text"][0]["text"]["content"] == "pocket:recording:abc123"
        
        assert "Source" in props
        assert props["Source"]["url"] == "https://heypocket.com/recordings/abc123"
        
        assert "Tags" in props
        assert len(props["Tags"]["multi_select"]) == 2

    def test_to_notion_children_with_summary(self):
        """Test page body includes summary callout."""
        rec = Recording(
            id="abc",
            summary="This is the AI summary.",
        )
        children = rec.to_notion_children()
        
        # Should have a callout for summary
        callout = next((c for c in children if c.get("type") == "callout"), None)
        assert callout is not None
        assert "summary" in callout["callout"]["rich_text"][0]["text"]["content"].lower() or \
               "This is the AI summary" in callout["callout"]["rich_text"][0]["text"]["content"]

    def test_to_notion_children_with_action_items(self):
        """Test page body includes action items as to-dos."""
        rec = Recording(
            id="abc",
            action_items=[
                ActionItem(label="Task 1"),
                ActionItem(label="Task 2", priority="High"),
            ],
        )
        children = rec.to_notion_children()
        
        # Should have to-do blocks
        todos = [c for c in children if c.get("type") == "to_do"]
        assert len(todos) == 2

    def test_tags_normalized_and_deduped(self):
        """Test tags are normalized and deduplicated."""
        rec = Recording(
            id="abc",
            tags=["Work", "work", "WORK", "Meeting", "meeting"],
        )
        property_map = {"title": "Name", "pocket_id": "ID", "tags": "Tags"}
        props = rec.to_notion_properties(property_map)
        
        # Should deduplicate case-insensitively
        tags = props["Tags"]["multi_select"]
        assert len(tags) == 2  # work + meeting


class TestSyncResult:
    """Tests for SyncResult model."""

    def test_sync_result_total(self):
        """Test total calculation."""
        result = SyncResult(created=5, skipped=3, failed=2)
        assert result.total == 10

    def test_sync_result_str(self):
        """Test string representation."""
        result = SyncResult(created=5, skipped=3, failed=2)
        assert "Created: 5" in str(result)
        assert "Skipped: 3" in str(result)
        assert "Failed: 2" in str(result)
