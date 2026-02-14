"""Pocket AI API client with reliability features.

Includes:
- Automatic retry with exponential backoff for transient errors
- Rate limiting to respect API limits
- Request timeouts to prevent indefinite hangs
- Structured logging for observability
"""

from __future__ import annotations

import contextlib
import os
import time
from datetime import datetime, timezone

import requests

from powerflow.models import ActionItem, Recording
from powerflow.utils.logging import get_logger, log_api_call
from powerflow.utils.reliability import (
    DEFAULT_TIMEOUT,
    RetryConfig,
    calculate_backoff,
    get_pocket_limiter,
    is_retriable_error,
)

logger = get_logger(__name__)

# Base URL from official docs: https://docs.heypocketai.com/docs/api
DEFAULT_BASE_URL = "https://public.heypocketai.com/api/v1"
BASE_URL = os.getenv("POCKET_API_URL", DEFAULT_BASE_URL)

# Pocket web app URL for recording links
POCKET_WEB_URL = "https://heypocket.com"

# Retry configuration for Pocket API
POCKET_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=30.0,
    exponential_base=2.0,
    retriable_status_codes={429, 500, 502, 503, 504},
)


def parse_datetime(dt_str: str | None) -> datetime | None:
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
    """Client for Pocket AI API with reliability features."""

    def __init__(self, api_key: str, timeout: float = 30.0) -> None:
        """Initialize Pocket client.

        Args:
            api_key: Pocket AI API key
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })
        self._rate_limiter = get_pocket_limiter()
        logger.debug("PocketClient initialized")

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make an API request with retry, rate limiting, and timeout.

        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint
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

        for attempt in range(1, POCKET_RETRY_CONFIG.max_attempts + 1):
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

                if not is_retriable_error(e, POCKET_RETRY_CONFIG):
                    log_api_call(logger, method, url, error=str(e))
                    raise

                if attempt >= POCKET_RETRY_CONFIG.max_attempts:
                    log_api_call(logger, method, url, error=f"Max retries exceeded: {e}")
                    raise

                delay = calculate_backoff(attempt, POCKET_RETRY_CONFIG)
                logger.warning(
                    "Retry %d/%d for %s %s in %.1fs: %s",
                    attempt,
                    POCKET_RETRY_CONFIG.max_attempts,
                    method,
                    endpoint,
                    delay,
                    e,
                )
                time.sleep(delay)

            except requests.exceptions.RequestException as e:
                last_error = e
                duration_ms = (time.monotonic() - start_time) * 1000

                if not is_retriable_error(e, POCKET_RETRY_CONFIG):
                    log_api_call(logger, method, url, error=str(e))
                    raise

                if attempt >= POCKET_RETRY_CONFIG.max_attempts:
                    log_api_call(logger, method, url, error=f"Max retries exceeded: {e}")
                    raise

                delay = calculate_backoff(attempt, POCKET_RETRY_CONFIG)
                logger.warning(
                    "Retry %d/%d for %s %s in %.1fs: %s",
                    attempt,
                    POCKET_RETRY_CONFIG.max_attempts,
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

    def get_recordings_list(self, limit: int = 100) -> list[dict]:
        """Get list of recordings (without full details)."""
        logger.debug("Fetching recordings list (limit=%d)", limit)
        data = self._request("GET", "/public/recordings", params={"limit": limit})
        recordings = data.get("data", [])
        logger.debug("Got %d recordings in list", len(recordings))
        return recordings

    def get_recording_details(self, recording_id: str) -> dict:
        """Get a single recording with full details including summarizations."""
        logger.debug("Fetching details for recording %s", recording_id[:8])
        data = self._request("GET", f"/public/recordings/{recording_id}")
        return data.get("data", {})

    def get_tags(self) -> list[str]:
        """Get all tags."""
        data = self._request("GET", "/public/tags")
        return data.get("data", [])

    def search(self, query: str) -> list[dict]:
        """Semantic search across recordings."""
        logger.debug("Searching recordings: %s", query[:50])
        data = self._request("POST", "/public/search", json={"query": query})
        return data.get("data", [])

    def fetch_recordings(self, since: datetime | None = None) -> list[Recording]:
        """Fetch all recordings, optionally filtered by created_at timestamp.

        Note: This uses N+1 API pattern (list + individual details).
        Acceptable because Pocket API doesn't support batch detail fetch.

        Args:
            since: Only fetch recordings created after this time. If None, fetch all.

        Returns:
            List of Recording objects with full details.
        """
        recordings = []
        raw_list = self.get_recordings_list()
        skipped = 0
        failed = 0

        logger.info(
            "Processing %d recordings%s",
            len(raw_list),
            f" since {since.isoformat()}" if since else "",
        )

        for rec in raw_list:
            recording_id = rec.get("id")
            if not recording_id:
                continue

            # Filter by created_at if since is provided
            if since:
                rec_created = parse_datetime(rec.get("createdAt") or rec.get("created_at"))
                if rec_created and rec_created <= since:
                    skipped += 1
                    continue  # Skip recordings before since

            # Get full recording details
            try:
                full_rec = self.get_recording_details(recording_id)
                recording = self._parse_recording(full_rec)
                if recording:
                    recordings.append(recording)
            except requests.RequestException as e:
                # Log but continue with others (error accumulation pattern)
                logger.warning(
                    "Failed to fetch recording %s: %s",
                    recording_id[:8],
                    e,
                )
                failed += 1
                continue

        logger.info(
            "Fetched %d recordings (skipped=%d, failed=%d)",
            len(recordings),
            skipped,
            failed,
        )
        return recordings

    def _parse_recording(self, data: dict) -> Recording | None:
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
            with contextlib.suppress(ValueError, TypeError):
                duration_seconds = int(duration_raw)

        # Tags
        tags = []
        tags_data = data.get("tags") or []
        for tag in tags_data:
            tag_name = tag.get("name") or tag.get("label") if isinstance(tag, dict) else str(tag)
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
            logger.debug("Pocket connection test successful")
            return True
        except requests.RequestException as e:
            logger.warning("Pocket connection test failed: %s", e)
            return False
