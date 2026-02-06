"""Data models for Power-Flow."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ActionItem:
    """An action item from Pocket AI."""

    label: str
    pocket_id: str  # Unique ID for deduplication
    recording_id: str
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    assignee: Optional[str] = None
    context: Optional[str] = None
    item_type: Optional[str] = None  # CreateReminder, etc.
    recording_title: Optional[str] = None
    recording_url: Optional[str] = None
    created_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None  # Recording duration
    tags: list[str] = field(default_factory=list)  # From recording

    def to_notion_properties(self, property_map: dict) -> dict:
        """Convert to Notion page properties based on mapping."""
        props = {}

        # Title is always required
        title_prop = property_map.get("title", "Name")
        props[title_prop] = {"title": [{"text": {"content": self.label}}]}

        # Pocket ID for deduplication
        pocket_id_prop = property_map.get("pocket_id", "Inbox ID")
        props[pocket_id_prop] = {"rich_text": [{"text": {"content": self.pocket_id}}]}

        # Priority (select)
        if self.priority and "priority" in property_map:
            props[property_map["priority"]] = {"select": {"name": self.priority}}

        # Due date
        if self.due_date and "due_date" in property_map:
            props[property_map["due_date"]] = {
                "date": {"start": self.due_date.isoformat()}
            }

        # Context (rich text)
        if self.context and "context" in property_map:
            # Truncate context if too long (Notion limit is 2000 chars per text block)
            context_text = self.context[:1900] if len(self.context) > 1900 else self.context
            props[property_map["context"]] = {
                "rich_text": [{"text": {"content": context_text}}]
            }

        # Source URL
        if self.recording_url and "source_url" in property_map:
            props[property_map["source_url"]] = {"url": self.recording_url}

        # Tags (multi-select) — normalize and deduplicate
        if self.tags and "tags" in property_map:
            seen = set()
            unique_tags = []
            for tag in self.tags:
                normalized = tag.strip().lower()
                if normalized and normalized not in seen:
                    seen.add(normalized)
                    unique_tags.append({"name": tag.strip()})
            if unique_tags:
                props[property_map["tags"]] = {"multi_select": unique_tags}

        return props

    def to_notion_children(self) -> list[dict]:
        """Build the page body blocks for rich visual content.
        
        Structure:
        1. Context callout (priority-styled with icon and color)
        2. Divider
        3. Source details toggle (collapsed by default)
           - Recording title
           - Duration
           - Created date
           - Link to Pocket
        """
        from .blocks import (
            create_callout,
            create_divider,
            create_toggle,
            create_bullet,
            create_paragraph,
            get_priority_style,
            format_duration,
        )
        
        children = []
        
        # 1. Context callout (priority-styled)
        if self.context:
            style = get_priority_style(self.priority)
            children.append(
                create_callout(
                    self.context,
                    icon=style["icon"],
                    color=style["color"]
                )
            )
        
        # Only add remaining blocks if we have source details
        source_children = []
        
        if self.recording_title:
            source_children.append(create_bullet(self.recording_title, "Recording"))
        
        if self.duration_seconds:
            duration_str = format_duration(self.duration_seconds)
            source_children.append(create_bullet(duration_str, "Duration"))
        
        if self.created_at:
            date_str = self.created_at.strftime("%b %d, %Y at %I:%M %p")
            source_children.append(create_bullet(date_str, "Created"))
        
        if self.recording_url:
            source_children.append(
                create_paragraph(
                    "🔗 Open in Pocket AI",
                    link=self.recording_url,
                    color="blue"
                )
            )
        
        # Add divider and toggle if we have source details
        if source_children:
            children.append(create_divider())
            children.append(create_toggle("Source Details", source_children))
        
        return children


@dataclass
class Recording:
    """A recording from Pocket AI."""

    id: str
    title: Optional[str] = None
    summary: Optional[str] = None
    transcript: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    action_items: list[ActionItem] = field(default_factory=list)
    created_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None


@dataclass
class SyncResult:
    """Result of a sync operation."""

    created: int = 0
    skipped: int = 0  # Already exists (dedup)
    failed: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.created + self.skipped + self.failed

    def __str__(self) -> str:
        return f"Created: {self.created}, Skipped: {self.skipped}, Failed: {self.failed}"
