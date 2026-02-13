"""Tests for data models."""

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
        """Test page body includes summary as parsed blocks."""
        rec = Recording(
            id="abc",
            summary="### Heading\n- **Bold** item\n- Regular item",
        )
        children = rec.to_notion_children()

        # Should have parsed markdown blocks
        heading = next((c for c in children if c.get("type") == "heading_3"), None)
        assert heading is not None
        assert heading["heading_3"]["rich_text"][0]["text"]["content"] == "Heading"

        # Should have bullet items
        bullets = [c for c in children if c.get("type") == "bulleted_list_item"]
        assert len(bullets) >= 2

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


class TestRecordingIcon:
    """Tests for Recording.get_icon() method."""

    def test_icon_from_work_tag(self):
        """Work tag should return briefcase emoji."""
        rec = Recording(id="abc", tags=["work", "meeting"])
        icon = rec.get_icon()
        assert icon == {"type": "emoji", "emoji": "💼"}

    def test_icon_from_meeting_tag(self):
        """Meeting tag should return calendar emoji."""
        rec = Recording(id="abc", tags=["meeting"])
        icon = rec.get_icon()
        assert icon == {"type": "emoji", "emoji": "📅"}

    def test_icon_first_match_wins(self):
        """First matching tag in the list wins."""
        rec = Recording(id="abc", tags=["random", "idea", "work"])
        icon = rec.get_icon()
        assert icon == {"type": "emoji", "emoji": "💡"}  # idea comes before work

    def test_icon_default_when_no_match(self):
        """No matching tags should return default mic emoji."""
        rec = Recording(id="abc", tags=["random", "stuff"])
        icon = rec.get_icon()
        assert icon == {"type": "emoji", "emoji": "🎙️"}

    def test_icon_default_when_no_tags(self):
        """Empty tags should return default mic emoji."""
        rec = Recording(id="abc", tags=[])
        icon = rec.get_icon()
        assert icon == {"type": "emoji", "emoji": "🎙️"}

    def test_icon_case_insensitive(self):
        """Tag matching should be case-insensitive."""
        rec = Recording(id="abc", tags=["WORK", "Meeting"])
        icon = rec.get_icon()
        assert icon == {"type": "emoji", "emoji": "💼"}


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


class TestSummaryCompletion:
    """Tests for is_summary_complete property."""

    def test_complete_with_summary(self):
        """Recording with summary is complete."""
        rec = Recording(id="1", summary="This is a summary")
        assert rec.is_summary_complete is True

    def test_complete_with_action_items(self):
        """Recording with action items is complete."""
        rec = Recording(id="1", action_items=[ActionItem(label="Do something")])
        assert rec.is_summary_complete is True

    def test_complete_with_mind_map(self):
        """Recording with mind map nodes is complete."""
        rec = Recording(id="1", mind_map=[{"node_id": "1", "title": "Root"}])
        assert rec.is_summary_complete is True

    def test_incomplete_without_ai_content(self):
        """Recording without AI content is incomplete (still processing)."""
        rec = Recording(id="1", title="Just title")
        assert rec.is_summary_complete is False

    def test_incomplete_with_empty_summary(self):
        """Recording with empty/whitespace summary is incomplete."""
        rec = Recording(id="1", summary="   ")
        assert rec.is_summary_complete is False

    def test_incomplete_with_empty_lists(self):
        """Recording with empty action_items and mind_map is incomplete."""
        rec = Recording(id="1", action_items=[], mind_map=[])
        assert rec.is_summary_complete is False

    def test_complete_with_multiple_indicators(self):
        """Recording with multiple AI content is complete."""
        rec = Recording(
            id="1",
            summary="Summary text",
            action_items=[ActionItem(label="Task")],
            mind_map=[{"node_id": "1", "title": "Root"}]
        )
        assert rec.is_summary_complete is True
