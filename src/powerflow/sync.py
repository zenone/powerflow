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
        
        Uses incremental sync (only fetch new recordings) and batch dedup
        (check multiple pocket_ids in one query) for efficiency.
        
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

        # Get last sync timestamp for incremental sync
        last_sync = getattr(self.config.pocket, 'last_sync', None)

        # Fetch action items since last sync (or all if first sync)
        try:
            action_items = self.pocket.fetch_action_items_since(last_sync)
        except Exception as e:
            result.errors.append(f"Failed to fetch from Pocket: {e}")
            return result

        if not action_items:
            return result

        # Batch check which items already exist
        pocket_ids = [item.pocket_id for item in action_items]
        try:
            existing_ids = self.notion.batch_check_existing_pocket_ids(
                database_id, pocket_ids, pocket_id_prop
            )
        except Exception as e:
            result.errors.append(f"Failed to check existing items: {e}")
            return result

        # Process each action item
        for item in action_items:
            try:
                # Check for duplicate using batch result
                if item.pocket_id in existing_ids:
                    result.skipped += 1
                    continue

                # Create in Notion with rich body content
                if not dry_run:
                    properties = item.to_notion_properties(property_map)
                    children = item.to_notion_children()
                    self.notion.create_page(database_id, properties, children)

                result.created += 1

            except Exception as e:
                result.failed += 1
                result.errors.append(f"Failed to sync '{item.label}': {e}")

        # Update last sync timestamp
        if not dry_run and (result.created > 0 or result.skipped > 0):
            self.config.update_last_sync()

        return result

    def get_pending_count(self) -> int:
        """Get count of action items that would be synced (not yet in Notion)."""
        if not self.config.is_configured:
            return 0

        database_id = self.config.notion.database_id
        property_map = self.config.notion.property_map
        pocket_id_prop = property_map.get("pocket_id", "Inbox ID")
        last_sync = getattr(self.config.pocket, 'last_sync', None)

        action_items = self.pocket.fetch_action_items_since(last_sync)
        
        if not action_items:
            return 0

        # Batch check existing
        pocket_ids = [item.pocket_id for item in action_items]
        existing_ids = self.notion.batch_check_existing_pocket_ids(
            database_id, pocket_ids, pocket_id_prop
        )

        return len(action_items) - len(existing_ids)
