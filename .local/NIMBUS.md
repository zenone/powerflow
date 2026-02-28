# Nimbus Project Guidance — Powerflow

Actions over advice. Read files, make minimal diffs, verify, report.

**Continuous Improvement**: See `.local/claude/rules/continuous-improvement.md` for self-healing and self-improvement directives.

---

## Audit Gates (MANDATORY)

Powerflow has a living audit gate registry: `.local/AUDIT-GATES.md`

**Rule:** When you commit a new design decision or invariant, you MUST add a gate in the same commit.

Gate format:
```
## D-PF-NNN — Short description
**Invariant:** What must always be true and why.
**Command:**
\`\`\`bash
<bash command that outputs violations only; empty = pass>
\`\`\`
**Pass:** zero output
```

Run all gates:
```bash
bash ~/Dropbox/.nimbus-shared/scripts/audit-gates-check.sh ~/Code/powerflow
```

**Current gates (6):** D-PF-001 through D-PF-006 — all passing.

Examples of things that need a gate:
- New write path to Notion → gate that only allowed callers exist
- New env var required → gate that no hardcoded fallback exists in source
- New dedup mechanism → gate that old bypass patterns don't appear

---

## Session Start

```
1. Read .local/CLAUDE.md                              ← coding contract
2. Read .local/claude/state/current-state.md          ← current focus
3. Read .local/claude/knowledge-base/lessons-learned.md  ← avoid repeating mistakes
4. Read PROJECT.md (if exists)                        ← project context
5. Run audit-gates-check.sh                           ← verify invariants before touching code
```

If `PROJECT.md` doesn't exist → create from `docs/PROJECT.md.template`

---

## The Loop

```
UNDERSTAND → PLAN → EXECUTE → VERIFY → REPORT
```

### Understand
- Read before changing
- If unclear, ask targeted questions
- State assumptions explicitly

### Plan
- Break into small steps
- One task at a time
- Identify risks upfront

### Execute
- Smallest viable diff
- Run tests between changes
- Stop if something breaks

### Verify
- Run actual commands
- Show actual output
- Never say "this should work"

### Report
```
## Summary
- [what was done]

## Files
- `path/file` — why

## Verified
$ command
output

## Next
- [if applicable]
```

---

## Rules

**Ask first:**
- `rm` anything (use `trash`)
- Database migrations
- Mass renames/refactors
- Anything irreversible

**Stay in scope:**
- Change only what's requested
- No drive-by refactors
- Note unrelated issues for later

**Verify everything:**
- Run the test, show the output
- Don't assume it works
- Check error cases

---

## OpenClaw-Specific

**Spawn sub-agents** for research-heavy tasks:
```
sessions_spawn: "Research [topic] and summarize findings"
```

**Use cron** for reminders and delayed actions.

**Cross-session context:**
- Check `memory/*.md` for recent history
- Update state files after meaningful progress

---

## When Stuck

1. State the problem clearly
2. Check what was tried: `.local/claude/state/current-state.md`
3. Reduce scope — solve smaller version first
4. Ask a focused question

---

## Session End

1. Update `.local/claude/state/current-state.md`:
   - Completed
   - Next steps
   - Blockers
2. Commit meaningful progress
3. Add learnings to `lessons-learned.md` if applicable

---

## Reference

| Need | Location |
|------|----------|
| Full coding contract | `.local/CLAUDE.md` |
| Workflows | `.local/claude/workflows/` |
| Rules | `.local/claude/rules/` |
| Learnings | `.local/claude/knowledge-base/` |
| Checklists | `.local/claude/templates/` |
