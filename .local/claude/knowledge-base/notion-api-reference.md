# Notion API Reference for Power-Flow

## Overview

Power-Flow uses the Notion API (v2022-06-28) to create rich, visually stunning pages.

This document captures Notion-specific patterns for creating Michelin-star quality integrations.

---

## API Limits & Constraints

| Limit | Value | Impact |
|-------|-------|--------|
| Rate limit | ~3 req/sec average | Batch operations, add delays |
| Rich text content | 2000 chars max | Truncate gracefully |
| Page properties | 100 max per DB | Plan property schema carefully |
| Blocks per request | 100 max children | Paginate large appends |
| Title length | 2000 chars | Truncate with "..." |

---

## Block Types for Rich Pages

### Callout (Context/Highlights)

Perfect for surfacing key information with visual emphasis.

```python
def create_callout_block(text: str, icon: str = "💡", color: str = "yellow_background") -> dict:
    """Create a callout block with icon and color."""
    return {
        "type": "callout",
        "callout": {
            "icon": {"type": "emoji", "emoji": icon},
            "color": color,
            "rich_text": [{"type": "text", "text": {"content": text}}]
        }
    }
```

**Color options**: `default`, `gray_background`, `brown_background`, `orange_background`, `yellow_background`, `green_background`, `blue_background`, `purple_background`, `pink_background`, `red_background`

### Toggle (Collapsible Details)

Hide verbose information by default, user expands when needed.

```python
def create_toggle_block(title: str, children: list[dict]) -> dict:
    """Create a toggle block with nested children."""
    return {
        "type": "toggle",
        "toggle": {
            "rich_text": [{"type": "text", "text": {"content": title}}],
            "children": children
        }
    }
```

### Quote (Transcript Excerpts)

For displaying source quotes or transcript snippets.

```python
def create_quote_block(text: str, color: str = "default") -> dict:
    """Create a quote block."""
    return {
        "type": "quote",
        "quote": {
            "rich_text": [{"type": "text", "text": {"content": text}}],
            "color": color
        }
    }
```

### Divider

Visual separator between sections.

```python
def create_divider() -> dict:
    return {"type": "divider", "divider": {}}
```

### Bulleted List

Clean metadata display.

```python
def create_bullet(text: str, bold_prefix: str = None) -> dict:
    """Create a bulleted list item, optionally with bold prefix."""
    rich_text = []
    if bold_prefix:
        rich_text.append({
            "type": "text",
            "text": {"content": f"{bold_prefix}: "},
            "annotations": {"bold": True}
        })
    rich_text.append({"type": "text", "text": {"content": text}})
    
    return {
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": rich_text}
    }
```

### Paragraph with Link

```python
def create_paragraph_with_link(text: str, url: str, link_text: str) -> dict:
    """Create a paragraph with an inline link."""
    return {
        "type": "paragraph",
        "paragraph": {
            "rich_text": [
                {"type": "text", "text": {"content": text}},
                {
                    "type": "text",
                    "text": {"content": link_text, "link": {"url": url}},
                    "annotations": {"color": "blue"}
                }
            ]
        }
    }
```

---

## Rich Text Annotations

Apply styling to text within any rich_text array:

```python
{
    "type": "text",
    "text": {"content": "Important!"},
    "annotations": {
        "bold": True,
        "italic": False,
        "strikethrough": False,
        "underline": False,
        "code": False,
        "color": "red"  # or "red_background"
    }
}
```

**Colors**: `default`, `gray`, `brown`, `orange`, `yellow`, `green`, `blue`, `purple`, `pink`, `red` (and `*_background` variants)

---

## Page Creation Pattern

### Properties + Children (Body Content)

The Notion API's create page endpoint accepts both:
- `properties`: Database row fields
- `children`: Page body blocks

```python
def create_page_with_body(
    database_id: str,
    properties: dict,
    children: list[dict]
) -> dict:
    """Create a page with both properties and body content."""
    payload = {
        "parent": {"database_id": database_id},
        "properties": properties,
        "children": children
    }
    return self._request("POST", "/pages", json=payload)
```

---

## Power-Flow Page Structure

### Standard Action Item Page

```
[Properties: Title, Priority, Due Date, Status, Tags, Inbox ID, Source URL]

[Body:]
├── Callout: Context (priority-colored)
├── Divider
└── Toggle: "Source Details"
    ├── Bullet: "Recording: {title}"
    ├── Bullet: "Duration: {duration}"
    ├── Bullet: "Created: {date}"
    └── Paragraph: "🔗 Open in Pocket" (linked)
```

### Priority-Based Styling

```python
PRIORITY_STYLES = {
    "High": {"icon": "🔥", "color": "red_background"},
    "Medium": {"icon": "⚡", "color": "yellow_background"},
    "Low": {"icon": "📝", "color": "gray_background"},
    None: {"icon": "💡", "color": "default"},
}

def get_context_callout(context: str, priority: str) -> dict:
    style = PRIORITY_STYLES.get(priority, PRIORITY_STYLES[None])
    return create_callout_block(context, icon=style["icon"], color=style["color"])
```

---

## Batch Operations

### Query Multiple Pocket IDs at Once

Instead of N queries for N items, use a compound OR filter:

```python
def get_existing_pocket_ids(self, database_id: str, pocket_ids: list[str]) -> set[str]:
    """Batch check which pocket_ids already exist."""
    if not pocket_ids:
        return set()
    
    # Notion compound filter: OR of all pocket_id equals
    filter_obj = {
        "or": [
            {"property": "Inbox ID", "rich_text": {"equals": pid}}
            for pid in pocket_ids[:100]  # Notion limit
        ]
    }
    
    results = self.query_database(database_id, filter_obj)
    existing = set()
    for page in results:
        inbox_id = page["properties"].get("Inbox ID", {})
        rich_text = inbox_id.get("rich_text", [])
        if rich_text:
            existing.add(rich_text[0]["plain_text"])
    
    return existing
```

**Note**: Notion OR filters limited to ~100 conditions. For larger batches, chunk and merge.

---

## Error Handling

### Rate Limit Response

```python
if response.status_code == 429:
    retry_after = int(response.headers.get("Retry-After", 1))
    time.sleep(retry_after)
    # Retry request
```

### Rich Text Truncation

```python
def safe_text(text: str, max_length: int = 1900) -> str:
    """Safely truncate text for Notion rich_text (2000 char limit)."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
```

---

## Future: Appending Blocks to Existing Pages

For updating page content (not properties):

```python
def append_blocks(self, page_id: str, children: list[dict]) -> dict:
    """Append blocks to an existing page."""
    return self._request(
        "PATCH",
        f"/blocks/{page_id}/children",
        json={"children": children}
    )
```

---

## References

- [Notion API: Rich Text](https://developers.notion.com/reference/rich-text)
- [Notion API: Block Types](https://developers.notion.com/reference/block)
- [Notion API: Working with Page Content](https://developers.notion.com/guides/data-apis/working-with-page-content)
- [Rate Limits](https://developers.notion.com/reference/errors#rate-limits)

---

## Markdown to Notion Blocks (2026-02-06)

### Problem
Notion doesn't render markdown syntax. Raw `###` and `**` appear as text.

### Solution
Parse markdown and create native Notion blocks:

| Markdown | Notion Block |
|----------|--------------|
| `### Heading` | `heading_3` block |
| `- Item` | `bulleted_list_item` block |
| `**bold**` | `rich_text` with `annotations.bold: true` |

### Bold Text Pattern

```python
# Parse **bold** markers into proper rich_text array
def parse_bold_segments(text: str) -> list[dict]:
    import re
    rich_text = []
    pattern = r'\*\*([^*]+)\*\*'
    last_end = 0
    
    for match in re.finditer(pattern, text):
        # Non-bold text before match
        if match.start() > last_end:
            rich_text.append({"type": "text", "text": {"content": text[last_end:match.start()]}})
        
        # Bold text
        rich_text.append({
            "type": "text",
            "text": {"content": match.group(1)},
            "annotations": {"bold": True}
        })
        last_end = match.end()
    
    # Remaining non-bold text
    if last_end < len(text):
        rich_text.append({"type": "text", "text": {"content": text[last_end:]}})
    
    return rich_text
```

### Usage

```python
# Instead of raw markdown in a callout:
# callout(markdown_text)  # BAD - shows raw ###, **

# Parse into blocks:
blocks = parse_markdown_to_blocks(markdown_text)
# Returns: [heading_3, bullet, bullet, heading_3, ...]
```
