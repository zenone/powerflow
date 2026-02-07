"""Core sync logic for Power-Flow."""

from datetime import datetime, timezone
from typing import Optional

from .config import Config
from .models import Recording, SyncResult
from .notion import NotionClient
from .pocket import PocketClient


def parse_last_sync(last_sync: Optional[str]) -> Optional[datetime]:
    """Parse last_sync string into timezone-aware datetime."""
    if not last_sync:
        return None
    try:
        dt = datetime.fromisoformat(last_sync.replace("Z", "+00:00"))
        # Ensure timezone-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, AttributeError):
        return None


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
        Sync recordings from Pocket to Notion.
        
        Each recording becomes an Inbox item. The user then processes/triages
        it into a task, note, project, or archives it.
        
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
        last_sync = parse_last_sync(self.config.pocket.last_sync)

        # Fetch recordings since last sync (or all if first sync)
        try:
            recordings = self.pocket.fetch_recordings(since=last_sync)
        except Exception as e:
            result.errors.append(f"Failed to fetch from Pocket: {e}")
            return result

        if not recordings:
            return result

        # Batch check which recordings already exist
        pocket_ids = [rec.pocket_id for rec in recordings]
        try:
            existing_ids = self.notion.batch_check_existing_pocket_ids(
                database_id, pocket_ids, pocket_id_prop
            )
        except Exception as e:
            result.errors.append(f"Failed to check existing items: {e}")
            return result

        # Process each recording
        for recording in recordings:
            try:
                # Check for duplicate using batch result
                if recording.pocket_id in existing_ids:
                    result.skipped += 1
                    continue

                # Create in Notion with rich body content and icon
                if not dry_run:
                    properties = recording.to_notion_properties(property_map)
                    children = recording.to_notion_children()
                    icon = recording.get_icon()
                    self.notion.create_page(database_id, properties, children, icon)

                result.created += 1

            except Exception as e:
                result.failed += 1
                result.errors.append(f"Failed to sync '{recording.display_title}': {e}")

        # Update last sync timestamp
        if not dry_run and (result.created > 0 or result.skipped > 0):
            self.config.update_last_sync()

        return result

    def get_pending_count(self) -> int:
        """Get count of recordings that would be synced (not yet in Notion)."""
        if not self.config.is_configured:
            return 0

        database_id = self.config.notion.database_id
        property_map = self.config.notion.property_map
        pocket_id_prop = property_map.get("pocket_id", "Inbox ID")
        last_sync = parse_last_sync(self.config.pocket.last_sync)

        try:
            recordings = self.pocket.fetch_recordings(since=last_sync)
        except Exception:
            return 0
        
        if not recordings:
            return 0

        # Batch check existing
        pocket_ids = [rec.pocket_id for rec in recordings]
        try:
            existing_ids = self.notion.batch_check_existing_pocket_ids(
                database_id, pocket_ids, pocket_id_prop
            )
        except Exception:
            return len(recordings)  # Assume all are new if check fails

        return len(recordings) - len(existing_ids)
