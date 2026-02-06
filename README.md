# Power-Flow

Sync [Pocket AI](https://heypocket.ai) action items and summaries to Notion with smart deduplication.

## Features

- 🔄 **One-command sync** — Pull action items from Pocket to your Notion inbox
- 🔍 **Auto-discover** — Finds your Notion databases automatically
- 🧠 **Smart mapping** — Matches existing properties, creates missing ones
- 🚫 **Deduplication** — Never creates duplicate entries on re-sync
- 🔒 **Secure** — API keys stay local, never in git

## Quick Start

### 1. Install

```bash
pip install powerflow
# or
pip install git+https://github.com/zenone/powerflow.git
```

### 2. Configure API Keys

Get your API keys:
- **Pocket AI**: App → Settings → API Keys → Create
- **Notion**: [notion.so/my-integrations](https://www.notion.so/my-integrations) → New integration

Set them in your environment:
```bash
export POCKET_API_KEY=pk_your_key_here
export NOTION_API_KEY=ntn_your_key_here
```

Or create a `.env` file:
```bash
POCKET_API_KEY=pk_your_key_here
NOTION_API_KEY=ntn_your_key_here
```

### 3. Share Your Notion Database

1. Open your target Notion database
2. Click `...` → `Connections` → Add your integration
3. Grant access

### 4. Setup

```bash
powerflow setup
```

This will:
- Verify your API keys
- Show available Notion databases
- Let you pick a target database
- Map Pocket fields to Notion properties
- Create any missing properties (with your permission)

### 5. Sync

```bash
powerflow sync
```

Run this whenever you want to sync new action items. Already-synced items are skipped automatically.

## Commands

```bash
powerflow setup           # Configure database and mapping
powerflow sync            # Sync action items to Notion
powerflow sync --dry-run  # Preview without making changes
powerflow status          # Show sync status and pending count
powerflow config          # View current configuration
```

## How It Works

```
Pocket AI → Power-Flow → Notion
  (API)       (sync)      (API)
                │
                ▼
         Deduplication
         (pocket_id)
```

1. Power-Flow fetches recordings and action items from Pocket API
2. For each action item, it generates a unique `pocket_id`
3. Before creating, it checks if that `pocket_id` exists in Notion
4. New items are created; existing items are skipped
5. Config tracks the mapping so you only set up once

## Configuration

Config is stored at `~/.powerflow/config.json`:

```json
{
  "notion": {
    "database_id": "abc123...",
    "database_name": "Inbox",
    "property_map": {
      "title": "Name",
      "pocket_id": "Inbox ID",
      "priority": "Priority",
      "due_date": "Due Date",
      "context": "Context"
    }
  },
  "pocket": {
    "last_sync": "2026-02-06T12:00:00"
  }
}
```

## Requirements

- Python 3.10+
- Pocket AI device with API access
- Notion account with integration

## Development

```bash
# Clone
git clone https://github.com/zenone/powerflow.git
cd powerflow

# Install in dev mode
pip install -e ".[dev]"

# Run tests
pytest

# Type check
mypy src/powerflow

# Lint
ruff check src/
```

## License

MIT
