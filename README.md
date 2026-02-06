# ⚡ Power-Flow

**Sync your Pocket AI action items to Notion — automatically.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-52%20passed-brightgreen.svg)](#development)

---

## 🎯 What It Does

You talk to [Pocket AI](https://heypocket.com/). It creates action items. Power-Flow puts them in your Notion inbox — with zero manual copy-paste.

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Pocket AI  │ ───▶ │ Power-Flow  │ ───▶ │   Notion    │
│  (your AI)  │ API  │   (sync)    │ API  │  (inbox)    │
└─────────────┘      └─────────────┘      └─────────────┘
                            │
                     ✓ Deduplication
                     ✓ Priority styling
                     ✓ Source links
```

Each action item becomes a beautifully formatted Notion page:

- 🔥 **High priority** → Red callout
- ⚡ **Medium priority** → Yellow callout  
- 📝 **Low priority** → Gray callout
- 🔗 **Source link** → Back to the original Pocket recording

---

## ✨ Features

- **🔄 One-command sync** — Run `powerflow sync` and you're done
- **🚀 Incremental** — Only fetches new recordings since last sync
- **🧠 Smart dedup** — Never creates duplicates, even if you run it 100 times
- **🎨 Rich pages** — Beautiful Notion blocks, not just flat text
- **🏷️ Tags sync** — Pocket tags → Notion multi-select
- **⚡ Batch operations** — Efficient API usage (not N+1 queries)
- **🔒 Secure** — API keys stay local, never leave your machine

---

## 🚀 Quick Start

### 1. Install

```bash
pip install powerflow
```

Or install from source:
```bash
pip install git+https://github.com/zenone/powerflow.git
```

### 2. Get Your API Keys

You'll need two keys. Don't worry — it takes about 3 minutes total.

**Pocket AI** → [Get your key](#-pocket-ai-api-key)  
**Notion** → [Get your key](#%EF%B8%8F-notion-api-key)

### 3. Set Environment Variables

```bash
export POCKET_API_KEY="pk_your_key_here"
export NOTION_API_KEY="ntn_your_key_here"
```

Or create a `.env` file in your working directory:
```bash
POCKET_API_KEY=pk_your_key_here
NOTION_API_KEY=ntn_your_key_here
```

### 4. Run Setup

```bash
powerflow setup
```

This walks you through:
- Verifying your API keys work
- Picking your Notion database
- Mapping Pocket fields to Notion properties

### 5. Sync!

```bash
powerflow sync
```

That's it. Your action items are now in Notion. 🎉

---

## 🔑 Getting Your API Keys

### 📱 Pocket AI API Key

1. Open the **Pocket AI** app on your phone
2. Tap **Settings** in the bottom navigation bar (gear icon, far right)
3. Scroll down and tap **Developers**
4. Tap **API Keys**
5. Tap **Create Secret Key**
6. Enter a name (optional) — something like `powerflow`
7. Tap **Create**
8. Copy the key (starts with `pk_`)

> 💡 **Tip**: The key looks like `pk_881a6107b...`. Keep it secret — don't share it or commit it to git!

### 🗂️ Notion API Key

This requires creating a Notion "integration" — sounds fancy, but it's just a way for apps to talk to your Notion workspace.

#### Step 1: Create the Integration

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **+ New integration**
3. Fill in:
   - **Name**: `Power-Flow` (or whatever you like)
   - **Associated workspace**: Select your workspace
4. Click **Submit**
5. Copy the **Internal Integration Token** (starts with `ntn_` or `secret_`)

#### Step 2: Give It Access to Your Database

This is the step people forget! Your integration can't see anything until you explicitly share a database with it.

1. Open your target Notion database (e.g., your Inbox)
2. Click the **`···`** menu in the top-right
3. Scroll to **Connections**
4. Click **+ Add connection**
5. Find and select **Power-Flow** (the integration you just created)
6. Click **Confirm**

> ⚠️ **Important**: If you skip this step, `powerflow setup` will say "No databases found" even though your API key is valid.

#### What Permissions Does It Need?

Power-Flow needs:
- ✅ **Read content** — to check for existing items (deduplication)
- ✅ **Insert content** — to create new pages
- ❌ **Update/Delete** — not needed (Power-Flow never modifies existing pages)

The default "Internal Integration" permissions are fine.

---

## 📚 Commands

| Command | Description |
|---------|-------------|
| `powerflow setup` | First-time configuration wizard |
| `powerflow sync` | Sync action items to Notion |
| `powerflow sync --dry-run` | Preview what would sync (no changes) |
| `powerflow status` | Show sync status and pending count |
| `powerflow config` | View current configuration |
| `powerflow --help` | Show all commands |

### Examples

```bash
# See what would sync without actually syncing
powerflow sync --dry-run

# Check how many items are pending
powerflow status

# Reconfigure (pick a different database)
powerflow setup
```

---

## ⚙️ How It Works

### Sync Flow

1. **Fetch** — Get recordings from Pocket API (only new ones since last sync)
2. **Extract** — Pull action items from each recording
3. **Dedupe** — Batch-check which items already exist in Notion
4. **Create** — Add new items as beautifully formatted Notion pages
5. **Track** — Update `last_sync` timestamp for next run

### Deduplication

Every action item gets a unique ID like `pocket:abc123:0` (recording ID + item index). This is stored in Notion and checked before creating. Run sync 100 times — you'll never get duplicates.

### Rich Page Content

Each Notion page includes:

```
┌──────────────────────────────────────┐
│ 📋 Action Item Title                 │ ← Title property
├──────────────────────────────────────┤
│                                      │
│ ┌──────────────────────────────────┐ │
│ │ 🔥 Context                       │ │ ← Callout (color = priority)
│ │ The AI's explanation of why...   │ │
│ └──────────────────────────────────┘ │
│                                      │
│ ────────────────────────────────────│ │ ← Divider
│                                      │
│ ▸ Source Details                     │ ← Toggle (collapsed)
│   • Recording: "Morning standup"     │
│   • Duration: 5:23                   │
│   • Created: Feb 6, 2026             │
│   🔗 Open in Pocket AI               │
│                                      │
└──────────────────────────────────────┘
```

---

## 🗂️ Configuration

Config lives at `~/.powerflow/config.json`:

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
      "context": "Next step",
      "tags": "Tags",
      "source_url": "Source"
    }
  },
  "pocket": {
    "last_sync": "2026-02-06T15:30:00Z"
  }
}
```

### Property Mapping

Power-Flow maps Pocket fields to your existing Notion properties. If a property doesn't exist, it'll offer to create it.

| Pocket Field | Notion Property | Type | Required |
|--------------|-----------------|------|----------|
| Action label | Title (e.g., "Name") | title | ✅ Yes |
| Pocket ID | Any text field (e.g., "Inbox ID") | rich_text | ✅ Yes (for dedup) |
| Priority | Select field | select | Optional |
| Due date | Date field | date | Optional |
| Context | Text field | rich_text | Optional |
| Tags | Multi-select | multi_select | Optional |
| Source URL | URL field | url | Optional |

---

## 🔧 Troubleshooting

### "No databases found"

**Cause**: Your Notion integration doesn't have access to any databases.

**Fix**: 
1. Open your database in Notion
2. Click `···` → Connections → Add connection
3. Select your integration (e.g., "Power-Flow")

### "Failed to fetch from Pocket"

**Cause**: Invalid or expired Pocket API key.

**Fix**:
1. Open Pocket AI app → Settings → API Keys
2. Generate a new key
3. Update your `POCKET_API_KEY` environment variable

### "Property type mismatch"

**Cause**: You're mapping to a property with an incompatible type (e.g., mapping text to a relation field).

**Fix**: 
1. Run `powerflow setup` again
2. Choose a different property, or
3. Create a new property with the correct type

### "Rate limited"

**Cause**: Too many API calls too fast (rare with normal usage).

**Fix**: Wait a minute and try again. Power-Flow uses batch operations to minimize API calls.

### Sync runs but nothing appears

**Check these**:
1. Are there new action items in Pocket? (Items already synced are skipped)
2. Run `powerflow sync --dry-run` to see what would sync
3. Check `powerflow status` for pending count

---

## 👩‍💻 Development

```bash
# Clone
git clone https://github.com/zenone/powerflow.git
cd powerflow

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=powerflow

# Type check
mypy src/powerflow

# Lint
ruff check src/
```

### Project Structure

```
powerflow/
├── src/powerflow/
│   ├── __init__.py
│   ├── cli.py          # CLI entry point
│   ├── pocket.py       # Pocket AI API client
│   ├── notion.py       # Notion API client
│   ├── sync.py         # Core sync engine
│   ├── blocks.py       # Notion block builders
│   ├── config.py       # Configuration management
│   └── models.py       # Data models
├── tests/
│   ├── test_models.py
│   ├── test_blocks.py
│   ├── test_incremental_sync.py
│   ├── test_batch_dedup.py
│   └── test_tags_sync.py
├── pyproject.toml
└── README.md
```

---

## 📄 License

MIT — do whatever you want with it.

---

## 🙏 Credits

Built with:
- [Pocket AI](https://heypocket.com/) — The AI that captures your thoughts
- [Notion API](https://developers.notion.com/) — The API that powers your workspace
- Coffee ☕

---

<p align="center">
  Made with ⚡ by <a href="https://github.com/zenone">@zenone</a>
</p>
