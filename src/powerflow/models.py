"""Data models for Power-Flow."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ActionItem:
    """An action item extracted from a recording."""

    label: str
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    assignee: Optional[str] = None
    context: Optional[str] = None
    item_type: Optional[str] = None  # CreateReminder, etc.

    def to_checklist_text(self) -> str:
        """Format as a checklist-style text line."""
        parts = [f"☐ {self.label}"]
        if self.priority:
            parts.append(f" [{self.priority}]")
        if self.due_date:
            parts.append(f" (due: {self.due_date.strftime('%b %d')})")
        return "".join(parts)


@dataclass
class Recording:
    """A recording from Pocket AI — the unit of sync."""

    id: str
    title: Optional[str] = None
    summary: Optional[str] = None
    transcript: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    action_items: list[ActionItem] = field(default_factory=list)
    created_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    pocket_url: Optional[str] = None

    @property
    def pocket_id(self) -> str:
        """Unique ID for deduplication."""
        return f"pocket:recording:{self.id}"

    @property
    def display_title(self) -> str:
        """Best title for display."""
        if self.title and self.title.strip():
            return self.title.strip()
        if self.summary:
            # First sentence or first 60 chars
            first_line = self.summary.split('.')[0].strip()
            if len(first_line) > 60:
                return first_line[:57] + "..."
            return first_line
        return "Untitled Recording"

    def to_notion_properties(self, property_map: dict) -> dict:
        """Convert to Notion page properties based on mapping."""
        props = {}

        # Title is always required
        title_prop = property_map.get("title", "Name")
        props[title_prop] = {"title": [{"text": {"content": self.display_title}}]}

        # Pocket ID for deduplication (CRITICAL)
        pocket_id_prop = property_map.get("pocket_id", "Inbox ID")
        props[pocket_id_prop] = {"rich_text": [{"text": {"content": self.pocket_id}}]}

        # Source URL
        if self.pocket_url and "source_url" in property_map:
            props[property_map["source_url"]] = {"url": self.pocket_url}

        # Tags (multi-select)
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
        """Build the page body blocks with Michelin-star attention to detail.
        
        Structure:
        1. Summary callout (if available) — gray background, thought bubble
        2. Action items callout (if any) — yellow background, checkbox icon
           - To-do items nested inside
        3. Divider
        4. Source details toggle (collapsed)
           - Duration, capture date, Pocket link
           - Transcript toggle (nested, collapsed)
        """
        from .blocks import (
            create_callout,
            create_divider,
            create_toggle,
            create_bullet,
            create_paragraph,
            create_todo,
            create_heading,
            format_duration,
        )
        
        children = []
        
        # 1. Summary callout — the AI's interpretation
        if self.summary:
            children.append(
                create_callout(
                    self.summary,
                    icon="💭",
                    color="gray_background"
                )
            )
        
        # 2. Action items section — visually prominent
        if self.action_items:
            # Build to-do items first
            todo_blocks = []
            for item in self.action_items:
                todo_text = item.label
                if item.priority:
                    todo_text += f" [{item.priority}]"
                if item.due_date:
                    todo_text += f" — due {item.due_date.strftime('%b %d')}"
                todo_blocks.append(create_todo(todo_text))
            
            # Wrap in a callout for visual prominence
            # Use toggle-style callout: heading + nested items
            children.append(create_heading("Action Items", level=3))
            children.extend(todo_blocks)
        
        # 3. Divider before metadata
        children.append(create_divider())
        
        # 4. Source details toggle (collapsed by default)
        source_children = []
        
        if self.duration_seconds:
            duration_str = format_duration(self.duration_seconds)
            source_children.append(create_bullet(duration_str, "Duration"))
        
        if self.created_at:
            date_str = self.created_at.strftime("%b %d, %Y at %I:%M %p")
            source_children.append(create_bullet(date_str, "Captured"))
        
        if self.pocket_url:
            source_children.append(
                create_paragraph(
                    "Open in Pocket AI →",
                    link=self.pocket_url,
                    color="blue"
                )
            )
        
        # Transcript toggle (nested, collapsed)
        if self.transcript:
            # Show first 500 chars as preview
            transcript_preview = self.transcript[:500]
            if len(self.transcript) > 500:
                transcript_preview += "..."
            source_children.append(
                create_toggle("📝 Full Transcript", [
                    create_paragraph(transcript_preview)
                ])
            )
        
        # Add source toggle if we have any details
        if source_children:
            children.append(create_toggle("📎 Source Details", source_children))
        
        return children


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
