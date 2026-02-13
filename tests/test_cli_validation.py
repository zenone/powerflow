"""Tests for CLI API key validation."""

from powerflow.cli import (
    validate_notion_key_format,
    validate_pocket_key_format,
)


class TestPocketKeyValidation:
    """Tests for Pocket API key format validation."""

    def test_valid_key_passes(self):
        """A reasonably long key should pass."""
        valid, error = validate_pocket_key_format("pk_" + "a" * 50)
        assert valid is True
        assert error == ""

    def test_empty_key_fails(self):
        """Empty key should fail."""
        valid, error = validate_pocket_key_format("")
        assert valid is False
        assert "empty" in error.lower()

    def test_short_key_fails(self):
        """Very short keys should fail."""
        valid, error = validate_pocket_key_format("abc123")
        assert valid is False
        assert "short" in error.lower()

    def test_key_with_space_fails(self):
        """Keys with spaces should fail."""
        # Key is long enough to pass length check, but has space
        valid, error = validate_pocket_key_format("pk_abc123defgh ijklmnopqrs")
        assert valid is False
        assert "whitespace" in error.lower()

    def test_key_with_newline_fails(self):
        """Keys with newlines should fail."""
        # Key is long enough to pass length check, but has newline
        valid, error = validate_pocket_key_format("pk_abc123defgh\nijklmnopqrs")
        assert valid is False
        assert "whitespace" in error.lower()


class TestNotionKeyValidation:
    """Tests for Notion API key format validation."""

    def test_valid_secret_key_passes(self):
        """Key starting with 'secret_' should pass."""
        valid, error = validate_notion_key_format("secret_" + "a" * 40)
        assert valid is True
        assert error == ""

    def test_valid_ntn_key_passes(self):
        """Key starting with 'ntn_' should pass."""
        valid, error = validate_notion_key_format("ntn_" + "a" * 40)
        assert valid is True
        assert error == ""

    def test_empty_key_fails(self):
        """Empty key should fail."""
        valid, error = validate_notion_key_format("")
        assert valid is False
        assert "empty" in error.lower()

    def test_wrong_prefix_fails(self):
        """Keys without correct prefix should fail."""
        valid, error = validate_notion_key_format("wrong_prefix_key_value")
        assert valid is False
        assert "secret_" in error or "ntn_" in error

    def test_short_key_fails(self):
        """Very short keys should fail."""
        valid, error = validate_notion_key_format("secret_abc")
        assert valid is False
        assert "short" in error.lower()

    def test_key_with_space_fails(self):
        """Keys with spaces should fail."""
        # Key is long enough to pass length check, but has space
        valid, error = validate_notion_key_format("secret_abc123defghijklmnop qrstuvwxyz")
        assert valid is False
        assert "whitespace" in error.lower()
