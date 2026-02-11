# Lessons Learned

Hard-won patterns from real projects. Read before making similar mistakes.

---

## Power-Flow Specific

### API URL Discovery (2026-02-06)

**Issue**: Third-party API base URL wasn't documented publicly.

**Lesson**: Always make API base URLs configurable via environment variable. Don't hardcode.

```python
DEFAULT_BASE_URL = "https://api.example.com"
BASE_URL = os.getenv("API_URL", DEFAULT_BASE_URL)
```

**Prevention**: Early in any integration project, verify API connectivity before writing business logic.

---

### Deduplication Strategy (2026-02-06)

**Requirement**: NEVER create duplicate entries in Notion database.

**Solution**: Store a unique `pocket_id` in Notion and check before creating.

**Implementation**:
```python
# Generate unique ID for each action item
pocket_id = f"pocket:{recording_id}:{action_index}"

# Check if exists before creating
def page_exists_by_pocket_id(database_id, pocket_id, property_name):
    filter_obj = {
        "property": property_name,
        "rich_text": {"equals": pocket_id}
    }
    results = query_database(database_id, filter_obj, page_size=1)
    return len(results) > 0
```

**Key points**:
- Check BEFORE creating, not after
- Use exact match filter, not contains
- Store the pocket_id as rich_text in a dedicated property
- ID format: `pocket:{recording_id}:{index}` ensures uniqueness

---

### Notion Property Type Mismatch (2026-02-06)

**Issue**: Tried to set a `relation` property with `rich_text` data.

**Symptom**: 400 Bad Request from Notion API.

**Root cause**: The "Context" property in user's Notion database was a relation to another database, not a text field.

**Lesson**: Always check property types before mapping:
```python
schema = notion.get_database_schema(database_id)
for name, prop in schema.items():
    prop_type = prop.get("type")  # "rich_text", "relation", "select", etc.
```

**Fix**: Map to a compatible property type or skip incompatible properties.

---

---

## 🏗️ Architecture

**Start minimal, extend later**
- Don't build for hypothetical scale
- Add abstractions when you need them twice
- YAGNI is almost always right

**Vertical slices over horizontal layers**
- Build one feature end-to-end before abstracting
- Proves the architecture with real code
- Catches integration issues early

**Configuration over code**
- Environment variables for deployment config
- Feature flags for runtime behavior
- Hardcoded values become tech debt

**API-first for multi-interface apps**
- `api/` layer consumed by both `web/` and `cli/`
- Same logic, tested once, consistent behavior
- Never import from `core/` in UI layers

**Daemon + job queue for privileged operations**
- Web/CLI can't run sudo commands safely
- Solution: Root daemon watches job queue, app writes jobs
- Clean privilege separation = no password prompts in UI

---

## ✨ Code Quality

**Small functions, clear names**
- If you need a comment to explain what, rename it
- Comments explain why, not what
- Functions over 30 lines usually need splitting

**Explicit over clever**
- Clever code is write-once, debug-forever
- Future you is tired and confused
- Boring code is good code

**Error handling is not optional**
- Handle errors where you can do something about them
- Propagate errors where you can't
- Never swallow errors silently

**Types are documentation**
- Use TypeScript for any JS > 200 lines
- Python type hints catch bugs before runtime
- Types make refactoring safe

---

## 🧪 Testing

**Test behavior, not implementation**
- Tests that break on refactors are worse than no tests
- Focus on inputs and outputs
- Mock at boundaries, not everywhere

**The testing pyramid is real**
- Many unit tests (fast, isolated)
- Some integration tests (boundaries)
- Few E2E tests (critical paths only)

**Flaky tests are toxic**
- Fix immediately or delete
- They erode trust in the suite
- A flaky test is worse than no test

**Fresh clone test**
- `git clone <repo> /tmp/test && cd /tmp/test && ./run.sh`
- If it doesn't work on fresh clone, it doesn't work
- Do this before every release

---

## 📝 Git

**Atomic commits**
- One logical change per commit
- Should be revertable independently
- Makes bisect possible

**Commit messages matter**
- Future you will search them
- Format: `type: what (why)`
- Examples: `fix: null check in auth (edge case from prod logs)`

**Never rewrite shared history**
- Force push to feature branches only
- Rebasing shared branches breaks teammates
- If in doubt, merge

**Audit scripts before release**
- All essential scripts tracked (`git ls-files | grep scriptname`)
- No hardcoded paths (use `$SCRIPT_DIR` or `$HOME`)
- `.gitignore` patterns can hide essential files—verify!

---

## 🐛 Debugging

**Reproduce first, fix second**
- Can't fix what you can't see
- Write a failing test before fixing
- Prevents regression

**Binary search is your friend**
- git bisect for regressions
- Comment out half the code
- Narrow the search space

**Read the error message**
- Seriously, the whole thing
- Line numbers are hints, not guarantees
- Stack traces read bottom-up for cause

---

## 🔧 Shell Scripts

**Scripts must work from any directory**
```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
```
- All shell scripts should `cd` to their own directory first
- Never use relative paths without `$SCRIPT_DIR`

**Preview mode for destructive operations**
- `--preview` shows what would happen without doing it
- Users trust tools that let them look before leaping
- Same code path, just skip the `execute()` call

---

## 🚀 Process

**Ship small, ship often**
- Big PRs are review nightmares
- Small changes are easy to reason about
- Easier to rollback

**Document decisions, not just code**
- Why matters more than what
- ADRs (Architecture Decision Records) pay off
- Future you will thank present you

**Automate what hurts**
- If you do it twice, consider scripting
- If you do it wrong once, definitely script it
- CI catches what humans miss

**Two-phase development workflow**
- Phase 1: Requirements, approach, edge cases, get approval
- Phase 2: Implement, test, ship
- Never start coding without a written plan

**Kill features that don't work**
- If a feature has 3+ sessions of debugging without resolution, cut it
- A polished single interface > buggy multiple interfaces
- Sunk cost is still sunk

---

## ⚠️ Common Traps

| Trap | Escape |
|------|--------|
| Premature optimization | Profile first, optimize measured hotspots |
| Over-engineering | Build for today, design for tomorrow |
| Not-invented-here | Use boring, proven libraries |
| Sunk cost fallacy | Delete bad code, even if it took hours |
| Gold plating | Ship the MVP, iterate based on feedback |
| Analysis paralysis | Timebox decisions, bias toward action |
| Gitignore hiding essentials | `git ls-files` audit before release |

---

## 🍎 macOS-Specific

**Root daemon can't access user files (TCC)**
- macOS Transparency, Consent, and Control blocks root from user directories
- Symptom: `Operation not permitted` on ~/.profile, ~/.gitconfig
- Fix: Check file accessibility before reading/writing
- Rule: Never assume root can access user files on modern macOS

**Naming: do it right on day 1**
- Renaming a shipped project is painful (paths, imports, system dirs)
- 50+ files to change, easy to miss something
- Either name it right initially or accept the name forever

---

## 🤖 AI-Specific Learnings

**Context is king**
- State files prevent thrashing
- Re-read after long responses
- Update state before ending session

**Verify, don't trust**
- Run the tests, show the output
- Check that imports are used
- Check that functions are called

**Scope discipline**
- Finish current task before starting new ones
- Note unrelated issues, don't fix them
- Drive-by refactors cause drive-by bugs

**Recovery patterns**
- `git stash` before risky operations
- `trash` instead of `rm`
- Commit working states frequently

**State files over agent memory**
- If it matters tomorrow, write it to disk today
- Agent context doesn't persist between sessions
- JSON files in `~/.appname/` for user config

---

## 🎨 Notion API Rich Content (2026-02-06)

### Page Properties vs Page Body

**Insight**: Notion pages have TWO distinct content areas:
1. **Properties**: Database fields (title, date, select, etc.) — shown in table views
2. **Children (body)**: Block content inside the page — visible when opened

**v0.1 mistake**: Only populated properties, left body empty.

**v0.2 fix**: Use `children` parameter in create page API:
```python
payload = {
    "parent": {"database_id": db_id},
    "properties": {...},
    "children": [...]  # Page body content
}
```

### Block Types for Visual Impact

| Use Case | Block Type | Why |
|----------|------------|-----|
| Highlight context | `callout` | Colored background, icon, stands out |
| Source metadata | `toggle` | Collapsed by default, reduces noise |
| Clickable links | `paragraph` with rich_text link | Inline link styling |
| Visual separation | `divider` | Clean section breaks |
| Lists | `bulleted_list_item` | Clean metadata display |
| Quotes | `quote` | Transcript excerpts, citations |

### Rich Text Limits

**Critical**: Notion rich_text objects have a 2000 character limit per content block.

**Solution**:
```python
def safe_text(text: str, max_length: int = 1900) -> str:
    if not text or len(text) <= max_length:
        return text or ""
    return text[:max_length - 3] + "..."
```

### Priority-Based Visual Styling

Map priority levels to visual treatments:
```python
PRIORITY_STYLES = {
    "High": {"icon": "🔥", "color": "red_background"},
    "Medium": {"icon": "⚡", "color": "yellow_background"},
    "Low": {"icon": "📝", "color": "gray_background"},
    None: {"icon": "💡", "color": "default"},
}
```

### Rate Limiting

- Notion API: ~3 requests/second average
- For bulk operations: add sleep between requests
- Check for `429` status and respect `Retry-After` header

### Batch Deduplication

**N+1 problem**: Checking each item individually = N queries.

**Better**: Batch query existing IDs with OR filter:
```python
filter_obj = {
    "or": [
        {"property": "Inbox ID", "rich_text": {"equals": id}}
        for id in pocket_ids[:100]  # Notion limit
    ]
}
```

---

## 🧐 Questions to Ask Before Building Any Integration

1. **What data is available?** (List ALL fields from source API)
2. **What data is valuable?** (Not all data deserves a property)
3. **What's the visual hierarchy?** (What should users see first?)
4. **What can be collapsed?** (Toggle blocks hide verbose data)
5. **What needs color coding?** (Priority, status, urgency)
6. **What links back to source?** (Always include origin URL)
7. **What about duplicates?** (Dedup strategy is day-1 requirement)
8. **What about rate limits?** (Check API docs, implement backoff)
9. **What about large payloads?** (Truncation, pagination)
10. **What about incremental sync?** (Don't re-fetch everything every time)

---

## 🧪 Testing Lessons (2026-02-06)

### Version Sync

**Issue**: `__init__.py` had `__version__ = "0.1.0"` while `pyproject.toml` had `0.3.0`.

**Symptom**: `powerflow --version` showed wrong version.

**Prevention**: 
- Single source of truth: consider reading version from pyproject.toml dynamically
- Or: add version check to CI/test suite

### Feature Wiring

**Issue**: Implemented tags sync in models but forgot to wire it into the setup wizard.

**Lesson**: New features need wiring in:
1. Core logic (models, sync engine) ✅
2. API client (Notion property creation) ← forgot multi_select
3. CLI (setup wizard mapping) ← forgot tags
4. Tests ✅
5. Documentation ✅

**Prevention**: Feature checklist:
```
[ ] Core logic
[ ] API layer
[ ] CLI integration
[ ] Tests
[ ] README
```

### Edge Case Testing

**Valuable edge cases discovered**:
- Empty Pocket account (no recordings)
- Recordings without action items
- Whitespace-only labels
- Empty string tags
- Sync before setup
- API failures mid-sync
- Single item failure shouldn't stop entire sync

**Pattern**: Test the boundaries:
- Zero items
- One item
- Many items
- Invalid items
- Partial failure

---

## 🤖 Daemon Design Lessons (2026-02-06)

### Set and Forget UX

**User expectation**: Install once, never think about it again.

**Implementation layers**:
1. `powerflow sync` — Manual one-shot
2. `powerflow daemon start` — Background process (session-lived)
3. `powerflow daemon install` — System service (survives reboot)

Each layer builds on the previous. Users choose their comfort level.

### Daemon Best Practices

**PID file** — Prevent multiple instances:
```python
PID_FILE = CONFIG_DIR / "daemon.pid"

def is_running() -> tuple[bool, int]:
    if not PID_FILE.exists():
        return False, None
    pid = int(PID_FILE.read_text())
    os.kill(pid, 0)  # Check if process exists
    return True, pid
```

**Graceful shutdown** — Handle SIGTERM/SIGINT:
```python
signal.signal(signal.SIGTERM, self._handle_shutdown)
self.running = False  # Let loop exit cleanly
```

**State file** — Track last sync, next sync, results:
```python
save_state({
    "status": "running",
    "last_sync": datetime.now().isoformat(),
    "next_sync": (datetime.now() + timedelta(minutes=interval)).isoformat(),
    "last_result": {"created": 3, "skipped": 2},
})
```

**Check for shutdown during sleep** — Don't block for full interval:
```python
# Bad: time.sleep(900)  # Blocks shutdown for 15 min
# Good:
while waited < wait_seconds and self.running:
    time.sleep(10)
    waited += 10
```

### Optimal Polling Intervals

| Use case | Interval |
|----------|----------|
| Development/testing | 1-5 min |
| Power user | 5-10 min |
| Normal use | 15 min (default) |
| Battery-conscious | 30-60 min |

**Key insight**: Pocket is user-driven (recordings happen when you talk). Polling every minute is wasteful — nothing will be there most of the time.

### launchd Service (macOS)

Key plist settings:
- `StartInterval`: Seconds between runs
- `RunAtLoad`: Start on boot/login
- `EnvironmentVariables`: Pass API keys (or use shell profile)

**Gotcha**: launchd doesn't source your `.bashrc`/`.zshrc`. API keys must be in the plist's EnvironmentVariables or set system-wide.

### Retry Logic Pattern

**Problem**: Network hiccup at 2am → 15 min wait → user misses time-sensitive item.

**Solution**: Retry failed syncs quickly before falling back to normal interval:
```python
RETRY_DELAY_SECONDS = 60
MAX_RETRIES = 2

if "error" in result:
    consecutive_failures += 1
    if consecutive_failures <= MAX_RETRIES:
        wait_seconds = RETRY_DELAY_SECONDS  # Quick retry
    else:
        wait_seconds = interval_minutes * 60  # Give up, wait normally
        send_notification("Sync Failed", "Check logs")
else:
    consecutive_failures = 0  # Reset on success
```

### Desktop Notifications Pattern

**When to notify**:
- ✅ New items synced (user wants to know)
- ✅ Persistent failure (user needs to act)
- ✅ Daemon started (confirmation)
- ❌ Every sync attempt (too noisy)
- ❌ Skipped items (not actionable)

**macOS implementation** (silent fail on other platforms):
```python
def send_notification(title: str, message: str) -> None:
    if sys.platform != "darwin":
        return
    try:
        subprocess.run(
            ["osascript", "-e", f'display notification "{message}" with title "{title}"'],
            capture_output=True, timeout=5
        )
    except Exception:
        pass  # Best-effort, never crash
```

---

## 📦 v0.4.0 Design Pivot (2026-02-06)

### Recording-Centric > Action-Item-Centric

**Original design (v0.1-v0.3)**: Sync individual action items extracted by Pocket AI.

**Problem discovered**: 
- Not all recordings have action items
- Pocket AI's extraction is imperfect — "buy milk" might not be recognized
- User's GTD workflow wants EVERYTHING in inbox for triage

**New design (v0.4.0)**: Sync entire RECORDINGS as inbox items.
- Each recording = one Notion page
- Action items appear as to-do checkboxes inside the page
- Summary, tags, transcript all preserved
- User decides what each recording becomes

**Key insight**: Don't let the AI decide what's important. Give the human everything and let them triage.

### Property Map Configuration Bug

**Issue**: Tags weren't syncing to Notion even though code supported it.

**Root cause**: The config's `property_map` was missing `"tags": "Tags"`. The setup wizard didn't auto-add it.

**Symptom**: Code worked fine, tests passed, but real sync didn't include tags.

**Lesson**: When adding new property mappings:
1. Update setup wizard to offer the mapping
2. Verify config file actually has the mapping after setup
3. Test with real API, not just mocked tests

**Fix pattern**:
```python
# Check and add missing mappings
if "tags" not in config.notion.property_map:
    config.notion.property_map["tags"] = "Tags"
    config.save()
```

### Smart Icons from Tags

**Design decision**: Auto-assign Notion page icons based on tags.

**Implementation**:
```python
TAG_EMOJI_MAP = {
    "work": "💼", "meeting": "📅", "idea": "💡",
    "reminder": "⏰", "personal": "👤", "task": "✅",
    "note": "📝", "question": "❓", "important": "⭐", "urgent": "🔥",
}
DEFAULT_EMOJI = "🎙️"  # Mic for voice recordings

def get_icon(self) -> dict:
    for tag in self.tags:
        normalized = tag.strip().lower()
        if normalized in TAG_EMOJI_MAP:
            return {"type": "emoji", "emoji": TAG_EMOJI_MAP[normalized]}
    return {"type": "emoji", "emoji": DEFAULT_EMOJI}
```

**UX benefit**: Visual scanning in Notion database view. Users instantly see what type of recording it is.

### Notion Page Body Structure (Michelin-Star Design)

**Goal**: Each page should be beautiful AND functional.

**Structure**:
```
┌─────────────────────────────────────────────┐
│ 💼 Recording Title                          │  ← Smart icon
├─────────────────────────────────────────────┤
│ 💭 [CALLOUT - gray]                         │
│    AI Summary text...                       │  ← Context first
│                                             │
│ ### Action Items                            │  ← H3 heading
│ ☐ Task 1 [High] — due Feb 10               │  ← To-do blocks
│ ☐ Task 2 [Medium]                          │
│                                             │
│ ─────────────────────────────────────────── │  ← Divider
│                                             │
│ ▸ 📎 Source Details                        │  ← Toggle (collapsed)
│     • Duration: 5:23                       │
│     • Captured: Feb 6, 2026                │
│     • Open in Pocket AI →                  │
│     ▸ 📝 Full Transcript                   │  ← Nested toggle
└─────────────────────────────────────────────┘
```

**Key decisions**:
- Summary callout FIRST (most important context)
- Action items with proper H3 heading (not fake markdown bold)
- Metadata collapsed by default (reduces noise)
- Transcript double-nested (rarely needed but available)

### Timezone Bug Pattern

**Issue**: `TypeError: can't compare offset-naive and offset-aware datetimes`

**Root cause**: `last_sync` stored as naive datetime, Pocket API returns UTC-aware timestamps.

**Fix**:
```python
def parse_datetime(dt_str: str) -> datetime:
    """Parse ISO datetime, ensuring UTC timezone."""
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
```

**Lesson**: ALL datetimes in sync systems should be timezone-aware UTC. Convert at boundaries, compare in UTC.

---

## 📝 Notion Markdown Rendering (2026-02-06)

### The Problem

Pocket's summary contains markdown:
```markdown
### Ethical Decision Making
- **Speaker 0** introduced a concept...
  - This approach is more complex...
```

But Notion doesn't render markdown syntax — it uses native blocks. Result: raw `###` and `**` displayed as text.

### The Solution

Parse markdown and convert to Notion blocks:

```python
def parse_markdown_to_blocks(markdown: str) -> list[dict]:
    blocks = []
    for line in markdown.split('\n'):
        if line.startswith('### '):
            # Create heading_3 block
            blocks.append(create_heading(line[4:], level=3))
        elif line.lstrip().startswith('- '):
            # Create bullet with bold parsing
            blocks.append(create_bullet_with_markdown(line))
        else:
            blocks.append(create_paragraph(line))
    return blocks

def parse_bold_segments(text: str) -> list[dict]:
    """Parse **bold** into rich_text with annotations."""
    # Use regex to find **text** and create bold annotations
    pattern = r'\*\*([^*]+)\*\*'
    # ... returns list of rich_text objects with bold=True where needed
```

### Key Insight

Notion API rich_text supports `annotations.bold` — but you must build the array yourself:
```python
rich_text = [
    {"type": "text", "text": {"content": "Hello "}},
    {"type": "text", "text": {"content": "world"}, "annotations": {"bold": True}},
]
```

### Result

- `### Heading` → Native Notion heading_3 block
- `- **Bold** item` → Bullet with bold text properly rendered
- Clean visual hierarchy instead of raw markdown

---

*Update this file when you learn something the hard way.*

---

## Summary Completion Check (2026-02-07)

### Problem
User reported concern about race conditions: what if a recording syncs to Notion before Pocket AI finishes generating the summary?

### Root Cause Analysis
Pocket AI processes recordings asynchronously. When you fetch a recording immediately after creation:
- `summarizations.v2_summary.markdown` may be empty
- `summarizations.v2_action_items.actions` may be empty
- `summarizations.v2_mind_map.nodes` may be empty

The current code would create a Notion page with no meaningful content.

### Solution
Added `is_summary_complete` property to Recording model:

```python
@property
def is_summary_complete(self) -> bool:
    has_summary = bool(self.summary and self.summary.strip())
    has_actions = len(self.action_items) > 0
    has_mind_map = len(self.mind_map) > 0
    return has_summary or has_actions or has_mind_map
```

Sync engine now checks this before creating pages:
```python
if not recording.is_summary_complete:
    result.pending += 1
    continue  # Will be picked up on next sync
```

### Key Design Decisions

1. **Check ANY AI content, not just summary**: A recording might have action items but no summary, or vice versa. Any AI-generated content indicates processing is complete.

2. **Skip, don't error**: Incomplete recordings should be silently skipped and retried. Users don't need alerts about normal processing delays.

3. **Don't update last_sync for pending**: The sync continues normally; pending recordings will naturally be included in the next sync since we use incremental sync based on `createdAt`.

4. **Add "pending" counter**: Daemon and CLI now report pending count separately from skipped (dedup) and failed.

### Testing

Added 7 tests for the new behavior:
- `test_complete_with_summary`
- `test_complete_with_action_items`
- `test_complete_with_mind_map`
- `test_incomplete_without_ai_content`
- `test_incomplete_with_empty_summary`
- `test_incomplete_with_empty_lists`
- `test_complete_with_multiple_indicators`

### Lesson
When integrating with AI processing pipelines, always account for asynchronous processing. Data may be available before it's fully processed.
