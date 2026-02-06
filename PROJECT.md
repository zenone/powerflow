# Power-Flow

## One-liner

Sync Pocket AI action items and summaries to Notion with smart deduplication.

## Users

Pocket AI device owners who use Notion for task management.

## Success Criteria (v1)

- [ ] `powerflow setup` discovers Notion databases and configures mapping
- [ ] `powerflow sync` pulls action items and creates Notion pages
- [ ] Deduplication prevents duplicate entries on re-sync
- [ ] Clear error messages for common issues (bad API key, no access, etc.)
- [ ] Works on fresh clone with just API keys

## Constraints

- Security: API keys in `.env` only, never in git
- Testing: Unit tests for API clients, integration tests for sync
- API-first: Clean separation between API clients and CLI
- UX: Low friction setup (auto-discover, smart-map, confirm)

## Non-Goals (v1)

- Webhook receiver (push mode) — future enhancement
- Two-way sync (Notion → Pocket)
- Web UI
- OAuth flow (internal integration token is sufficient)

## Architecture

```
Pocket AI API → Power-Flow CLI → Notion API
                     │
                     ▼
              ~/.powerflow/
              config.json
```

**Pull mode only (v1)**: Run `powerflow sync` manually or via cron.

## Dev Workflow

- **Run**: `python -m powerflow sync`
- **Test**: `pytest`
- **Install**: `pip install -e .`
