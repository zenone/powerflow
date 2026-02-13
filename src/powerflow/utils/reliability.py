"""Reliability utilities: retry, rate limiting, timeouts.

Implements patterns identified during codebase audit:
- Exponential backoff retry for transient errors
- Token bucket rate limiting (Notion: 3 req/sec)
- Timeout handling to prevent indefinite hangs

Usage:
    from powerflow.utils import with_retry, RateLimiter, with_timeout

    # Retry decorator
    @with_retry(max_attempts=3, retriable_status_codes={429, 500, 502, 503, 504})
    def api_call():
        ...

    # Rate limiter
    limiter = RateLimiter(calls_per_second=3)
    limiter.wait()  # Block until rate allows

    # Timeout
    with with_timeout(30):
        response = requests.get(url)
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import wraps
from typing import TYPE_CHECKING, TypeVar

import requests

if TYPE_CHECKING:
    from collections.abc import Set

logger = logging.getLogger(__name__)

# Type variable for generic function decoration
F = TypeVar("F", bound=Callable)


# -----------------------------------------------------------------------------
# Retry Configuration
# -----------------------------------------------------------------------------


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    retriable_status_codes: set[int] = field(
        default_factory=lambda: {429, 500, 502, 503, 504}
    )
    retriable_exceptions: tuple[type[Exception], ...] = field(
        default_factory=lambda: (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.ChunkedEncodingError,
        )
    )


DEFAULT_RETRY_CONFIG = RetryConfig()


def is_retriable_error(
    error: Exception,
    config: RetryConfig | None = None,
) -> bool:
    """Check if an error should trigger a retry.

    Args:
        error: The exception to check
        config: Retry configuration (uses default if None)

    Returns:
        True if the error is retriable
    """
    if config is None:
        config = DEFAULT_RETRY_CONFIG

    # Check for retriable exception types
    if isinstance(error, config.retriable_exceptions):
        return True

    # Check for HTTP status code errors
    if isinstance(error, requests.exceptions.HTTPError):
        response = error.response
        if response is not None and response.status_code in config.retriable_status_codes:
            return True

    return False


def calculate_backoff(
    attempt: int,
    config: RetryConfig | None = None,
) -> float:
    """Calculate exponential backoff delay.

    Args:
        attempt: Current attempt number (1-indexed)
        config: Retry configuration

    Returns:
        Delay in seconds before next retry
    """
    if config is None:
        config = DEFAULT_RETRY_CONFIG

    delay = config.base_delay * (config.exponential_base ** (attempt - 1))
    return min(delay, config.max_delay)


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retriable_status_codes: Set[int] | None = None,
    on_retry: Callable[[Exception, int], None] | None = None,
) -> Callable[[F], F]:
    """Decorator for automatic retry with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts (including initial)
        base_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        exponential_base: Base for exponential backoff calculation
        retriable_status_codes: HTTP status codes to retry on
        on_retry: Optional callback called before each retry (error, attempt)

    Returns:
        Decorated function with retry logic

    Example:
        @with_retry(max_attempts=3, retriable_status_codes={429, 500})
        def fetch_data():
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
    """
    if retriable_status_codes is None:
        retriable_status_codes = {429, 500, 502, 503, 504}

    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        retriable_status_codes=set(retriable_status_codes),
    )

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error: Exception | None = None

            for attempt in range(1, config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e

                    if not is_retriable_error(e, config):
                        logger.debug(
                            "Non-retriable error in %s: %s",
                            func.__name__,
                            e,
                        )
                        raise

                    if attempt >= config.max_attempts:
                        logger.warning(
                            "Max retries (%d) exceeded for %s: %s",
                            config.max_attempts,
                            func.__name__,
                            e,
                        )
                        raise

                    delay = calculate_backoff(attempt, config)
                    logger.info(
                        "Retry %d/%d for %s in %.1fs: %s",
                        attempt,
                        config.max_attempts,
                        func.__name__,
                        delay,
                        e,
                    )

                    if on_retry:
                        on_retry(e, attempt)

                    time.sleep(delay)

            # Should not reach here, but satisfy type checker
            if last_error:
                raise last_error
            raise RuntimeError("Unexpected retry loop exit")

        return wrapper  # type: ignore[return-value]

    return decorator


# -----------------------------------------------------------------------------
# Rate Limiting
# -----------------------------------------------------------------------------


class RateLimiter:
    """Token bucket rate limiter.

    Thread-safe implementation for controlling API request rate.

    Example:
        limiter = RateLimiter(calls_per_second=3)

        for item in items:
            limiter.wait()  # Block until rate allows
            api_call(item)
    """

    def __init__(
        self,
        calls_per_second: float = 3.0,
        burst_size: int | None = None,
    ) -> None:
        """Initialize rate limiter.

        Args:
            calls_per_second: Maximum sustained request rate
            burst_size: Maximum burst size (defaults to calls_per_second)
        """
        self.calls_per_second = calls_per_second
        self.burst_size = burst_size if burst_size is not None else int(calls_per_second)
        self.tokens = float(self.burst_size)
        self.last_update = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_update
        self.tokens = min(
            self.burst_size,
            self.tokens + elapsed * self.calls_per_second,
        )
        self.last_update = now

    def acquire(self, blocking: bool = True, timeout: float | None = None) -> bool:
        """Acquire a token from the bucket.

        Args:
            blocking: If True, block until token available
            timeout: Maximum time to wait (None = infinite)

        Returns:
            True if token acquired, False if timeout
        """
        deadline = None if timeout is None else time.monotonic() + timeout

        with self._lock:
            while True:
                self._refill()

                if self.tokens >= 1:
                    self.tokens -= 1
                    return True

                if not blocking:
                    return False

                # Calculate wait time for next token
                wait_time = (1 - self.tokens) / self.calls_per_second

                if deadline is not None:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        return False
                    wait_time = min(wait_time, remaining)

                # Release lock while sleeping
                self._lock.release()
                try:
                    time.sleep(wait_time)
                finally:
                    self._lock.acquire()

    def wait(self, timeout: float | None = None) -> bool:
        """Wait until rate limit allows a request.

        Args:
            timeout: Maximum time to wait (None = infinite)

        Returns:
            True if ready to proceed, False if timeout
        """
        return self.acquire(blocking=True, timeout=timeout)


# Singleton rate limiters for common APIs
_notion_limiter: RateLimiter | None = None
_pocket_limiter: RateLimiter | None = None


def get_notion_limiter() -> RateLimiter:
    """Get the shared Notion API rate limiter (3 req/sec)."""
    global _notion_limiter
    if _notion_limiter is None:
        _notion_limiter = RateLimiter(calls_per_second=3.0)
    return _notion_limiter


def get_pocket_limiter() -> RateLimiter:
    """Get the shared Pocket API rate limiter (5 req/sec, conservative)."""
    global _pocket_limiter
    if _pocket_limiter is None:
        _pocket_limiter = RateLimiter(calls_per_second=5.0)
    return _pocket_limiter


# -----------------------------------------------------------------------------
# Timeout
# -----------------------------------------------------------------------------


class TimeoutError(Exception):
    """Raised when an operation times out."""

    pass


class with_timeout:
    """Context manager for request timeouts.

    Note: This sets the timeout on requests, not a hard process timeout.
    For requests library, pass timeout directly to the call.

    This class provides a consistent interface for timeout configuration.

    Example:
        timeout = with_timeout(30)
        response = requests.get(url, timeout=timeout.seconds)
    """

    def __init__(self, seconds: float = 30.0) -> None:
        """Initialize timeout configuration.

        Args:
            seconds: Timeout duration in seconds
        """
        self.seconds = seconds

    def __enter__(self) -> with_timeout:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False

    @property
    def as_tuple(self) -> tuple[float, float]:
        """Return timeout as (connect, read) tuple for requests.

        Connect timeout is shorter (10s), read timeout is the full duration.
        """
        return (min(10.0, self.seconds), self.seconds)


# Default timeout for API calls
DEFAULT_TIMEOUT = with_timeout(30.0)
