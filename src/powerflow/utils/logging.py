"""Structured logging utilities for powerflow.

Provides consistent logging configuration across all modules with:
- Structured log format for machine parsing
- Human-readable console output
- Log rotation for daemon mode
- Contextual fields (operation, recording_id, etc.)

Usage:
    from powerflow.utils import get_logger, setup_logging

    # Setup once at application start
    setup_logging(level="INFO", log_file="~/.powerflow/daemon.log")

    # Get logger in each module
    logger = get_logger(__name__)
    logger.info("Syncing", extra={"recording_count": 5})
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

# -----------------------------------------------------------------------------
# Log Format
# -----------------------------------------------------------------------------

# Console format: human-readable with timestamp and level
CONSOLE_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
CONSOLE_DATE_FORMAT = "%H:%M:%S"

# File format: structured with full timestamp for log analysis
FILE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
FILE_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Default log directory
DEFAULT_LOG_DIR = Path.home() / ".powerflow" / "logs"


# -----------------------------------------------------------------------------
# Logger Configuration
# -----------------------------------------------------------------------------


class ContextAdapter(logging.LoggerAdapter):
    """Logger adapter that adds contextual information to log records.

    Allows adding extra fields without modifying every log call.

    Example:
        logger = get_logger(__name__)
        ctx_logger = logger.with_context(operation="sync", batch_id="abc123")
        ctx_logger.info("Processing batch")  # Includes operation and batch_id
    """

    def process(
        self,
        msg: str,
        kwargs: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        """Add context to log message."""
        extra = kwargs.get("extra", {})
        extra.update(self.extra or {})

        # Format context fields into message suffix
        if extra:
            context_str = " ".join(f"{k}={v}" for k, v in extra.items() if v is not None)
            if context_str:
                msg = f"{msg} [{context_str}]"

        kwargs["extra"] = extra
        return msg, kwargs


class PowerflowLogger(logging.Logger):
    """Custom logger with context support."""

    def with_context(self, **context: Any) -> ContextAdapter:
        """Create a logger adapter with additional context.

        Args:
            **context: Key-value pairs to include in log messages

        Returns:
            ContextAdapter that includes context in all messages
        """
        return ContextAdapter(self, context)


# Register custom logger class
logging.setLoggerClass(PowerflowLogger)


def get_logger(name: str) -> PowerflowLogger:
    """Get a logger instance for the given module.

    Args:
        name: Usually __name__ of the calling module

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)  # type: ignore[return-value]


# -----------------------------------------------------------------------------
# Setup Functions
# -----------------------------------------------------------------------------


def setup_logging(
    level: str = "INFO",
    log_file: str | Path | None = None,
    console: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 3,
    verbose: bool = False,
) -> None:
    """Configure logging for the application.

    Should be called once at application startup.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (None = no file logging)
        console: Whether to log to console
        max_bytes: Max size of log file before rotation
        backup_count: Number of rotated log files to keep
        verbose: If True, use DEBUG level and more detailed format
    """
    # Determine log level
    if verbose:
        level = "DEBUG"
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Get root logger for powerflow
    root_logger = logging.getLogger("powerflow")
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(CONSOLE_FORMAT, CONSOLE_DATE_FORMAT)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # File handler with rotation
    if log_file:
        log_path = Path(log_file).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(FILE_FORMAT, FILE_DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def setup_daemon_logging(
    log_dir: Path | None = None,
    level: str = "INFO",
) -> Path:
    """Configure logging for daemon mode.

    Sets up file logging with rotation, suitable for long-running processes.

    Args:
        log_dir: Directory for log files (default: ~/.powerflow/logs)
        level: Log level

    Returns:
        Path to the log file
    """
    if log_dir is None:
        log_dir = DEFAULT_LOG_DIR

    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "daemon.log"

    setup_logging(
        level=level,
        log_file=log_file,
        console=False,  # Daemon shouldn't write to console
        max_bytes=10 * 1024 * 1024,  # 10 MB
        backup_count=3,  # Keep 3 rotated files
    )

    return log_file


# -----------------------------------------------------------------------------
# Logging Helpers
# -----------------------------------------------------------------------------


def log_api_call(
    logger: logging.Logger,
    method: str,
    url: str,
    status_code: int | None = None,
    duration_ms: float | None = None,
    error: str | None = None,
) -> None:
    """Log an API call with consistent format.

    Args:
        logger: Logger instance
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        status_code: Response status code (if successful)
        duration_ms: Request duration in milliseconds
        error: Error message (if failed)
    """
    # Truncate URL for readability
    display_url = url[:80] + "..." if len(url) > 80 else url

    if error:
        logger.warning(
            "API %s %s failed: %s",
            method,
            display_url,
            error,
        )
    elif status_code:
        level = logging.DEBUG if status_code < 400 else logging.WARNING
        duration_str = f" ({duration_ms:.0f}ms)" if duration_ms else ""
        logger.log(
            level,
            "API %s %s -> %d%s",
            method,
            display_url,
            status_code,
            duration_str,
        )


def log_sync_result(
    logger: logging.Logger,
    created: int = 0,
    skipped: int = 0,
    pending: int = 0,
    failed: int = 0,
    duration_s: float | None = None,
) -> None:
    """Log sync operation results with consistent format.

    Args:
        logger: Logger instance
        created: Number of items created
        skipped: Number of items skipped (duplicates)
        pending: Number of items pending (not ready)
        failed: Number of items that failed
        duration_s: Total duration in seconds
    """
    duration_str = f" in {duration_s:.1f}s" if duration_s else ""
    logger.info(
        "Sync complete%s: created=%d skipped=%d pending=%d failed=%d",
        duration_str,
        created,
        skipped,
        pending,
        failed,
    )
