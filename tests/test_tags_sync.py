"""Tests for tags synchronization."""

import pytest

from powerflow.models import Recording


class TestTagsSync:
    """Tests for recording tags syncing to Notion."""

    def test_recording_with_tags_to_notion_properties(self):
        """Test recording with tags converts to Notion multi_select."""
        rec = Recording(
            id="abc123",
            title="Test",
            tags=["work", "important", "meeting"],
        )
        property_map = {
            "title": "Name",
            "pocket_id": "Inbox ID",
            "tags": "Tags",
        }
        props = rec.to_notion_properties(property_map)
        
        assert "Tags" in props
        assert props["Tags"]["multi_select"] == [
            {"name": "work"},
            {"name": "important"},
            {"name": "meeting"},
        ]

    def test_recording_empty_tags(self):
        """Test recording with empty tags list."""
        rec = Recording(
            id="abc123",
            title="Test",
            tags=[],
        )
        property_map = {
            "title": "Name",
            "pocket_id": "Inbox ID",
            "tags": "Tags",
        }
        props = rec.to_notion_properties(property_map)
        
        # Tags property should not be included if empty
        assert "Tags" not in props

    def test_recording_no_tags_in_map(self):
        """Test recording when tags not in property map."""
        rec = Recording(
            id="abc123",
            title="Test",
            tags=["work", "meeting"],
        )
        property_map = {
            "title": "Name",
            "pocket_id": "Inbox ID",
            # No tags mapping
        }
        props = rec.to_notion_properties(property_map)
        
        # Tags should not appear in props
        assert "Tags" not in props
        assert "tags" not in props

    def test_tags_normalized_for_notion(self):
        """Test tags are normalized (stripped, deduplicated)."""
        rec = Recording(
            id="abc123",
            title="Test",
            tags=["  Work  ", "work", "WORK", "Meeting", "meeting"],
        )
        property_map = {
            "title": "Name",
            "pocket_id": "Inbox ID",
            "tags": "Tags",
        }
        props = rec.to_notion_properties(property_map)
        
        # Should deduplicate case-insensitively, keeping first occurrence's casing
        tags = props["Tags"]["multi_select"]
        tag_names = [t["name"] for t in tags]
        
        # Should have exactly 2 unique tags
        assert len(tags) == 2
        # First occurrence of each should be preserved
        assert "Work" in tag_names
        assert "Meeting" in tag_names
