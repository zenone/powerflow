# Changelog

All notable changes to Power-Flow will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-02-14

### Added
- **Reliability utilities** (`utils/reliability.py`)
  - Retry decorator with exponential backoff
  - Token bucket rate limiter (Notion: 3 req/sec, Pocket: 5 req/sec)
  - Configurable timeouts (30s default)
- **Structured logging** (`utils/logging.py`)
  - Log rotation support (10MB, 3 backups)
  - Context-aware logging with `ContextAdapter`
  - Helper functions for API call and sync result logging
- **API key format validation** in CLI
- **Input validation** for daemon interval parsing
- 55 new tests (149 total)

### Changed
- `notion.py`: Integrated retry, rate limiting, timeout, and logging
- `pocket.py`: Integrated retry, rate limiting, timeout, and logging
- `sync.py`: Added comprehensive logging throughout
- `daemon.py`: Added log rotation, atomic state writes
- `cli.py`: Replaced generic exception handling with specific types

### Fixed
- `get_pending_count()` now returns -1 on error instead of misleading count
- `parse_interval()` now validates input range (1-1440 minutes)
- `save_state()` now uses atomic write pattern (write .tmp then rename)

## [0.4.0] - 2026-02-07

### Added
- Summary completion check to prevent syncing before Pocket AI finishes processing
- Recordings without AI content marked as "pending" and retried on next sync

### Fixed
- Race condition when sync runs before Pocket finishes processing

## [0.3.0] - 2026-02-06

### Added
- Tags sync (Pocket tags → Notion multi-select)
- Batch deduplication (check multiple IDs in single query)
- Smart icons based on tags (work → 💼, idea → 💡, etc.)

### Changed
- Recording-centric sync (each recording = one Notion page)
- Improved Notion page formatting with markdown parsing

## [0.2.0] - 2026-02-06

### Added
- Daemon mode with `powerflow daemon start/stop/status`
- launchd service installation with `powerflow daemon install`
- Incremental sync (only fetch new recordings since last sync)
- Desktop notifications for important events (macOS)

### Changed
- Improved error handling with retry logic in daemon

## [0.1.0] - 2026-02-06

### Added
- Initial release
- Basic sync from Pocket AI to Notion
- Setup wizard for API keys and database selection
- Action items extraction and formatting
- Deduplication via `pocket_id` property
