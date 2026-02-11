# Pocket AI API Reference

## Overview

Pocket AI provides a REST API for accessing recordings, transcripts, summaries, and action items.

**Base URL**: `https://public.heypocketai.com/api/v1`

**Authentication**: Bearer token  
`Authorization: Bearer pk_xxx`

---

## Getting an API Key

1. Open the **Pocket AI** app on your device
2. Go to **Settings** (gear icon)
3. Tap **API Keys** or **Developer**
4. Tap **Create API Key** or **Generate**
5. Copy the key (starts with `pk_`)

---

## Endpoints

### GET /public/recordings

List all recordings.

**Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `limit` | int | Max results (default 100) |
| `offset` | int | Pagination offset |
| `tag_ids` | string | Filter by tag IDs (comma-separated) |

**Response**:
```json
{
  "data": [
    {
      "id": "abc123",
      "title": "Morning voice note",
      "createdAt": "2026-02-06T08:30:00Z",
      "duration": 154,
      "tags": [{"id": "t1", "name": "work"}]
    }
  ]
}
```

### GET /public/recordings/{id}

Get full recording details including transcript and action items.

**Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `include_transcript` | bool | Include full transcript |
| `include_summarizations` | bool | Include summaries and action items |

**Response** (key fields):
```json
{
  "data": {
    "id": "abc123",
    "title": "Morning voice note",
    "createdAt": "2026-02-06T08:30:00Z",
    "duration": 154,
    "tags": [...],
    "transcript": {...},
    "summarizations": {
      "v2_action_items": {
        "actions": [
          {
            "label": "Send report to team",
            "assignee": "me",
            "context": "User mentioned needing to send...",
            "dueDate": "2026-02-07T17:00:00Z",
            "priority": "High",
            "type": "CreateReminder"
          }
        ]
      },
      "summary": "...",
      "mind_map": {...}
    }
  }
}
```

### GET /public/tags

List all tags.

**Response**:
```json
{
  "data": [
    {"id": "t1", "name": "work"},
    {"id": "t2", "name": "personal"}
  ]
}
```

### POST /public/search

Semantic search across recordings.

**Body**:
```json
{
  "query": "meeting notes about product launch"
}
```

---

## Action Item Structure

Located at: `data.summarizations.v2_action_items.actions[]`

| Field | Type | Description |
|-------|------|-------------|
| `label` | string | The action item text |
| `assignee` | string | Who it's assigned to (usually "me") |
| `context` | string | AI-generated context/explanation |
| `dueDate` | string? | ISO 8601 date or null |
| `priority` | string? | "High", "Medium", "Low", or null |
| `type` | string | Action type (CreateReminder, etc.) |
| `payload` | object | Type-specific data |

---

## Date Handling

- All dates are ISO 8601 format
- Server interprets dates as **UTC**
- `createdAt` on recordings is reliable for incremental sync

---

## Rate Limits

- Not officially documented
- In practice: reasonable usage is fine
- Power-Flow fetches lazily (only full recording when needed)

---

## Error Responses

```json
{
  "error": {
    "code": "unauthorized",
    "message": "Invalid API key"
  }
}
```

Common codes:
- `unauthorized` — Bad API key
- `not_found` — Recording ID doesn't exist
- `rate_limited` — Too many requests

---

## Notes

- API is read-only (no create/update endpoints for recordings)
- Action items can't be marked complete via API
- Transcript includes word-level timestamps
- Mind map is a structured node tree (useful for hierarchy)
