"""Notion API client."""

import requests
from typing import Optional

from .models import ActionItem


BASE_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


class NotionClient:
    """Client for Notion API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        })

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make an API request."""
        url = f"{BASE_URL}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()

    def search_databases(self) -> list[dict]:
        """Search for all databases the integration can access."""
        results = []
        has_more = True
        start_cursor = None

        while has_more:
            payload = {
                "filter": {"property": "object", "value": "database"},
            }
            if start_cursor:
                payload["start_cursor"] = start_cursor

            data = self._request("POST", "/search", json=payload)
            results.extend(data.get("results", []))
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")

        return results

    def get_database(self, database_id: str) -> dict:
        """Get database details including schema."""
        return self._request("GET", f"/databases/{database_id}")

    def get_database_schema(self, database_id: str) -> dict[str, dict]:
        """Get database property schema."""
        db = self.get_database(database_id)
        return db.get("properties", {})

    def query_database(
        self,
        database_id: str,
        filter_obj: Optional[dict] = None,
        page_size: int = 100,
    ) -> list[dict]:
        """Query database pages."""
        results = []
        has_more = True
        start_cursor = None

        while has_more:
            payload = {"page_size": page_size}
            if filter_obj:
                payload["filter"] = filter_obj
            if start_cursor:
                payload["start_cursor"] = start_cursor

            data = self._request("POST", f"/databases/{database_id}/query", json=payload)
            results.extend(data.get("results", []))
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")

        return results

    def page_exists_by_pocket_id(
        self,
        database_id: str,
        pocket_id: str,
        pocket_id_property: str = "Inbox ID",
    ) -> bool:
        """Check if a page with this pocket_id already exists."""
        filter_obj = {
            "property": pocket_id_property,
            "rich_text": {"equals": pocket_id},
        }
        results = self.query_database(database_id, filter_obj, page_size=1)
        return len(results) > 0

    def create_page(
        self,
        database_id: str,
        properties: dict,
        children: list[dict] = None,
    ) -> dict:
        """Create a new page in the database with optional body content.
        
        Args:
            database_id: Target database ID
            properties: Page properties (database fields)
            children: Optional list of block objects for page body content
        
        Returns:
            Created page object
        """
        payload = {
            "parent": {"database_id": database_id},
            "properties": properties,
        }
        if children:
            payload["children"] = children
        return self._request("POST", "/pages", json=payload)

    def create_property(
        self,
        database_id: str,
        property_name: str,
        property_type: str,
    ) -> dict:
        """Add a new property to a database."""
        # Build property config based on type
        property_config: dict = {}
        if property_type == "rich_text":
            property_config = {"rich_text": {}}
        elif property_type == "url":
            property_config = {"url": {}}
        elif property_type == "select":
            property_config = {"select": {"options": []}}
        elif property_type == "date":
            property_config = {"date": {}}
        elif property_type == "checkbox":
            property_config = {"checkbox": {}}
        else:
            property_config = {"rich_text": {}}  # Default to rich_text

        payload = {
            "properties": {
                property_name: property_config,
            }
        }
        return self._request("PATCH", f"/databases/{database_id}", json=payload)

    def ensure_properties_exist(
        self,
        database_id: str,
        required_properties: dict[str, str],
    ) -> list[str]:
        """
        Ensure required properties exist in database.
        
        Args:
            database_id: Database to check
            required_properties: Dict of property_name -> property_type
        
        Returns:
            List of created property names
        """
        schema = self.get_database_schema(database_id)
        existing = set(schema.keys())
        created = []

        for prop_name, prop_type in required_properties.items():
            if prop_name not in existing:
                self.create_property(database_id, prop_name, prop_type)
                created.append(prop_name)

        return created

    def test_connection(self) -> bool:
        """Test API connection."""
        try:
            self.search_databases()
            return True
        except requests.RequestException:
            return False

    def format_databases_for_display(self, databases: list[dict]) -> list[dict]:
        """Format database list for CLI display."""
        formatted = []
        for db in databases:
            title_parts = db.get("title", [])
            title = title_parts[0].get("plain_text", "Untitled") if title_parts else "Untitled"
            icon = db.get("icon", {})
            emoji = icon.get("emoji", "📄") if icon and icon.get("type") == "emoji" else "📄"

            formatted.append({
                "id": db["id"],
                "title": title,
                "emoji": emoji,
                "url": db.get("url", ""),
            })
        return formatted
