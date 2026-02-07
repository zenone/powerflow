# ⚡ Power-Flow

**Sync your Pocket AI recordings to Notion — automatically.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-87%20passed-brightgreen.svg)](#development)

---

## 🎯 What It Does

You talk to [Pocket AI](https://heypocket.com/). Power-Flow puts everything in your Notion inbox — ready for you to triage into tasks, notes, projects, or archive.

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Pocket AI  │ ───▶ │ Power-Flow  │ ───▶ │   Notion    │
│ (your voice)│ API  │   (sync)    │ API  │  (inbox)    │
└─────────────┘      └─────────────┘      └─────────────┘
                            │
                     ✓ Each recording → Inbox item
                     ✓ Action items → To-do checkboxes
                     ✓ Tags & summary preserved
                     ✓ Smart deduplication
```

Each recording becomes a beautifully formatted Notion page:

```
┌──────────────────────────────────────────────────────────┐
│ 💼 Meeting with Design Team                              │  ← Smart icon (from tags)
├──────────────────────────────────────────────────────────┤
│                                                          │
│ ### Meeting Summary                                      │  ← Parsed markdown
│ • **Team decision**: Progressive disclosure approach    │
│ • Timeline: Launch by end of Q1                         │
│                                                          │
│ ### Action Items                                         │
│                                                          │
│ ☐ Review competitor onboarding [High] — due Feb 10      │  ← Extracted tasks
│ ☐ Schedule follow-up with Sarah [Medium]                │
│                                                          │
│ ▸ 🧠 Mind Map                                           │  ← Hierarchical outline
│     • Main Topic                                        │
│       → Subtopic A                                      │
│       → Subtopic B                                      │
│                                                          │
│ ─────────────────────────────────────────────────────── │
│                                                          │
│ ▸ 📎 Source Details                                     │  ← Collapsed toggle
│     • Duration: 5:23                                    │
│     • Captured: Feb 6, 2026 at 10:15 AM                │
│     • Open in Pocket AI →                              │
│     ▸ 📝 Full Transcript                               │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## ✨ Features

- **🔄 One-command sync** — Run `powerflow sync` and you're done
- **📦 Recording-centric** — Each recording = one Inbox item (for GTD-style triage)
- **✅ Action items preserved** — Pocket's extracted tasks become to-do checkboxes
- **🎨 Smart icons** — Tags auto-map to emojis (work → 💼, idea → 💡, etc.)
- **🚀 Incremental** — Only fetches new recordings since last sync
- **🧠 Smart dedup** — Never creates duplicates, even if you run it 100 times
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

That's it. Your recordings are now in Notion. 🎉

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
| `powerflow sync` | Sync recordings to Notion |
| `powerflow sync --dry-run` | Preview what would sync (no changes) |
| `powerflow status` | Show sync status and pending count |
| `powerflow config show` | View current configuration |
| `powerflow config reset` | Reset all configuration |
| `powerflow --help` | Show all commands |

### Examples

```bash
# See what would sync without actually syncing
powerflow sync --dry-run

# Check how many recordings are pending
powerflow status

# Reconfigure (pick a different database)
powerflow setup
```

---

## 🤖 Automatic Sync (Set and Forget)

Don't want to run `powerflow sync` manually? Set it up to run automatically.

### Option 1: Background Daemon

```bash
# Start syncing every 15 minutes (default)
powerflow daemon start

# Custom interval (5 minutes, 30 minutes, 1 hour)
powerflow daemon start --interval 5m
powerflow daemon start --interval 30m
powerflow daemon start --interval 1h

# Check status
powerflow daemon status

# Stop the daemon
powerflow daemon stop
```

### Option 2: System Service (Auto-start on Boot)

For true "set and forget" — syncs automatically even after restart:

```bash
# Install as system service (macOS launchd)
powerflow daemon install

# With custom interval
powerflow daemon install --interval 30m

# Remove service
powerflow daemon uninstall
```

### Which Interval Should I Use?

| Interval | Best For |
|----------|----------|
| **5 min** | Power users who want near-instant sync |
| **15 min** | Most users (recommended default) |
| **30 min** | Casual users, battery-conscious |
| **1 hour** | Minimal resource usage |

> 💡 **Tip**: Pocket recordings only happen when you talk to it, so frequent polling rarely finds new items. 15 minutes is the sweet spot for most people.

### Smart Features

The daemon isn't just a dumb timer — it's smart:

- **🔄 Retry on failure** — If sync fails, retries after 1 minute (up to 2 times)
- **🔔 Desktop notifications** (macOS) — Get notified when new items sync
- **📊 State tracking** — Tracks consecutive failures, last result, next sync time

---

## 🎨 Smart Icons

Power-Flow automatically assigns page icons based on your Pocket tags:

| Tag | Icon | Tag | Icon |
|-----|------|-----|------|
| work | 💼 | personal | 👤 |
| meeting | 📅 | reminder | ⏰ |
| idea | 💡 | task | ✅ |
| note | 📝 | question | ❓ |
| important | ⭐ | urgent | 🔥 |

No matching tag? Default: 🎙️ (mic for voice recordings)

First matching tag wins, so order your tags by importance if you want control.

---

## ⚙️ How It Works

### Sync Flow

1. **Fetch** — Get recordings from Pocket API (only new ones since last sync)
2. **Parse** — Extract title, summary, action items, tags, transcript
3. **Dedupe** — Batch-check which recordings already exist in Notion
4. **Create** — Add new recordings as rich Notion pages with icons
5. **Track** — Update `last_sync` timestamp for next run

### Deduplication

Every recording gets a unique ID like `pocket:recording:abc123`. This is stored in Notion and checked before creating. Run sync 100 times — you'll never get duplicates.

### Page Structure

Each Notion page includes:

| Section | Content |
|---------|---------|
| **Icon** | Auto-assigned emoji based on tags |
| **Title** | Recording title or first line of summary |
| **Summary** | Pocket's summary parsed into native headings, bullets, bold |
| **Action items** | To-do checkboxes with priority and due dates |
| **Mind map toggle** | Hierarchical outline of topics (if available) |
| **Source toggle** | Duration, capture date, Pocket link, transcript |

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
| Title | Title (e.g., "Name") | title | ✅ Yes |
| Pocket ID | Any text field (e.g., "Inbox ID") | rich_text | ✅ Yes (for dedup) |
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
1. Open Pocket AI app → Settings → Developers → API Keys
2. Generate a new key
3. Update your `POCKET_API_KEY` environment variable

### "Rate limited"

**Cause**: Too many API calls too fast (rare with normal usage).

**Fix**: Wait a minute and try again. Power-Flow uses batch operations to minimize API calls.

### Sync runs but nothing appears

**Check these**:
1. Are there new recordings in Pocket? (Already-synced recordings are skipped)
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
│   ├── __init__.py      # Version
│   ├── __main__.py      # python -m powerflow entry
│   ├── cli.py           # CLI entry point
│   ├── pocket.py        # Pocket AI API client
│   ├── notion.py        # Notion API client
│   ├── sync.py          # Core sync engine
│   ├── blocks.py        # Notion block builders
│   ├── config.py        # Configuration management
│   ├── models.py        # Data models (Recording, ActionItem)
│   └── daemon.py        # Background sync daemon
├── tests/               # 87 tests
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
  <br>
  <a href="https://www.linkedin.com/in/zenone/">LinkedIn</a> · <a href="https://github.com/zenone">GitHub</a>
</p>
