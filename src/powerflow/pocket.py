"""Pocket AI API client."""

import os
import requests
from datetime import datetime, timezone
from typing import Optional

from .models import ActionItem, Recording


# Base URL from official docs: https://docs.heypocketai.com/docs/api
DEFAULT_BASE_URL = "https://public.heypocketai.com/api/v1"
BASE_URL = os.getenv("POCKET_API_URL", DEFAULT_BASE_URL)

# Pocket web app URL for recording links
POCKET_WEB_URL = "https://heypocket.com"


def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Parse an ISO datetime string, handling timezone properly."""
    if not dt_str:
        return None
    try:
        # Handle Z suffix
        dt_str = dt_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(dt_str)
        # Ensure timezone-aware (assume UTC if naive)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, AttributeError):
        return None


class PocketClient:
    """Client for Pocket AI API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make an API request."""
        url = f"{BASE_URL}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()

    def get_recordings_list(self, limit: int = 100) -> list[dict]:
        """Get list of recordings (without full details)."""
        data = self._request("GET", "/public/recordings", params={"limit": limit})
        return data.get("data", [])

    def get_recording_details(self, recording_id: str) -> dict:
        """Get a single recording with full details including summarizations."""
        data = self._request("GET", f"/public/recordings/{recording_id}")
        return data.get("data", {})

    def get_tags(self) -> list[str]:
        """Get all tags."""
        data = self._request("GET", "/public/tags")
        return data.get("data", [])

    def search(self, query: str) -> list[dict]:
        """Semantic search across recordings."""
        data = self._request("POST", "/public/search", json={"query": query})
        return data.get("data", [])

    def fetch_recordings(self, since: Optional[datetime] = None) -> list[Recording]:
        """
        Fetch all recordings, optionally filtered by created_at timestamp.
        
        Args:
            since: Only fetch recordings created after this time. If None, fetch all.
            
        Returns:
            List of Recording objects with full details.
        """
        recordings = []
        raw_list = self.get_recordings_list()

        for rec in raw_list:
            recording_id = rec.get("id")
            if not recording_id:
                continue

            # Filter by created_at if since is provided
            if since:
                rec_created = parse_datetime(rec.get("createdAt") or rec.get("created_at"))
                if rec_created and rec_created <= since:
                    continue  # Skip recordings before since

            # Get full recording details
            try:
                full_rec = self.get_recording_details(recording_id)
                recording = self._parse_recording(full_rec)
                if recording:
                    recordings.append(recording)
            except requests.RequestException:
                # Skip failed fetches, continue with others
                continue

        return recordings

    def _parse_recording(self, data: dict) -> Optional[Recording]:
        """Parse raw API response into a Recording object."""
        recording_id = data.get("id")
        if not recording_id:
            return None

        # Extract basic fields
        title = data.get("title") or data.get("name")
        created_at = parse_datetime(data.get("createdAt") or data.get("created_at"))
        
        # Duration
        duration_seconds = None
        duration_raw = data.get("duration") or data.get("durationSeconds")
        if duration_raw:
            try:
                duration_seconds = int(duration_raw)
            except (ValueError, TypeError):
                pass

        # Tags
        tags = []
        tags_data = data.get("tags") or []
        for tag in tags_data:
            if isinstance(tag, dict):
                tag_name = tag.get("name") or tag.get("label")
            else:
                tag_name = str(tag)
            if tag_name:
                tags.append(tag_name)

        # Transcript
        transcript = None
        transcript_data = data.get("transcript", {})
        if isinstance(transcript_data, dict):
            transcript = transcript_data.get("text")

        # Summarizations
        summarizations = data.get("summarizations", {})
        
        # Summary (API returns markdown field, not summary)
        summary = None
        v2_summary = summarizations.get("v2_summary", {})
        if isinstance(v2_summary, dict):
            summary = v2_summary.get("markdown") or v2_summary.get("summary")
        
        # Mind map (hierarchical outline)
        mind_map_nodes = []
        v2_mind_map = summarizations.get("v2_mind_map", {})
        if isinstance(v2_mind_map, dict):
            mind_map_nodes = v2_mind_map.get("nodes", [])

        # Action items
        action_items = []
        v2_actions = summarizations.get("v2_action_items", {})
        actions_list = v2_actions.get("actions", []) if isinstance(v2_actions, dict) else []
        
        for action in actions_list:
            if not isinstance(action, dict):
                continue
                
            due_date = None
            if action.get("dueDate"):
                due_date = parse_datetime(action["dueDate"])

            item = ActionItem(
                label=action.get("label", "Untitled Action"),
                priority=action.get("priority"),
                due_date=due_date,
                assignee=action.get("assignee"),
                context=action.get("context"),
                item_type=action.get("type"),
            )
            action_items.append(item)

        # Build recording URL
        pocket_url = f"{POCKET_WEB_URL}/recordings/{recording_id}"

        return Recording(
            id=recording_id,
            title=title,
            summary=summary,
            transcript=transcript,
            tags=tags,
            action_items=action_items,
            mind_map=mind_map_nodes,
            created_at=created_at,
            duration_seconds=duration_seconds,
            pocket_url=pocket_url,
        )

    def test_connection(self) -> bool:
        """Test API connection."""
        try:
            self.get_recordings_list(limit=1)
            return True
        except requests.RequestException:
            return False
