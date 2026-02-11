"""Data models for Power-Flow."""

from dataclasses import dataclass, field
from datetime import datetime

# Tag to emoji mapping for Notion page icons
TAG_EMOJI_MAP = {
    "work": "💼",
    "meeting": "📅",
    "idea": "💡",
    "reminder": "⏰",
    "personal": "👤",
    "task": "✅",
    "note": "📝",
    "question": "❓",
    "important": "⭐",
    "urgent": "🔥",
}
DEFAULT_EMOJI = "🎙️"


@dataclass
class ActionItem:
    """An action item extracted from a recording."""

    label: str
    priority: str | None = None
    due_date: datetime | None = None
    assignee: str | None = None
    context: str | None = None
    item_type: str | None = None  # CreateReminder, etc.

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
    title: str | None = None
    summary: str | None = None
    transcript: str | None = None
    tags: list[str] = field(default_factory=list)
    action_items: list[ActionItem] = field(default_factory=list)
    mind_map: list[dict] = field(default_factory=list)  # Hierarchical outline nodes
    created_at: datetime | None = None
    duration_seconds: int | None = None
    pocket_url: str | None = None

    @property
    def is_summary_complete(self) -> bool:
        """Check if AI summary processing has completed.

        A recording is considered ready for sync when it has meaningful
        AI-generated content. This prevents syncing recordings that are
        still being processed by Pocket's AI.

        Returns True if ANY of these are present:
        - Non-empty summary (markdown)
        - At least one action item
        - Mind map nodes

        Returns False if the recording has no AI-generated content,
        indicating it's likely still processing.
        """
        has_summary = bool(self.summary and self.summary.strip())
        has_actions = len(self.action_items) > 0
        has_mind_map = len(self.mind_map) > 0

        return has_summary or has_actions or has_mind_map

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

    def get_icon(self) -> dict:
        """Get Notion icon based on tags.

        Returns first matching tag emoji, or default mic emoji.
        """
        for tag in self.tags:
            normalized = tag.strip().lower()
            if normalized in TAG_EMOJI_MAP:
                return {"type": "emoji", "emoji": TAG_EMOJI_MAP[normalized]}
        return {"type": "emoji", "emoji": DEFAULT_EMOJI}

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

    def _build_mind_map_tree(self) -> list[dict]:
        """Build mind map blocks with visual hierarchy.

        Uses indentation markers since Notion API doesn't support
        deeply nested children in page creation.
        """
        if not self.mind_map:
            return []

        # Build parent-child relationships
        children_map = {}  # parent_id -> [child_nodes]
        roots = []

        for node in self.mind_map:
            if not isinstance(node, dict):
                continue
            node_id = node.get("node_id")
            parent_id = node.get("parent_node_id")

            if node_id == parent_id:
                roots.append(node)
            else:
                if parent_id not in children_map:
                    children_map[parent_id] = []
                children_map[parent_id].append(node)

        blocks = []

        def add_node(node: dict, depth: int = 0):
            """Add a node with visual depth indicator."""
            title = node.get("title", "Untitled")
            node_id = node.get("node_id")

            # Visual hierarchy: root is bold, children get indent markers
            if depth == 0:
                # Root node - bold
                blocks.append({
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{
                            "type": "text",
                            "text": {"content": title},
                            "annotations": {"bold": True}
                        }]
                    }
                })
            else:
                # Child nodes - indented with arrows
                indent = "    " * (depth - 1)
                prefix = f"{indent}↳ " if depth > 0 else ""
                blocks.append({
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": f"{prefix}{title}"}}]
                    }
                })

            # Process children
            for child in children_map.get(node_id, []):
                add_node(child, depth + 1)

        for root in roots:
            add_node(root, 0)

        return blocks

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
            create_bullet,
            create_divider,
            create_heading,
            create_paragraph,
            create_todo,
            create_toggle,
            format_duration,
            parse_markdown_to_blocks,
        )

        children = []

        # 1. Summary — parsed from markdown into proper Notion blocks
        if self.summary:
            summary_blocks = parse_markdown_to_blocks(self.summary)
            if summary_blocks:
                children.extend(summary_blocks)

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

        # 3. Mind map outline (if available) — hierarchical breakdown
        if self.mind_map:
            mind_map_blocks = self._build_mind_map_tree()
            if mind_map_blocks:
                children.append(create_toggle("🧠 Mind Map", mind_map_blocks))

        # 4. Divider before metadata
        children.append(create_divider())

        # 5. Source details toggle (collapsed by default)
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
    pending: int = 0  # Summary not yet complete (will retry next sync)
    failed: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.created + self.skipped + self.pending + self.failed

    def __str__(self) -> str:
        parts = [f"Created: {self.created}", f"Skipped: {self.skipped}"]
        if self.pending > 0:
            parts.append(f"Pending: {self.pending}")
        if self.failed > 0:
            parts.append(f"Failed: {self.failed}")
        return ", ".join(parts)
