"""Notion block builders for rich page content.

This module provides functions to create visually stunning Notion blocks
following Michelin-star attention to detail.
"""

from typing import Optional


# Priority-based visual styling
PRIORITY_STYLES = {
    "High": {"icon": "🔥", "color": "red_background"},
    "Medium": {"icon": "⚡", "color": "yellow_background"},
    "Low": {"icon": "📝", "color": "gray_background"},
    None: {"icon": "💡", "color": "default"},
}


def safe_text(text: str, max_length: int = 1900) -> str:
    """Safely truncate text for Notion's 2000 char limit per rich_text block."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_duration(seconds: int) -> str:
    """Format seconds as human-readable duration (e.g., '2:34' or '1:05:23')."""
    if not seconds or seconds < 0:
        return "Unknown"
    if seconds < 60:
        return f"0:{seconds:02d}"
    minutes, secs = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}:{secs:02d}"
    hours, mins = divmod(minutes, 60)
    return f"{hours}:{mins:02d}:{secs:02d}"


def create_rich_text(content: str, bold: bool = False, italic: bool = False, 
                     color: str = "default", link: Optional[str] = None) -> dict:
    """Create a rich text object with optional styling."""
    text_obj = {"content": safe_text(content)}
    if link:
        text_obj["link"] = {"url": link}
    
    result = {
        "type": "text",
        "text": text_obj,
    }
    
    # Only add annotations if non-default
    if bold or italic or color != "default":
        result["annotations"] = {
            "bold": bold,
            "italic": italic,
            "strikethrough": False,
            "underline": False,
            "code": False,
            "color": color,
        }
    
    return result


def create_callout(
    text: str,
    icon: str = "💡",
    color: str = "default"
) -> dict:
    """Create a callout block with icon and colored background.
    
    Callouts are perfect for highlighting important context or notes.
    """
    return {
        "type": "callout",
        "callout": {
            "icon": {"type": "emoji", "emoji": icon},
            "color": color,
            "rich_text": [create_rich_text(text)]
        }
    }


def create_divider() -> dict:
    """Create a horizontal divider block."""
    return {"type": "divider", "divider": {}}


def create_toggle(title: str, children: list[dict]) -> dict:
    """Create a toggle block with nested children (collapsed by default)."""
    return {
        "type": "toggle",
        "toggle": {
            "rich_text": [create_rich_text(title)],
            "children": children
        }
    }


def create_bullet(text: str, bold_prefix: Optional[str] = None) -> dict:
    """Create a bulleted list item, optionally with a bold label prefix.
    
    Example: create_bullet("Morning voice note", "Recording")
    Renders as: • **Recording:** Morning voice note
    """
    rich_text = []
    
    if bold_prefix:
        rich_text.append(create_rich_text(f"{bold_prefix}: ", bold=True))
        rich_text.append(create_rich_text(text))
    else:
        rich_text.append(create_rich_text(text))
    
    return {
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": rich_text
        }
    }


def create_paragraph(text: str, link: Optional[str] = None, color: str = "default") -> dict:
    """Create a paragraph block, optionally as a link."""
    return {
        "type": "paragraph",
        "paragraph": {
            "rich_text": [create_rich_text(text, color=color, link=link)]
        }
    }


def create_quote(text: str, color: str = "default") -> dict:
    """Create a quote block for citations or transcript excerpts."""
    return {
        "type": "quote",
        "quote": {
            "rich_text": [create_rich_text(text)],
            "color": color
        }
    }


def create_heading(text: str, level: int = 2, color: str = "default") -> dict:
    """Create a heading block (level 1, 2, or 3)."""
    level = max(1, min(3, level))  # Clamp to 1-3
    heading_key = f"heading_{level}"
    
    return {
        "type": heading_key,
        heading_key: {
            "rich_text": [create_rich_text(text)],
            "color": color,
            "is_toggleable": False
        }
    }


def get_priority_style(priority: Optional[str]) -> dict:
    """Get the visual style for a given priority level."""
    # Normalize priority string
    if priority:
        priority = priority.strip().title()
        if priority not in PRIORITY_STYLES:
            priority = None
    return PRIORITY_STYLES.get(priority, PRIORITY_STYLES[None])
