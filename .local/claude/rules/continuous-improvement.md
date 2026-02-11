# Continuous Improvement

Embody the spirit of autonomous self-improvement. Don't just fix bugs — evolve the codebase.

---

## Philosophy

**Kaizen**: Small, continuous improvements compound into excellence.

When working on any task, keep a background thread scanning for:
- Patterns that could be abstracted
- Error handling gaps
- Documentation that's stale or missing
- Tests that should exist but don't
- Performance improvements
- Security enhancements

---

## Self-Improvement Loop

```
DETECT → RESEARCH → PROPOSE → IMPLEMENT → VERIFY → DOCUMENT
```

### 1. DETECT

While working, notice:
- Code smells or anti-patterns
- Repeated error patterns
- Missing tests for edge cases
- Outdated comments or docs
- Opportunities for better abstractions
- Performance bottlenecks
- Security vulnerabilities

**Auto-improve if:**
- The fix is obvious and low-risk
- It doesn't change external behavior
- It can be verified immediately

### 2. RESEARCH

Before implementing non-trivial improvements:
```bash
# Use web search for current best practices
web_search: "python [topic] best practices 2025 2026"

# Or spawn a research sub-agent
sessions_spawn: "Research best practices for [topic] in Python CLI applications"
```

**Research triggers:**
- New library versions available
- Better patterns exist for this use case
- Security advisory for a dependency
- Performance optimization techniques

### 3. PROPOSE

For changes that affect behavior or architecture:
```markdown
## Improvement Proposal

**Current state**: [what exists now]
**Problem**: [why it's suboptimal]
**Proposed**: [what to do]
**Tradeoffs**: [pros/cons]
**Effort**: [low/medium/high]
**Risk**: [low/medium/high]
```

**Auto-implement** (don't ask) if:
- Risk: low
- Effort: low
- Doesn't change external behavior

**Ask first** if:
- Risk: medium or high
- Changes public API
- Affects multiple files
- Involves dependency changes

### 4. IMPLEMENT

Follow the coding contract (`CLAUDE.md`):
- Smallest viable diff
- Run tests between changes
- Atomic commits

### 5. VERIFY

- Run full test suite
- Check for regressions
- Verify the improvement actually improves things

### 6. DOCUMENT

Update relevant files:
- `lessons-learned.md` — If you learned something reusable
- `README.md` — If user-facing behavior changed
- `CHANGELOG.md` — If version-worthy change
- Code comments — If the "why" isn't obvious

---

## Self-Healing Triggers

When you encounter these, fix them:

| Issue | Action |
|-------|--------|
| Deprecated API usage | Update to current API |
| Type hint missing | Add type hints |
| Exception swallowed silently | Add proper error handling |
| Magic numbers | Extract to constants |
| Duplicate code | DRY if used 3+ times |
| Missing docstring | Add docstring |
| Flaky test | Fix or delete |
| Outdated comment | Update or remove |
| Security issue | Fix immediately, notify human |

---

## Research-First Pattern

For any improvement involving external APIs or libraries:

```python
# 1. Check current best practices
# web_search: "[library] best practices [year]"

# 2. Check for newer patterns
# web_search: "[library] deprecation warnings [year]"

# 3. Check security advisories
# web_search: "[library] security vulnerability [year]"
```

---

## Quality Gates (Self-Check)

Before considering any work complete:

- [ ] Tests pass (`pytest`)
- [ ] Types check (`mypy src/`)
- [ ] Linting passes (`ruff check src/`)
- [ ] No new warnings introduced
- [ ] Documentation updated if needed
- [ ] Commit message is descriptive

---

## What NOT to Auto-Improve

- Public API changes (breaking changes)
- Dependency version bumps (may have side effects)
- Configuration file structure
- Database schema
- Anything that requires user migration

These require explicit human approval.

---

## Session Pattern

**At session start:**
1. Read `current-state.md` for context
2. Read `lessons-learned.md` for recent issues
3. Note any improvement opportunities

**During work:**
- Fix small issues as you encounter them
- Log larger improvements for later

**At session end:**
1. Update `current-state.md` with progress
2. Add any learnings to `lessons-learned.md`
3. Commit improvements with clear messages

---

## Examples

### Good: Auto-Improve

```python
# Before: Missing type hint
def get_recording(id):
    return self._fetch(f"/recordings/{id}")

# After: Added without asking (low risk, doesn't change behavior)
def get_recording(self, recording_id: str) -> dict:
    return self._fetch(f"/recordings/{recording_id}")
```

### Good: Research First

```
Noticed: API returns timezone-naive datetimes
Action: web_search "python timezone aware datetime best practices 2026"
Result: Applied standard pattern (fromisoformat + replace(tzinfo=UTC))
Documented: Added to lessons-learned.md
```

### Good: Propose First

```markdown
## Proposal: Add retry logic to API calls

**Current**: Single attempt, fails on transient network issues
**Proposed**: Add tenacity with exponential backoff
**Tradeoffs**: +reliability, +dependency, +complexity
**Risk**: Low (well-tested library, common pattern)

Should I implement?
```

---

*The best code improves itself. Leave the codebase better than you found it.*
