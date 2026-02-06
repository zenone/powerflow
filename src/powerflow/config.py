"""Configuration management for Power-Flow."""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


CONFIG_DIR = Path.home() / ".powerflow"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class NotionConfig:
    """Notion-specific configuration."""

    database_id: Optional[str] = None
    database_name: Optional[str] = None
    property_map: dict = field(default_factory=lambda: {
        "title": "Name",
        "pocket_id": "Inbox ID",
        "priority": "Priority",
        "due_date": "Due Date",
        "context": "Context",
        "source_url": "Source",
    })


@dataclass
class PocketConfig:
    """Pocket-specific configuration."""

    last_sync: Optional[str] = None  # ISO timestamp


@dataclass
class Config:
    """Main configuration."""

    notion: NotionConfig = field(default_factory=NotionConfig)
    pocket: PocketConfig = field(default_factory=PocketConfig)
    created_at: Optional[str] = None

    @classmethod
    def load(cls) -> "Config":
        """Load config from file, or return defaults."""
        if not CONFIG_FILE.exists():
            return cls()

        try:
            data = json.loads(CONFIG_FILE.read_text())
            return cls(
                notion=NotionConfig(**data.get("notion", {})),
                pocket=PocketConfig(**data.get("pocket", {})),
                created_at=data.get("created_at"),
            )
        except (json.JSONDecodeError, TypeError) as e:
            print(f"⚠️  Config file corrupted, using defaults: {e}")
            return cls()

    def save(self) -> None:
        """Save config to file."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        if not self.created_at:
            self.created_at = datetime.now().isoformat()

        data = {
            "notion": asdict(self.notion),
            "pocket": asdict(self.pocket),
            "created_at": self.created_at,
        }

        CONFIG_FILE.write_text(json.dumps(data, indent=2))

    def update_last_sync(self) -> None:
        """Update last sync timestamp and save."""
        self.pocket.last_sync = datetime.now().isoformat()
        self.save()

    @property
    def is_configured(self) -> bool:
        """Check if setup has been completed."""
        return bool(self.notion.database_id)


def get_pocket_api_key() -> Optional[str]:
    """Get Pocket API key from environment."""
    return os.getenv("POCKET_API_KEY")


def get_notion_api_key() -> Optional[str]:
    """Get Notion API key from environment."""
    return os.getenv("NOTION_API_KEY")


def validate_env() -> list[str]:
    """Validate required environment variables. Returns list of missing vars."""
    missing = []
    if not get_pocket_api_key():
        missing.append("POCKET_API_KEY")
    if not get_notion_api_key():
        missing.append("NOTION_API_KEY")
    return missing
