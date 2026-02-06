"""Core sync logic for Power-Flow."""

from typing import Optional

from .config import Config
from .models import ActionItem, SyncResult
from .notion import NotionClient
from .pocket import PocketClient


class SyncEngine:
    """Orchestrates sync between Pocket and Notion."""

    def __init__(
        self,
        pocket: PocketClient,
        notion: NotionClient,
        config: Config,
    ):
        self.pocket = pocket
        self.notion = notion
        self.config = config

    def sync(self, dry_run: bool = False) -> SyncResult:
        """
        Sync action items from Pocket to Notion.
        
        Args:
            dry_run: If True, don't actually create pages
            
        Returns:
            SyncResult with counts and any errors
        """
        result = SyncResult()

        if not self.config.is_configured:
            result.errors.append("Not configured. Run 'powerflow setup' first.")
            return result

        database_id = self.config.notion.database_id
        property_map = self.config.notion.property_map
        pocket_id_prop = property_map.get("pocket_id", "Inbox ID")

        # Fetch all action items from Pocket
        try:
            action_items = self.pocket.fetch_all_action_items()
        except Exception as e:
            result.errors.append(f"Failed to fetch from Pocket: {e}")
            return result

        # Process each action item
        for item in action_items:
            try:
                # Check for duplicate
                exists = self.notion.page_exists_by_pocket_id(
                    database_id, item.pocket_id, pocket_id_prop
                )

                if exists:
                    result.skipped += 1
                    continue

                # Create in Notion
                if not dry_run:
                    properties = item.to_notion_properties(property_map)
                    self.notion.create_page(database_id, properties)

                result.created += 1

            except Exception as e:
                result.failed += 1
                result.errors.append(f"Failed to sync '{item.label}': {e}")

        # Update last sync timestamp
        if not dry_run and result.created > 0:
            self.config.update_last_sync()

        return result

    def get_pending_count(self) -> int:
        """Get count of action items that would be synced (not yet in Notion)."""
        if not self.config.is_configured:
            return 0

        database_id = self.config.notion.database_id
        property_map = self.config.notion.property_map
        pocket_id_prop = property_map.get("pocket_id", "Inbox ID")

        action_items = self.pocket.fetch_all_action_items()
        pending = 0

        for item in action_items:
            exists = self.notion.page_exists_by_pocket_id(
                database_id, item.pocket_id, pocket_id_prop
            )
            if not exists:
                pending += 1

        return pending
