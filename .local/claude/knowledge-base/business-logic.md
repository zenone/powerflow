# Power-Flow Business Logic

**Last Updated**: 2026-02-06

This document captures all business logic decisions for future development.

---

## Core Principle

**NEVER create duplicate entries in Notion.**

Every sync operation must check if an item already exists before creating.

---

## Data Flow

```
Pocket AI → Power-Flow → Notion
   │             │            │
   │             │            └── Inbox Database
   │             │
   │             ├── Fetch recordings
   │             ├── Extract action items
   │             ├── Check for duplicates (pocket_id)
   │             └── Create if new, skip if exists
   │
   └── Recordings with:
       - Metadata (title, duration, dates)
       - Tags
       - Transcript
       - Summarizations:
         - v2_summary (markdown)
         - v2_action_items (array)
         - v2_mind_map (nodes)
```

---

## What We Sync

**Action Items** (not full recordings)

Rationale:
- User's Notion "Inbox" database is task-oriented
- Action items are actionable, trackable
- Recordings are context, not tasks

Each action item becomes one Notion page with:
- Title (action item label)
- Priority (from Pocket)
- Due Date (if set)
- Context (action item context text)
- Source (link back to recording)
- pocket_id (for deduplication)

---

## Deduplication Strategy

### The Problem
Users run sync multiple times. We must not create duplicates.

### The Solution
1. Generate unique `pocket_id` for each action item:
   ```
   pocket_id = f"pocket:{recording_id}:{action_index}"
   ```

2. Before creating, query Notion:
   ```python
   filter = {"property": "Inbox ID", "rich_text": {"equals": pocket_id}}
   exists = len(query_results) > 0
   ```

3. If exists → skip
4. If not exists → create

### Why This Works
- `pocket_id` is deterministic (same input = same ID)
- Stored in Notion for future lookups
- Query is O(1) with Notion's index

### Edge Cases
- Recording deleted in Pocket: Notion entry remains (user may have edited it)
- Action item edited in Pocket: We don't update (preserves user's Notion edits)
- Same action text in different recordings: Different pocket_id, both created

---

## First-Run UX Flow

```
1. User runs `powerflow setup`

2. Check for Pocket API key:
   - In env? → Use it
   - In config? → Use it
   - Neither? → Prompt with instructions

3. Verify Pocket key:
   - Try GET /recordings
   - Success? → Continue
   - 401? → "Invalid API key"
   - Network error? → "Check internet connection"

4. Check for Notion API key:
   - Same flow as Pocket

5. Verify Notion key:
   - Try POST /search
   - Success? → Continue
   - 401? → "Invalid API key"
   - 403? → "Check integration permissions"

6. Discover databases:
   - Call Notion search API
   - Filter by type=database
   - No results? → Explain how to share DB with integration

7. User selects database:
   - Show numbered list
   - Accept number or manual ID
   - Validate access

8. Analyze schema:
   - Get database properties
   - Map Pocket fields to existing properties
   - Identify missing required properties

9. Create missing properties:
   - pocket_id (REQUIRED for dedup)
   - Context (if no suitable text field)
   - Source (if no URL field)
   - Ask user before creating

10. Save configuration:
    - ~/.powerflow/config.json
    - Database ID, name, property map
```

---

## Property Mapping

### Required Properties

| Pocket Field | Notion Property | Type | Purpose |
|--------------|-----------------|------|---------|
| label | Name | title | Action item text |
| (generated) | Inbox ID | rich_text | Deduplication key |

### Optional Properties

| Pocket Field | Notion Property | Type | Notes |
|--------------|-----------------|------|-------|
| priority | Priority | select | "High", "Medium", "Low" |
| dueDate | Due Date | date | ISO format |
| context | Next step / Action Context | rich_text | AI-generated context |
| (recording URL) | Source | url | Link to recording |

### Type Compatibility

The setup wizard checks property types:
- `rich_text` → Can receive text
- `select` → Can receive priority values
- `date` → Can receive ISO dates
- `url` → Can receive links
- `relation` → SKIP (can't populate programmatically without linked page ID)

---

## Error Handling

### Principle
No stack traces. Plain English. Actionable suggestions.

### Error Categories

| Category | Example | User Message |
|----------|---------|--------------|
| Auth | 401 | "Invalid API key. Please check and try again." |
| Permission | 403 | "API key doesn't have permission. Check your integration settings." |
| Network | Connection refused | "Can't connect to API. Check your internet connection." |
| Not Found | 404 | "Database not found. It may have been deleted." |
| Rate Limit | 429 | "Too many requests. Wait a moment and try again." |
| Server | 500 | "API is having issues. Try again later." |

### Exit Codes

- `0` — Success
- `1` — Error (any kind)

---

## Configuration

### File Location
```
~/.powerflow/config.json
```

### Schema
```json
{
  "notion": {
    "database_id": "uuid",
    "database_name": "Inbox",
    "property_map": {
      "title": "Name",
      "pocket_id": "Inbox ID",
      "priority": "Priority",
      "due_date": "Due Date",
      "context": "Next step",
      "source_url": "Source"
    }
  },
  "pocket": {
    "last_sync": "2026-02-06T12:00:00Z"
  },
  "created_at": "2026-02-06T10:00:00Z"
}
```

### Idempotency

Setup can be run multiple times:
- Re-selects database
- Re-maps properties
- Doesn't duplicate Notion pages (dedup handles that)

---

## Future Considerations

### Not Implemented (v0.1)

1. **Webhook support** — Real-time sync when Pocket creates action item
2. **Two-way sync** — Push Notion changes back to Pocket
3. **Recording sync** — Sync full recordings, not just action items
4. **Summary sync** — Include markdown summary in Notion page body
5. **Update detection** — Update Notion if Pocket item changed
6. **Batch optimization** — Reduce API calls for large syncs

### Potential Enhancements

1. **Auto-tagging** — Copy Pocket tags to Notion Tags property
2. **Recording context** — Add recording title to action item
3. **Smart scheduling** — Auto-set due dates based on priority
4. **Conflict resolution** — Handle edits in both systems
