"""Pocket AI API client."""

import os
import requests
from datetime import datetime
from typing import Optional

from .models import ActionItem, Recording


# Base URL can be overridden via environment variable
# Default is a placeholder - user must set POCKET_API_URL if default doesn't work
DEFAULT_BASE_URL = "https://api.heypocket.com"
BASE_URL = os.getenv("POCKET_API_URL", DEFAULT_BASE_URL)


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

    def get_recordings(self, limit: int = 100) -> list[dict]:
        """Get all recordings."""
        data = self._request("GET", "/public/recordings", params={"limit": limit})
        return data.get("data", [])

    def get_recording(self, recording_id: str) -> dict:
        """Get a single recording with full details."""
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

    def fetch_all_action_items(self) -> list[ActionItem]:
        """Fetch all action items from all recordings."""
        action_items = []
        recordings = self.get_recordings()

        for rec in recordings:
            recording_id = rec.get("id")
            if not recording_id:
                continue

            # Get full recording details
            full_rec = self.get_recording(recording_id)
            items = self._extract_action_items(full_rec, recording_id)
            action_items.extend(items)

        return action_items

    def _extract_action_items(self, recording: dict, recording_id: str) -> list[ActionItem]:
        """Extract action items from a recording response."""
        items = []

        # Navigate to action items: data.summarizations.v2_action_items.actions[]
        summarizations = recording.get("summarizations", {})
        v2_actions = summarizations.get("v2_action_items", {})
        actions = v2_actions.get("actions", [])

        recording_title = recording.get("title") or recording.get("name")
        recording_created = recording.get("createdAt") or recording.get("created_at")

        for idx, action in enumerate(actions):
            # Generate unique pocket_id for deduplication
            # Use action's native ID if available, otherwise use index
            action_id = action.get("id") or f"{recording_id}:{idx}"
            pocket_id = f"pocket:{action_id}"

            # Parse due date if present
            due_date = None
            if action.get("dueDate"):
                try:
                    due_date = datetime.fromisoformat(action["dueDate"].replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass

            # Parse created date
            created_at = None
            if recording_created:
                try:
                    created_at = datetime.fromisoformat(recording_created.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass

            item = ActionItem(
                label=action.get("label", "Untitled Action"),
                pocket_id=pocket_id,
                recording_id=recording_id,
                priority=action.get("priority"),
                due_date=due_date,
                assignee=action.get("assignee"),
                context=action.get("context"),
                item_type=action.get("type"),
                recording_title=recording_title,
                created_at=created_at,
            )
            items.append(item)

        return items

    def test_connection(self) -> bool:
        """Test API connection."""
        try:
            self.get_recordings(limit=1)
            return True
        except requests.RequestException:
            return False
