"""Tests for Notion block builders."""

import pytest

from powerflow.blocks import (
    safe_text,
    format_duration,
    create_rich_text,
    create_callout,
    create_divider,
    create_toggle,
    create_bullet,
    create_paragraph,
    create_quote,
    create_heading,
    get_priority_style,
    PRIORITY_STYLES,
)


class TestSafeText:
    """Tests for safe_text function."""

    def test_returns_empty_for_none(self):
        assert safe_text(None) == ""

    def test_returns_empty_for_empty_string(self):
        assert safe_text("") == ""

    def test_returns_unchanged_for_short_text(self):
        text = "Hello world"
        assert safe_text(text) == text

    def test_truncates_long_text_with_ellipsis(self):
        text = "x" * 2000
        result = safe_text(text, max_length=100)
        assert len(result) == 100
        assert result.endswith("...")

    def test_respects_custom_max_length(self):
        text = "x" * 100
        result = safe_text(text, max_length=50)
        assert len(result) == 50


class TestFormatDuration:
    """Tests for format_duration function."""

    def test_returns_unknown_for_none(self):
        assert format_duration(None) == "Unknown"

    def test_returns_unknown_for_negative(self):
        assert format_duration(-1) == "Unknown"

    def test_formats_seconds_only(self):
        assert format_duration(45) == "0:45"

    def test_formats_minutes_and_seconds(self):
        assert format_duration(125) == "2:05"

    def test_formats_hours_minutes_seconds(self):
        assert format_duration(3725) == "1:02:05"


class TestCreateRichText:
    """Tests for create_rich_text function."""

    def test_basic_text(self):
        result = create_rich_text("Hello")
        assert result["type"] == "text"
        assert result["text"]["content"] == "Hello"
        assert "annotations" not in result  # No annotations for default

    def test_bold_text(self):
        result = create_rich_text("Hello", bold=True)
        assert result["annotations"]["bold"] is True

    def test_text_with_link(self):
        result = create_rich_text("Click here", link="https://example.com")
        assert result["text"]["link"]["url"] == "https://example.com"

    def test_colored_text(self):
        result = create_rich_text("Hello", color="red")
        assert result["annotations"]["color"] == "red"


class TestCreateCallout:
    """Tests for create_callout function."""

    def test_basic_callout(self):
        result = create_callout("Important note")
        assert result["type"] == "callout"
        assert result["callout"]["icon"]["emoji"] == "💡"
        assert result["callout"]["color"] == "default"

    def test_custom_icon_and_color(self):
        result = create_callout("Alert!", icon="🔥", color="red_background")
        assert result["callout"]["icon"]["emoji"] == "🔥"
        assert result["callout"]["color"] == "red_background"


class TestCreateDivider:
    """Tests for create_divider function."""

    def test_divider_structure(self):
        result = create_divider()
        assert result["type"] == "divider"
        assert result["divider"] == {}


class TestCreateToggle:
    """Tests for create_toggle function."""

    def test_toggle_with_children(self):
        children = [create_paragraph("Child content")]
        result = create_toggle("Click to expand", children)
        
        assert result["type"] == "toggle"
        assert result["toggle"]["rich_text"][0]["text"]["content"] == "Click to expand"
        assert len(result["toggle"]["children"]) == 1


class TestCreateBullet:
    """Tests for create_bullet function."""

    def test_simple_bullet(self):
        result = create_bullet("Item text")
        assert result["type"] == "bulleted_list_item"
        assert len(result["bulleted_list_item"]["rich_text"]) == 1

    def test_bullet_with_bold_prefix(self):
        result = create_bullet("value", bold_prefix="Label")
        rich_text = result["bulleted_list_item"]["rich_text"]
        assert len(rich_text) == 2
        assert rich_text[0]["annotations"]["bold"] is True
        assert rich_text[0]["text"]["content"] == "Label: "


class TestCreateParagraph:
    """Tests for create_paragraph function."""

    def test_basic_paragraph(self):
        result = create_paragraph("Some text")
        assert result["type"] == "paragraph"
        assert result["paragraph"]["rich_text"][0]["text"]["content"] == "Some text"

    def test_paragraph_with_link(self):
        result = create_paragraph("Click here", link="https://example.com")
        assert result["paragraph"]["rich_text"][0]["text"]["link"]["url"] == "https://example.com"


class TestCreateQuote:
    """Tests for create_quote function."""

    def test_basic_quote(self):
        result = create_quote("Famous words")
        assert result["type"] == "quote"
        assert result["quote"]["rich_text"][0]["text"]["content"] == "Famous words"


class TestCreateHeading:
    """Tests for create_heading function."""

    def test_heading_1(self):
        result = create_heading("Title", level=1)
        assert result["type"] == "heading_1"

    def test_heading_2(self):
        result = create_heading("Subtitle", level=2)
        assert result["type"] == "heading_2"

    def test_heading_clamps_to_valid_range(self):
        result = create_heading("Test", level=5)
        assert result["type"] == "heading_3"  # Clamped to max


class TestGetPriorityStyle:
    """Tests for get_priority_style function."""

    def test_high_priority(self):
        style = get_priority_style("High")
        assert style["icon"] == "🔥"
        assert style["color"] == "red_background"

    def test_medium_priority(self):
        style = get_priority_style("Medium")
        assert style["icon"] == "⚡"
        assert style["color"] == "yellow_background"

    def test_low_priority(self):
        style = get_priority_style("Low")
        assert style["icon"] == "📝"
        assert style["color"] == "gray_background"

    def test_none_priority(self):
        style = get_priority_style(None)
        assert style["icon"] == "💡"
        assert style["color"] == "default"

    def test_case_insensitive(self):
        style = get_priority_style("high")
        assert style["icon"] == "🔥"  # Title-cased to "High"

    def test_unknown_priority_defaults(self):
        style = get_priority_style("critical")
        assert style["icon"] == "💡"  # Falls back to None style
