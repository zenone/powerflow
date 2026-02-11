# Feature Development Workflow

From idea to shipped. One step at a time.

---

## Phase 1: Understand

**Goal**: Crystal clarity on what we're building.

### Actions
1. Read existing context:
   - `PROJECT.md` — project spec
   - `.local/claude/state/current-state.md` — current status
   - Related code files

2. Clarify requirements:
   - What problem does this solve?
   - Who uses it?
   - What's the success criteria?
   - What's explicitly out of scope?

3. If anything is unclear:
   - Ask 2-3 targeted questions
   - Don't guess — wrong assumptions waste time

### Deliverable
```
## Understanding
- Feature: [name]
- Purpose: [one sentence]
- User: [who benefits]
- Success: [how we know it works]
- Scope: [what's included/excluded]
```

---

## Phase 2: Plan

**Goal**: A clear, reviewable plan before writing code.

### Actions
1. Break the feature into steps (3-7 typically)
2. Identify dependencies between steps
3. Note risks and unknowns
4. Estimate relative complexity

### Deliverable
```
## Plan
1. [Step] — [why first]
2. [Step] — [depends on 1]
3. [Step] — [can be parallel]
...

Risks:
- [Risk] → [mitigation]

Questions (if any):
- [Thing to verify before starting]
```

### Checkpoint
**Stop and confirm** the plan before implementing. Wasted planning is cheaper than wasted code.

---

## Phase 3: Implement

**Goal**: Working code, one step at a time.

### For Each Step

1. **Write the code**
   - Smallest viable change
   - Follow existing patterns
   - No drive-by refactors

2. **Test the change**
   - Run existing tests
   - Add new tests if behavior changed
   - Manual verification for UI changes

3. **Commit**
   - Atomic commit for this step
   - Clear message: `feat: add X to Y`

4. **Update state**
   - Note progress in `current-state.md`
   - Especially important if session might end

### Red Flags During Implementation
- Changing files outside the plan → stop, reassess
- Tests failing unexpectedly → fix before continuing
- Taking longer than expected → update plan, maybe split
- Finding a better approach → finish current step, then propose

---

## Phase 4: Verify

**Goal**: Confidence it works correctly.

### Verification Checklist
- [ ] All tests pass
- [ ] New tests cover new behavior
- [ ] Manual testing of happy path
- [ ] Manual testing of error cases
- [ ] Code matches the plan (no extra, no missing)
- [ ] No regressions in existing functionality

### Commands to Run
```bash
# Run full test suite
make test  # or: npm test / pytest

# Lint and type check
make lint  # or: npm run lint / mypy

# If applicable: check formatting
make format --check
```

---

## Phase 5: Ship

**Goal**: Code is in a reviewable/mergeable state.

### Pre-Ship Checklist
- [ ] All commits are clean and atomic
- [ ] Branch is rebased on main (if using branches)
- [ ] Tests pass in CI
- [ ] Documentation updated (if public API changed)
- [ ] `current-state.md` reflects completion

### Ship Actions
```bash
# Final commit if needed
git add -A && git commit -m "feat: [feature name]"

# Push
git push origin [branch]

# If direct to main
git push
```

---

## Deliverable Summary

Every completed feature should have:

```
## Summary
- Implemented: [what]
- Tests: [added/modified]
- Docs: [updated/none needed]

## Files Changed
- `path/file.py` — [what changed]
- `tests/test_file.py` — [tests added]

## Verified
$ make test
[output showing pass]

## Next Steps
- [if any follow-up needed]
```

---

## Common Pitfalls

| Pitfall | Prevention |
|---------|------------|
| Starting without clear requirements | Phase 1 — don't skip it |
| Big bang implementation | One step at a time, commit each |
| Testing at the end | Test after each step |
| Scope creep | Stick to the plan, note extras for later |
| Skipping verification | Run the tests, show the output |
| Incomplete handoff | Update state file, even if done |
