# Power-Flow Project Context

**Created**: 2026-02-06
**Version**: 0.4.0
**Status**: Production-ready

## One-Liner

Sync Pocket AI recordings to Notion inbox — each recording becomes a triage item with smart icons.

## Problem

Pocket AI captures thoughts, meetings, and conversations — generating summaries, action items, and tags automatically. But those recordings live in the Pocket app. Users with GTD-style workflows want EVERYTHING in their Notion inbox for triage.

## Solution

Power-Flow bridges Pocket AI → Notion:
- Each recording → one Notion inbox item (for triage)
- Action items → to-do checkboxes inside the page
- Smart emoji icons based on tags (work → 💼, idea → 💡, etc.)
- Summary, transcript, metadata all preserved
- Daemon mode for automatic sync

---

## Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────┐
│   Pocket AI     │         │   Power-Flow    │         │   Notion    │
│   (Device/App)  │────────▶│   (Sync Engine) │────────▶│   Inbox DB  │
│                 │  API    │                 │  API    │             │
└─────────────────┘         └─────────────────┘         └─────────────┘
                                    │
                                    ▼
                            ┌─────────────────┐
                            │  Dedup Check    │
                            │  (pocket_id)    │
                            └─────────────────┘
```

### Two Modes

| Mode | Trigger | Use Case |
|------|---------|----------|
| **Pull** | `powerflow sync` or cron | Scheduled sync, backfill |
| **Push** | Webhook receiver | Real-time (future) |

---

## Pocket AI API

**Base URL**: `https://api.heypocketai.com` (inferred from testing)

**Auth**: `Authorization: Bearer pk_xxx`

### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/public/recordings` | GET | List all recordings |
| `/public/recordings/{id}` | GET | Full recording + action items |
| `/public/search` | POST | Semantic search |
| `/public/tags` | GET | List tags |

### Action Item Structure

Located at: `data.summarizations.v2_action_items.actions[]`

```json
{
  "label": "Delete local LLM app off iMac",
  "assignee": "me",
  "context": "User wants to remove the local LLM app...",
  "dueDate": null,
  "priority": "Medium",
  "type": "CreateReminder",
  "payload": { ... }
}
```

### Recording Data Available

- ✅ Transcript (full text + word-level timestamps)
- ✅ Summary (markdown formatted)
- ✅ Mind Map (node structure)
- ✅ Tags (auto-generated)
- ✅ Action Items (with context, priority, due dates)

---

## Notion Integration

**Approach**: Direct Notion API (standalone, portable)

**Why not OpenClaw integration?**
- Wider utility (any Pocket user can use it)
- Open source potential
- Doesn't break if OpenClaw changes
- Full Notion API access

### Target Database

Steve's "Inbox" database with existing properties:
- Name (title)
- Type (select: Idea, Task, Note, Project, Person)
- Status (status)
- Priority (select)
- Tags (multi_select)
- Due Date (date)
- Inbox ID (text) ← for deduplication
- Context (relation)
- etc.

---

## UX Flow (First Run)

```
$ powerflow setup

🔑 Checking Pocket API... ✓
🔑 Checking Notion API... ✓

📚 Found 4 databases:
   1. Inbox
   2. Tasks
   3. Projects
   4. [Enter ID manually]

Select [1-4]: 1

📊 Mapping Pocket → Inbox:
   ✅ Action Item  → Name (title)
   ✅ Priority     → Priority (existing)
   ✅ Due Date     → Due Date (existing)
   ➕ pocket_id    → [will create - for dedup]
   ➕ Context      → [will create]
   ➕ Source       → [will create - link to recording]

Proceed? [Y/n]: y

✅ Created 3 properties
✅ Config saved: ~/.powerflow/config.json

Run `powerflow sync` to start syncing!
```

### UX Principles

| Principle | Implementation |
|-----------|----------------|
| Low friction | Auto-discover databases |
| High value | Works with existing schema |
| Transparent | Shows what will be mapped/created |
| Recoverable | Config saved, re-run setup anytime |
| Idempotent | Running setup twice doesn't break |

---

## Config File

Location: `~/.powerflow/config.json`

```json
{
  "notion": {
    "database_id": "196ef8a8-3a6f-4d69-a2b3-b21c4d28b4a1",
    "database_name": "Inbox",
    "property_map": {
      "title": "Name",
      "pocket_id": "Inbox ID",
      "priority": "Priority",
      "due_date": "Due Date",
      "context": "Context",
      "source_url": "Source"
    }
  },
  "pocket": {
    "last_sync": null
  },
  "created_at": "2026-02-06T12:48:00Z"
}
```

---

## Deduplication Strategy ⚠️ CRITICAL

**Requirement**: NEVER create duplicate entries in Notion.

**Key**: Use `pocket_id` (stored in Notion's "Inbox ID" field)

**Format**: `pocket:recording:{recording_id}` (v0.4.0 — recording-centric)

**Flow**:
```
1. Fetch recordings from Pocket (since last_sync)
2. For each recording:
   a. Generate pocket_id = f"pocket:recording:{recording.id}"
   b. Batch-query Notion: filter by Inbox ID starts_with "pocket:"
   c. If exists → SKIP
   d. If not exists → CREATE page with body content
3. Never update existing items (preserves user edits)
```

**Implementation**:
```python
# In sync.py - batch deduplication
existing_ids = self.notion.batch_check_existing_pocket_ids(
    pocket_ids=[r.pocket_id for r in recordings],
    database_id=db_id,
    property_name=pocket_id_prop,
)
for recording in recordings:
    if recording.pocket_id in existing_ids:
        result.skipped += 1
        continue
    # Create with icon and body content
    icon = recording.get_icon()
    children = recording.to_notion_children()
    self.notion.create_page(db_id, properties, children, icon)
```

**Verified**: Ran sync twice, second run correctly skipped all existing items.

---

## CLI Commands

```bash
powerflow setup          # First-time configuration
powerflow sync           # Sync action items to Notion
powerflow sync --dry-run # Preview without writing
powerflow status         # Show sync status
powerflow config         # View/edit configuration
```

---

## Project Structure

```
powerflow/
├── src/
│   └── powerflow/
│       ├── __init__.py
│       ├── cli.py          # CLI entry point
│       ├── pocket.py       # Pocket API client
│       ├── notion.py       # Notion API client
│       ├── sync.py         # Core sync logic
│       ├── config.py       # Config management
│       └── models.py       # Data models
├── tests/
│   ├── test_pocket.py
│   ├── test_notion.py
│   └── test_sync.py
├── .env.example
├── pyproject.toml
└── README.md
```

---

## Environment Variables

```bash
POCKET_API_KEY=pk_xxx           # Pocket API key (read permissions)
NOTION_API_KEY=ntn_xxx          # Notion integration token
NOTION_DATABASE_ID=xxx          # Optional, can be set via setup
```

---

## Success Criteria (v1)

1. ✅ `powerflow setup` discovers databases and configures mapping
2. ✅ `powerflow sync` pulls action items and creates Notion pages
3. ✅ Deduplication prevents duplicate entries
4. ✅ Clear error messages for common issues
5. ✅ Works on fresh clone with just API keys

---

## Non-Goals (v1)

- ❌ Webhook receiver (push mode) — future enhancement
- ❌ Two-way sync (Notion → Pocket)
- ❌ Web UI
- ❌ OAuth flow (internal integration token is sufficient)

---

## References

- Pocket AI Docs: https://docs.heypocketai.com/docs
- Notion API: https://developers.notion.com/
- User's Inbox DB ID: `196ef8a8-3a6f-4d69-a2b3-b21c4d28b4a1`
