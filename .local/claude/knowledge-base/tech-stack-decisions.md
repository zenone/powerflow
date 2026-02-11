# Tech Stack Decisions

## [2026-02-06] Language: Python 3.10+

**Decision**: Python 3.10+ with type hints

**Rationale**:
- User's existing ecosystem (Pocket AI has Python SDK patterns)
- Excellent HTTP library support (requests)
- Type hints for maintainability
- Fast iteration for CLI tools

**Trade-offs**:
- Slower than compiled languages (acceptable for CLI tool)
- Requires Python runtime (common on dev machines)

---

## [2026-02-06] HTTP Client: requests

**Decision**: Use `requests` library for HTTP

**Rationale**:
- Industry standard, well-tested
- Simple API for REST calls
- Good error handling
- Session support for auth headers

**Alternatives Considered**:
- `httpx` (async support, but adds complexity)
- `urllib3` (lower-level, more boilerplate)

---

## [2026-02-06] CLI Framework: None (stdlib)

**Decision**: Use Python stdlib (argparse not needed for simple commands)

**Rationale**:
- Only 4-5 commands needed
- Zero dependencies
- Full control over UX
- Can add click/typer later if needed

**Trade-offs**:
- No automatic help generation (manual print_usage)
- No shell completion (can add later)

---

## [2026-02-06] Config Storage: JSON file

**Decision**: Store config at `~/.powerflow/config.json`

**Rationale**:
- Human-readable and editable
- No database dependency
- Standard XDG-ish location
- Easy to backup/sync

**Schema**:
```json
{
  "notion": {
    "database_id": "...",
    "database_name": "...",
    "property_map": {...}
  },
  "pocket": {
    "last_sync": "ISO timestamp"
  }
}
```

---

## [2026-02-06] Notion Integration: Direct API

**Decision**: Direct Notion API, not OpenClaw integration

**Rationale**:
- Wider utility (any Pocket user can use)
- Open source potential
- Full API access
- Doesn't depend on OpenClaw

**Trade-offs**:
- User must create Notion integration (2 min setup)
- Must share database with integration

---

## [2026-02-06] Deduplication: pocket_id in Notion

**Decision**: Store unique `pocket_id` in Notion database property

**Format**: `pocket:{recording_id}:{action_index}` or native action ID

**Rationale**:
- Simple query: "does page with this pocket_id exist?"
- No external state needed
- Survives config reset
- Works across machines

**Implementation**:
- Check before create using Notion filter query
- O(n) queries for n items (acceptable for small batches)

---

## [2026-02-06] Pocket API Integration

**Decision**: Direct HTTP calls via `requests` library

**Base URL**: `https://public.heypocketai.com/api/v1`
(Discovered from: https://docs.heypocketai.com/docs/api)

**Endpoints Used**:
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/public/recordings` | GET | List all recordings |
| `/public/recordings/{id}` | GET | Get full recording + action items |
| `/public/tags` | GET | List tags |
| `/public/search` | POST | Semantic search |

**Auth**: `Authorization: Bearer pk_xxx`

**Key Insight**: Action items are nested at `recording.summarizations.v2_action_items.actions[]`

---

## Dependencies (minimal)

```toml
[project.dependencies]
requests = ">=2.28.0"
```

Dev dependencies:
- pytest, pytest-cov (testing)
- ruff (linting)
- mypy (type checking)
