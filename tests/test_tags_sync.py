"""Tests for tags sync (v0.3)."""

from datetime import datetime

import pytest

from powerflow.models import ActionItem


class TestTagsSync:
    """Tests for tags sync feature."""

    def test_action_item_with_tags_to_notion_properties(self):
        """Tags should be included in Notion properties as multi_select."""
        item = ActionItem(
            label="Test action",
            pocket_id="pocket:123:0",
            recording_id="123",
            tags=["work", "urgent", "meeting"],
        )

        property_map = {
            "title": "Name",
            "pocket_id": "Inbox ID",
            "tags": "Tags",
        }

        props = item.to_notion_properties(property_map)

        assert "Tags" in props
        assert props["Tags"]["multi_select"] == [
            {"name": "work"},
            {"name": "urgent"},
            {"name": "meeting"},
        ]

    def test_action_item_empty_tags(self):
        """Empty tags list should not add Tags property."""
        item = ActionItem(
            label="Test action",
            pocket_id="pocket:123:0",
            recording_id="123",
            tags=[],
        )

        property_map = {
            "title": "Name",
            "pocket_id": "Inbox ID",
            "tags": "Tags",
        }

        props = item.to_notion_properties(property_map)

        # Tags property should not be present if empty
        assert "Tags" not in props

    def test_action_item_no_tags_in_map(self):
        """If tags not in property_map, should be ignored."""
        item = ActionItem(
            label="Test action",
            pocket_id="pocket:123:0",
            recording_id="123",
            tags=["work"],
        )

        property_map = {
            "title": "Name",
            "pocket_id": "Inbox ID",
            # No "tags" mapping
        }

        props = item.to_notion_properties(property_map)

        # Should not fail, just skip tags
        assert "Tags" not in props

    def test_tags_normalized_for_notion(self):
        """Tags should be normalized (trimmed, deduplicated)."""
        item = ActionItem(
            label="Test action",
            pocket_id="pocket:123:0",
            recording_id="123",
            tags=["work", " work ", "WORK", "meeting"],  # Duplicates
        )

        property_map = {"title": "Name", "pocket_id": "ID", "tags": "Tags"}
        props = item.to_notion_properties(property_map)

        # Should deduplicate (case-insensitive) and trim
        tag_names = [t["name"] for t in props["Tags"]["multi_select"]]
        assert len(tag_names) == 2  # "work" and "meeting"
        assert "meeting" in tag_names
