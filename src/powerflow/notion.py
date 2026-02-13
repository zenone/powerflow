"""Notion API client with reliability features.

Includes:
- Automatic retry with exponential backoff for transient errors
- Rate limiting (3 req/sec) to respect Notion API limits
- Request timeouts to prevent indefinite hangs
- Structured logging for observability
"""

from __future__ import annotations

import time

import requests

from powerflow.utils.logging import get_logger, log_api_call
from powerflow.utils.reliability import (
    DEFAULT_TIMEOUT,
    RetryConfig,
    calculate_backoff,
    get_notion_limiter,
    is_retriable_error,
)

logger = get_logger(__name__)

BASE_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# Retry configuration for Notion API
NOTION_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=60.0,
    exponential_base=2.0,
    retriable_status_codes={429, 500, 502, 503, 504},
)


class NotionClient:
    """Client for Notion API with reliability features."""

    def __init__(self, api_key: str, timeout: float = 30.0):
        """Initialize Notion client.

        Args:
            api_key: Notion integration API key
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        })
        self._rate_limiter = get_notion_limiter()
        logger.debug("NotionClient initialized")

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make an API request with retry, rate limiting, and timeout.

        Args:
            method: HTTP method (GET, POST, PATCH)
            endpoint: API endpoint (e.g., /databases/xxx)
            **kwargs: Additional arguments for requests

        Returns:
            Parsed JSON response

        Raises:
            requests.HTTPError: On non-retriable HTTP errors
            requests.RequestException: On connection/timeout errors after retries
        """
        url = f"{BASE_URL}{endpoint}"

        # Set default timeout if not provided
        if "timeout" not in kwargs:
            kwargs["timeout"] = DEFAULT_TIMEOUT.as_tuple

        last_error: Exception | None = None

        for attempt in range(1, NOTION_RETRY_CONFIG.max_attempts + 1):
            # Rate limiting: wait for token
            self._rate_limiter.wait()

            start_time = time.monotonic()
            try:
                response = self.session.request(method, url, **kwargs)
                duration_ms = (time.monotonic() - start_time) * 1000

                log_api_call(
                    logger,
                    method,
                    url,
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                )

                response.raise_for_status()
                return response.json()

            except requests.exceptions.HTTPError as e:
                last_error = e
                duration_ms = (time.monotonic() - start_time) * 1000

                # Check for rate limit with Retry-After header
                if e.response is not None and e.response.status_code == 429:
                    retry_after = e.response.headers.get("Retry-After")
                    if retry_after:
                        delay = float(retry_after)
                        logger.warning(
                            "Rate limited, waiting %s seconds (Retry-After header)",
                            retry_after,
                        )
                        time.sleep(delay)
                        continue

                if not is_retriable_error(e, NOTION_RETRY_CONFIG):
                    log_api_call(logger, method, url, error=str(e))
                    raise

                if attempt >= NOTION_RETRY_CONFIG.max_attempts:
                    log_api_call(logger, method, url, error=f"Max retries exceeded: {e}")
                    raise

                delay = calculate_backoff(attempt, NOTION_RETRY_CONFIG)
                logger.warning(
                    "Retry %d/%d for %s %s in %.1fs: %s",
                    attempt,
                    NOTION_RETRY_CONFIG.max_attempts,
                    method,
                    endpoint,
                    delay,
                    e,
                )
                time.sleep(delay)

            except requests.exceptions.RequestException as e:
                last_error = e
                duration_ms = (time.monotonic() - start_time) * 1000

                if not is_retriable_error(e, NOTION_RETRY_CONFIG):
                    log_api_call(logger, method, url, error=str(e))
                    raise

                if attempt >= NOTION_RETRY_CONFIG.max_attempts:
                    log_api_call(logger, method, url, error=f"Max retries exceeded: {e}")
                    raise

                delay = calculate_backoff(attempt, NOTION_RETRY_CONFIG)
                logger.warning(
                    "Retry %d/%d for %s %s in %.1fs: %s",
                    attempt,
                    NOTION_RETRY_CONFIG.max_attempts,
                    method,
                    endpoint,
                    delay,
                    e,
                )
                time.sleep(delay)

        # Should not reach here
        if last_error:
            raise last_error
        raise RuntimeError("Unexpected request loop exit")

    def search_databases(self) -> list[dict]:
        """Search for all databases the integration can access."""
        logger.debug("Searching for accessible databases")
        results = []
        has_more = True
        start_cursor = None

        while has_more:
            payload: dict = {
                "filter": {"property": "object", "value": "database"},
            }
            if start_cursor:
                payload["start_cursor"] = start_cursor

            data = self._request("POST", "/search", json=payload)
            results.extend(data.get("results", []))
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")

        logger.debug("Found %d databases", len(results))
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
        filter_obj: dict | None = None,
        page_size: int = 100,
    ) -> list[dict]:
        """Query database pages with pagination."""
        logger.debug("Querying database %s", database_id[:8])
        results = []
        has_more = True
        start_cursor = None

        while has_more:
            payload: dict = {"page_size": page_size}
            if filter_obj:
                payload["filter"] = filter_obj
            if start_cursor:
                payload["start_cursor"] = start_cursor

            data = self._request("POST", f"/databases/{database_id}/query", json=payload)
            results.extend(data.get("results", []))
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")

        logger.debug("Query returned %d results", len(results))
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

    def batch_check_existing_pocket_ids(
        self,
        database_id: str,
        pocket_ids: list[str],
        pocket_id_property: str = "Inbox ID",
    ) -> set[str]:
        """Check which pocket_ids already exist in the database.

        Uses OR filter to check multiple IDs in a single query.
        Chunks large lists to stay within Notion's filter limits.

        Args:
            database_id: Target database
            pocket_ids: List of pocket_ids to check
            pocket_id_property: Name of the property storing pocket_id

        Returns:
            Set of pocket_ids that already exist in the database
        """
        if not pocket_ids:
            return set()

        logger.debug("Checking %d pocket_ids for duplicates", len(pocket_ids))
        existing = set()
        chunk_size = 100  # Notion OR filter limit

        for i in range(0, len(pocket_ids), chunk_size):
            chunk = pocket_ids[i:i + chunk_size]

            # Build OR filter
            filter_obj = {
                "or": [
                    {"property": pocket_id_property, "rich_text": {"equals": pid}}
                    for pid in chunk
                ]
            }

            results = self.query_database(database_id, filter_obj)

            # Extract pocket_ids from results
            for page in results:
                prop = page.get("properties", {}).get(pocket_id_property, {})
                rich_text = prop.get("rich_text", [])
                if rich_text:
                    existing.add(rich_text[0].get("plain_text", ""))

        logger.debug("Found %d existing pocket_ids", len(existing))
        return existing

    def create_page(
        self,
        database_id: str,
        properties: dict,
        children: list[dict] | None = None,
        icon: dict | None = None,
    ) -> dict:
        """Create a new page in the database with optional body content.

        Args:
            database_id: Target database ID
            properties: Page properties (database fields)
            children: Optional list of block objects for page body content
            icon: Optional page icon, e.g. {"type": "emoji", "emoji": "🎙️"}

        Returns:
            Created page object
        """
        payload: dict = {
            "parent": {"database_id": database_id},
            "properties": properties,
        }
        if children:
            payload["children"] = children
        if icon:
            payload["icon"] = icon

        logger.info("Creating page in database %s", database_id[:8])
        return self._request("POST", "/pages", json=payload)

    def create_property(
        self,
        database_id: str,
        property_name: str,
        property_type: str,
    ) -> dict:
        """Add a new property to a database.

        Args:
            database_id: Target database ID
            property_name: Name for the new property
            property_type: Type of property (rich_text, url, select, date, checkbox, multi_select)

        Returns:
            Updated database object
        """
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
        elif property_type == "multi_select":
            property_config = {"multi_select": {"options": []}}
        else:
            logger.warning(
                "Unknown property type '%s' for '%s', defaulting to rich_text",
                property_type,
                property_name,
            )
            property_config = {"rich_text": {}}

        payload = {
            "properties": {
                property_name: property_config,
            }
        }

        logger.info("Creating property '%s' (%s) in database %s",
                   property_name, property_type, database_id[:8])
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

        if created:
            logger.info("Created %d missing properties: %s", len(created), ", ".join(created))

        return created

    def test_connection(self) -> bool:
        """Test API connection."""
        try:
            self.search_databases()
            logger.debug("Notion connection test successful")
            return True
        except requests.RequestException as e:
            logger.warning("Notion connection test failed: %s", e)
            return False

    def format_databases_for_display(self, databases: list[dict]) -> list[dict]:
        """Format database list for CLI display.

        Note: This is presentation logic and ideally belongs in the CLI layer.
        Kept here for backwards compatibility.
        """
        formatted = []
        for db in databases:
            title_parts = db.get("title", [])
            title = (
                title_parts[0].get("plain_text", "Untitled")
                if title_parts else "Untitled"
            )
            icon = db.get("icon", {})
            emoji = (
                icon.get("emoji", "📄")
                if icon and icon.get("type") == "emoji" else "📄"
            )

            formatted.append({
                "id": db["id"],
                "title": title,
                "emoji": emoji,
                "url": db.get("url", ""),
            })
        return formatted
