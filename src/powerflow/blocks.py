"""Notion block builders for rich page content.

This module provides functions to create visually stunning Notion blocks
following Michelin-star attention to detail.
"""


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
                     color: str = "default", link: str | None = None) -> dict:
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


def create_bullet(text: str, bold_prefix: str | None = None) -> dict:
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


def create_paragraph(text: str, link: str | None = None, color: str = "default") -> dict:
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


def create_todo(text: str, checked: bool = False) -> dict:
    """Create a to-do checkbox block."""
    return {
        "type": "to_do",
        "to_do": {
            "rich_text": [create_rich_text(text)],
            "checked": checked,
            "color": "default"
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


def get_priority_style(priority: str | None) -> dict:
    """Get the visual style for a given priority level."""
    # Normalize priority string
    if priority:
        priority = priority.strip().title()
        if priority not in PRIORITY_STYLES:
            priority = None
    return PRIORITY_STYLES.get(priority, PRIORITY_STYLES[None])


def parse_bold_segments(text: str) -> list[dict]:
    """Parse **bold** markers and return rich_text array with proper annotations.

    Example: "Hello **world** and **foo**"
    Returns: [{"text": "Hello "}, {"text": "world", bold}, {"text": " and "}, {"text": "foo", bold}]
    """
    import re
    rich_text = []

    # Pattern matches **text**
    pattern = r'\*\*([^*]+)\*\*'
    last_end = 0

    for match in re.finditer(pattern, text):
        # Add text before the match (non-bold)
        if match.start() > last_end:
            before = text[last_end:match.start()]
            if before:
                rich_text.append(create_rich_text(before))

        # Add the bold text
        bold_text = match.group(1)
        rich_text.append(create_rich_text(bold_text, bold=True))

        last_end = match.end()

    # Add remaining text after last match
    if last_end < len(text):
        remaining = text[last_end:]
        if remaining:
            rich_text.append(create_rich_text(remaining))

    # If no matches, return the whole text as-is
    if not rich_text:
        rich_text.append(create_rich_text(text))

    return rich_text


def create_bullet_with_markdown(text: str) -> dict:
    """Create a bullet with **bold** markers parsed properly."""
    return {
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": parse_bold_segments(text)
        }
    }


def parse_markdown_to_blocks(markdown: str) -> list[dict]:
    """Parse Pocket's markdown summary into proper Notion blocks.

    Handles:
    - ### Headings → heading_3 blocks
    - - Bullet items → bulleted_list_item blocks
    - **bold** → bold annotations
    - Regular paragraphs → paragraph blocks

    Returns a list of Notion block objects.
    """
    if not markdown:
        return []

    blocks = []
    lines = markdown.strip().split('\n')

    for line in lines:
        line = line.rstrip()

        # Skip empty lines
        if not line.strip():
            continue

        # Heading (### text)
        if line.startswith('### '):
            heading_text = line[4:].strip()
            blocks.append({
                "type": "heading_3",
                "heading_3": {
                    "rich_text": parse_bold_segments(heading_text),
                    "color": "default",
                    "is_toggleable": False
                }
            })

        # Bullet point (- text or  - text for indented)
        elif line.lstrip().startswith('- '):
            # Remove leading whitespace and the "- "
            bullet_text = line.lstrip()[2:].strip()
            blocks.append({
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": parse_bold_segments(bullet_text)
                }
            })

        # Regular paragraph
        else:
            blocks.append({
                "type": "paragraph",
                "paragraph": {
                    "rich_text": parse_bold_segments(line)
                }
            })

    return blocks
