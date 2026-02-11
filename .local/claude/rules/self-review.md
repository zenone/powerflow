# Self-Review Protocol

Review your own code before presenting. Catch what you can catch.

---

## Before Every Response

### Syntax & Structure
- [ ] Valid syntax (no typos, matched brackets)
- [ ] Imports are used (no dead imports)
- [ ] Functions are called (no dead code)
- [ ] Variables are used (no orphaned declarations)

### Logic
- [ ] Solves the actual problem (not an adjacent one)
- [ ] Edge cases handled (null, empty, zero, negative)
- [ ] Error paths handled (not just happy path)
- [ ] Loop termination guaranteed (no infinite loops)
- [ ] Off-by-one errors checked (boundaries, indices)

### Security
- [ ] No hardcoded secrets
- [ ] No SQL injection vectors
- [ ] No path traversal risks
- [ ] User input validated/sanitized

### Quality
- [ ] Names are clear and accurate
- [ ] No magic numbers (use constants)
- [ ] No commented-out code
- [ ] No debug statements left behind
- [ ] Consistent style with existing code

### Completeness
- [ ] All files needed are included
- [ ] File paths are correct
- [ ] Changes work together (not orphaned)

---

## Common Self-Review Catches

| Issue | Check |
|-------|-------|
| Import not used | Search for usage in file |
| Function never called | Search for calls |
| Typo in name | Compare declaration to usage |
| Missing error handling | Trace through failure paths |
| Hardcoded value | Should this be config? |
| Missing null check | What if this is undefined? |

---

## The 5-Second Rule

After writing code, wait 5 seconds and re-read it.

You'll catch:
- Obvious typos
- Copy-paste errors
- Things that don't make sense

This simple pause prevents embarrassing mistakes.

---

## Red Flags

If you see yourself doing any of these, stop and reconsider:

- Writing more than 100 lines without testing
- Changing files outside the current task
- Adding "temporary" code
- Using string manipulation for structured data (JSON, HTML, SQL)
- Catching exceptions and doing nothing
- Using `any` type or disabling type checks
- Copy-pasting code instead of abstracting

---

## When Self-Review Fails

If you find bugs after presenting:
1. Acknowledge immediately
2. Explain what went wrong
3. Fix it completely
4. Add the pattern to your review checklist

Learning from mistakes > pretending perfection.
