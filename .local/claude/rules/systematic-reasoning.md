# Systematic Reasoning

For complex decisions, don't wing it. Use structured analysis.

---

## When to Use

- Multiple valid approaches exist
- Tradeoffs aren't obvious
- Decision affects architecture
- You're uncertain which path is best
- The choice is hard to reverse

---

## The Framework

### 1. State the Problem
One sentence. What decision needs to be made?

```
Problem: How should we handle authentication in this API?
```

### 2. List Options
2-4 realistic options. Don't pad with strawmen.

```
Options:
A. JWT tokens (stateless)
B. Session cookies (server-side state)
C. OAuth2 with external provider
```

### 3. Define Criteria
What matters for this decision? Rank by importance.

```
Criteria (ranked):
1. Security — must be secure
2. Simplicity — team can maintain it
3. Performance — handle expected load
4. Flexibility — future requirements
```

### 4. Evaluate Each Option
Brief, honest assessment against criteria.

```
A. JWT
   - Security: Good (if implemented correctly)
   - Simplicity: Medium (token refresh complexity)
   - Performance: Excellent (no DB lookup)
   - Flexibility: Good (stateless scales)

B. Sessions
   - Security: Good (server-controlled)
   - Simplicity: High (well-understood)
   - Performance: Medium (session store needed)
   - Flexibility: Medium (sticky sessions at scale)

C. OAuth2
   - Security: Excellent (delegated)
   - Simplicity: Low (external dependency)
   - Performance: Medium (extra hops)
   - Flexibility: Low (provider lock-in risk)
```

### 5. Recommend
State your recommendation and the key reason.

```
Recommendation: A (JWT)

Reason: Best balance of security and simplicity for our scale.
The team is familiar with JWT patterns, and stateless tokens
simplify horizontal scaling. Session refresh adds complexity
but is a solved problem with established libraries.

Risks to monitor:
- Token size in headers
- Refresh token rotation
```

---

## Compact Format

For smaller decisions, use single-line format:

```
Options: A (JWT), B (sessions), C (OAuth2)
Tradeoffs: A=stateless+complexity, B=simple+state, C=secure+vendor
Recommendation: A — best fit for stateless API at our scale
```

---

## Anti-Patterns

**Analysis paralysis**
- Timebox decisions (30 min max for most)
- "Good enough" beats "perfect but delayed"
- You can change your mind later

**False precision**
- Don't assign numerical scores unless truly quantifiable
- "Better/Worse/Same" is often sufficient
- Fake objectivity masks subjective judgment

**Missing options**
- "Do nothing" is always an option
- "Defer the decision" is sometimes right
- Don't force a choice when waiting is smarter

**Strawman options**
- Only list viable options
- Don't pad the list to make one look good
- 2 real options > 5 fake ones

---

## Quick Decision Test

Before deep analysis, ask:

1. **Is this reversible?** If yes, bias toward action over analysis.
2. **What's the cost of being wrong?** Low cost = decide fast.
3. **Do we have enough information?** If not, what's the cheapest way to learn more?
4. **Is someone else better positioned to decide?** Escalate if so.

---

## After Deciding

1. **Document the decision** — future you will forget why
2. **Document what would change your mind** — makes it easier to revisit
3. **Move on** — don't second-guess unless new information arrives
