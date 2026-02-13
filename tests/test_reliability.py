"""Tests for reliability utilities."""

import threading
import time
from unittest.mock import Mock

import pytest
import requests

from powerflow.utils.reliability import (
    DEFAULT_TIMEOUT,
    RateLimiter,
    RetryConfig,
    calculate_backoff,
    is_retriable_error,
    with_retry,
    with_timeout,
)


class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_default_config(self):
        """Test default retry configuration values."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert 429 in config.retriable_status_codes
        assert 500 in config.retriable_status_codes

    def test_custom_config(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=2.0,
            retriable_status_codes={429, 503},
        )
        assert config.max_attempts == 5
        assert config.base_delay == 2.0
        assert config.retriable_status_codes == {429, 503}


class TestIsRetriableError:
    """Tests for is_retriable_error."""

    def test_connection_error_is_retriable(self):
        """Connection errors should be retriable."""
        error = requests.exceptions.ConnectionError("Connection refused")
        assert is_retriable_error(error) is True

    def test_timeout_error_is_retriable(self):
        """Timeout errors should be retriable."""
        error = requests.exceptions.Timeout("Request timed out")
        assert is_retriable_error(error) is True

    def test_429_is_retriable(self):
        """429 rate limit errors should be retriable."""
        response = Mock()
        response.status_code = 429
        error = requests.exceptions.HTTPError(response=response)
        assert is_retriable_error(error) is True

    def test_500_is_retriable(self):
        """500 server errors should be retriable."""
        response = Mock()
        response.status_code = 500
        error = requests.exceptions.HTTPError(response=response)
        assert is_retriable_error(error) is True

    def test_404_is_not_retriable(self):
        """404 errors should NOT be retriable."""
        response = Mock()
        response.status_code = 404
        error = requests.exceptions.HTTPError(response=response)
        assert is_retriable_error(error) is False

    def test_400_is_not_retriable(self):
        """400 errors should NOT be retriable."""
        response = Mock()
        response.status_code = 400
        error = requests.exceptions.HTTPError(response=response)
        assert is_retriable_error(error) is False

    def test_value_error_is_not_retriable(self):
        """Non-request errors should NOT be retriable."""
        error = ValueError("Invalid input")
        assert is_retriable_error(error) is False


class TestCalculateBackoff:
    """Tests for calculate_backoff."""

    def test_first_attempt(self):
        """First attempt should use base delay."""
        delay = calculate_backoff(1)
        assert delay == 1.0

    def test_second_attempt(self):
        """Second attempt should double delay."""
        delay = calculate_backoff(2)
        assert delay == 2.0

    def test_third_attempt(self):
        """Third attempt should quadruple delay."""
        delay = calculate_backoff(3)
        assert delay == 4.0

    def test_respects_max_delay(self):
        """Should not exceed max delay."""
        config = RetryConfig(max_delay=5.0)
        delay = calculate_backoff(10, config)
        assert delay == 5.0

    def test_custom_config(self):
        """Should use custom config values."""
        config = RetryConfig(base_delay=2.0, exponential_base=3.0)
        delay = calculate_backoff(2, config)
        assert delay == 6.0  # 2.0 * 3^1


class TestWithRetry:
    """Tests for with_retry decorator."""

    def test_success_on_first_try(self):
        """Should return immediately on success."""
        call_count = 0

        @with_retry(max_attempts=3)
        def succeed():
            nonlocal call_count
            call_count += 1
            return "success"

        result = succeed()
        assert result == "success"
        assert call_count == 1

    def test_retries_on_retriable_error(self):
        """Should retry on retriable errors."""
        call_count = 0

        @with_retry(max_attempts=3, base_delay=0.01)
        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise requests.exceptions.ConnectionError("Connection failed")
            return "success"

        result = fail_then_succeed()
        assert result == "success"
        assert call_count == 2

    def test_raises_after_max_retries(self):
        """Should raise after exhausting retries."""
        call_count = 0

        @with_retry(max_attempts=3, base_delay=0.01)
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise requests.exceptions.ConnectionError("Connection failed")

        with pytest.raises(requests.exceptions.ConnectionError):
            always_fail()

        assert call_count == 3

    def test_no_retry_on_non_retriable_error(self):
        """Should not retry non-retriable errors."""
        call_count = 0

        @with_retry(max_attempts=3)
        def fail_with_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid input")

        with pytest.raises(ValueError):
            fail_with_value_error()

        assert call_count == 1

    def test_on_retry_callback(self):
        """Should call on_retry callback before each retry."""
        retries = []

        def track_retry(error, attempt):
            retries.append((str(error), attempt))

        @with_retry(max_attempts=3, base_delay=0.01, on_retry=track_retry)
        def fail_then_succeed():
            if len(retries) < 2:
                raise requests.exceptions.Timeout("Timeout")
            return "success"

        result = fail_then_succeed()
        assert result == "success"
        assert len(retries) == 2


class TestRateLimiter:
    """Tests for RateLimiter."""

    def test_allows_initial_burst(self):
        """Should allow initial burst up to burst_size."""
        limiter = RateLimiter(calls_per_second=10, burst_size=3)

        # Should allow 3 immediate calls
        for _ in range(3):
            assert limiter.acquire(blocking=False) is True

        # 4th should fail without blocking
        assert limiter.acquire(blocking=False) is False

    def test_refills_over_time(self):
        """Should refill tokens over time."""
        limiter = RateLimiter(calls_per_second=100, burst_size=1)

        # Use the token
        assert limiter.acquire(blocking=False) is True
        assert limiter.acquire(blocking=False) is False

        # Wait for refill
        time.sleep(0.02)

        # Should have token now
        assert limiter.acquire(blocking=False) is True

    def test_blocking_wait(self):
        """Should block until token available."""
        limiter = RateLimiter(calls_per_second=100, burst_size=1)

        # Use the token
        limiter.acquire()

        # This should block briefly then succeed
        start = time.monotonic()
        assert limiter.wait(timeout=1.0) is True
        elapsed = time.monotonic() - start
        assert elapsed < 0.5  # Should be fast with high rate

    def test_timeout_returns_false(self):
        """Should return False on timeout."""
        limiter = RateLimiter(calls_per_second=1, burst_size=1)

        # Use the token
        limiter.acquire()

        # This should timeout
        assert limiter.wait(timeout=0.01) is False

    def test_thread_safety(self):
        """Should be thread-safe and limit total acquisitions."""
        # Use very low rate to minimize refill during test
        limiter = RateLimiter(calls_per_second=0.1, burst_size=10)
        acquired = []
        lock = threading.Lock()

        def acquire_token():
            if limiter.acquire(blocking=False):
                with lock:
                    acquired.append(1)

        threads = [threading.Thread(target=acquire_token) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have acquired approximately burst_size tokens
        # Allow small variance due to timing (10-12)
        assert 9 <= len(acquired) <= 12, f"Expected ~10 tokens, got {len(acquired)}"


class TestWithTimeout:
    """Tests for with_timeout."""

    def test_default_timeout(self):
        """DEFAULT_TIMEOUT should have reasonable value."""
        assert DEFAULT_TIMEOUT.seconds == 30.0

    def test_custom_timeout(self):
        """Should store custom timeout value."""
        timeout = with_timeout(60.0)
        assert timeout.seconds == 60.0

    def test_as_tuple(self):
        """Should return (connect, read) tuple."""
        timeout = with_timeout(30.0)
        connect, read = timeout.as_tuple
        assert connect == 10.0  # Connect capped at 10
        assert read == 30.0

    def test_short_timeout_as_tuple(self):
        """Short timeouts should use same value for both."""
        timeout = with_timeout(5.0)
        connect, read = timeout.as_tuple
        assert connect == 5.0
        assert read == 5.0

    def test_context_manager(self):
        """Should work as context manager."""
        with with_timeout(30.0) as t:
            assert t.seconds == 30.0
