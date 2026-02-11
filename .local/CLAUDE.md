# Coding Contract

Ship correct, minimal changes with high confidence.

---

## Session Start

Read in order:
1. `.local/claude/state/current-state.md` — where we are
2. `.local/claude/knowledge-base/lessons-learned.md` — mistakes to avoid
3. `PROJECT.md` — project context (if exists)

---

## The Loop

Every task follows this pattern:

```
UNDERSTAND → PLAN → IMPLEMENT → VERIFY → REPORT
```

### 1. Understand
- Read relevant files before touching them
- If requirements are unclear: ask 2-3 targeted questions, then propose
- Never assume — state assumptions explicitly

### 2. Plan
- Break into smallest possible steps
- Identify risks before writing code
- For complex decisions, use structured reasoning:
  ```
  Options: A, B, C
  Tradeoffs: [brief for each]
  Recommendation: X because Y
  ```

### 3. Implement
- One step at a time
- Smallest viable diff — no drive-by refactors
- Run tests between steps
- If something breaks, stop and assess

### 4. Verify
- Run the actual tests (not "tests would pass")
- Show the output
- Verification is part of the task, not optional

### 5. Report
Every response ends with:
```
## Summary
- [what was done]

## Files Changed
- `path/file` — why

## Verified
$ [command run]
[output]

## Next
- [if more steps needed]
```

---

## Rules

**Code quality**
- Prefer explicit over clever
- Prefer composition over inheritance
- Prefer pure functions where practical
- No dead code, no commented-out code
- Tests when behavior changes

**Git**
- Atomic commits with descriptive messages
- Never commit secrets (use `.env.example`)
- Don't rewrite shared history

**Safety**
- Ask before destructive operations (`rm`, migrations, mass changes)
- Prefer `trash` over `rm`
- Create safety snapshot before large refactors:
  ```bash
  git stash push -m "safety: before [operation]"
  ```

**Scope**
- Stay in lane — change only what's requested
- If you spot unrelated issues, note them for later
- If tempted to "clean up" nearby code, don't

---

## Self-Review Checklist

Before presenting code, verify:
- [ ] Solves the actual problem (not an adjacent one)
- [ ] No syntax errors
- [ ] No obvious logic errors
- [ ] No hardcoded values that should be config
- [ ] No secrets or sensitive data
- [ ] Imports are used
- [ ] Functions are called
- [ ] Error cases handled
- [ ] Tests pass

---

## Common Failure Modes (Guard Against)

| Failure | Prevention |
|---------|------------|
| Over-engineering | Ask: "Is this the simplest solution?" |
| Helpful rewrites | Touch only what's needed |
| Assuming it works | Run the tests, show output |
| Hallucinating APIs | Verify with docs or quick test |
| Scope creep | Finish current task first |
| Lost context | Re-read state file if uncertain |
| Forgetting to update state | Do it at session end, always |

---

## When Stuck

1. **State the problem clearly** — often this reveals the solution
2. **Check what was already tried** — `.local/claude/state/current-state.md`
3. **Reduce scope** — solve a smaller version first
4. **Ask** — a focused question beats thrashing

---

## Session End

Before stopping:
1. Update `.local/claude/state/current-state.md`:
   - What was completed
   - What's next
   - Any blockers or open questions
2. Commit if there's meaningful progress
3. Note any learnings for `.local/claude/knowledge-base/lessons-learned.md`

---

## Deep Dives

| Topic | File |
|-------|------|
| Detailed workflows | `.local/claude/workflows/` |
| Coding rules | `.local/claude/rules/` |
| Past learnings | `.local/claude/knowledge-base/` |
| Checklists | `.local/claude/templates/` |
| Best practices 2026 | `.local/claude/BEST_PRACTICES_2026.md` |
