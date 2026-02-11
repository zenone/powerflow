# 🧠 .local/ — Your AI Coding Brain

This is where the magic lives. Everything your AI coding assistant needs to not suck.

> **Privacy note**: This entire directory is gitignored. The public never sees it. Your AI-assisted workflow stays your secret sauce. 🤫

---

## 📁 What's Inside

```
.local/
├── CLAUDE.md           → 🎯 The coding contract (start here)
├── OPENCLAW.md         → 🤖 OpenClaw-specific instructions
├── README.md           → 📖 You are here
│
└── claude/             → 🗂️ Detailed guidance
    ├── state/          → 📍 Where we are right now
    ├── knowledge-base/ → 🧠 Lessons learned, tech decisions
    ├── rules/          → 🚧 Guardrails (security, git, testing)
    ├── workflows/      → 🔄 How to build features, ship code
    └── templates/      → 📝 Checklists and prompts
```

---

## 🚀 Quick Start

### Using Claude Code / Cursor

Claude Code looks for `CLAUDE.md` in your project root. Three ways to handle this:

**Option 1: Symlink it** (recommended)
```bash
ln -s .local/CLAUDE.md CLAUDE.md
echo "CLAUDE.md" >> .gitignore  # Keep it hidden
```

**Option 2: Just tell Claude**
```
Read .local/CLAUDE.md and .local/claude/state/current-state.md
```

**Option 3: Copy when needed**
```bash
cp .local/CLAUDE.md CLAUDE.md
# Delete before committing
```

### Using OpenClaw

Start your session with:
```
Read .local/OPENCLAW.md and follow it.
```

Or add this to your workspace `AGENTS.md`:
```markdown
## Project Work
For projects with `.local/`, read `.local/OPENCLAW.md` first.
```

---

## 📚 File Guide

| File | What it does | When to use it |
|------|--------------|----------------|
| `CLAUDE.md` | The prime directive. Workflow, rules, deliverable format. | Every session |
| `OPENCLAW.md` | Same energy, tuned for OpenClaw | OpenClaw sessions |
| `claude/state/current-state.md` | Where you left off, what's next | Every session |
| `claude/knowledge-base/lessons-learned.md` | Mistakes you don't want to repeat | Before similar work |
| `claude/rules/self-review.md` | Checklist before presenting code | Every code change |
| `claude/workflows/feature-development.md` | Full feature workflow | Building new stuff |

---

## 🔄 The Workflow (TL;DR)

Every task follows this loop:

```
UNDERSTAND → PLAN → IMPLEMENT → VERIFY → REPORT
```

1. **Understand**: Read the relevant files. Ask if unclear.
2. **Plan**: Break it into steps. Identify risks.
3. **Implement**: One step at a time. Run tests between steps.
4. **Verify**: Actually run the tests. Show the output.
5. **Report**: Summary, files changed, how to test.

Details in `claude/workflows/feature-development.md`.

---

## 💡 Pro Tips

### Keep State Updated
After meaningful progress:
```bash
echo "- Completed: auth flow" >> .local/claude/state/current-state.md
```

Your future self (and future AI sessions) will thank you.

### Learn From Mistakes
When something bites you, add it to:
```
.local/claude/knowledge-base/lessons-learned.md
```

### Evolve the Template
Learned something that applies to ALL projects?

```bash
cd ~/Code/tools/ai-dev-kit
git pull
# Update the relevant file in .local/
git add . && git commit -m "chore: learned something useful"
git push
```

Now every new project benefits. Compound improvements. 📈

---

## 🗺️ Directory Deep Dive

### `claude/state/`
**Your session memory.** Where you are, what you're working on, what's blocked.

- `current-state.md` — The one file to read every session

### `claude/knowledge-base/`
**Institutional memory.** Lessons learned, why you chose certain tech, patterns that work.

- `lessons-learned.md` — Don't repeat mistakes
- `tech-stack-decisions.md` — Why we chose X over Y
- `architecture-patterns.md` — Patterns that work here

### `claude/rules/`
**Guardrails.** Things that should always (or never) happen.

- `self-review.md` — Check your work before presenting
- `security.md` — Don't commit secrets, validate inputs
- `git.md` — Atomic commits, good messages
- `testing.md` — Test behavior, not implementation

### `claude/workflows/`
**Playbooks.** Step-by-step for common scenarios.

- `feature-development.md` — Build a feature end-to-end
- `quality-assurance.md` — Verify before shipping
- `github-preparation.md` — Ready for public/team review

### `claude/templates/`
**Checklists and scaffolds.** Copy-paste starting points.

- `pre-publish-checklist.md` — Before shipping
- `two-phase-prompt.md` — Spec → implement workflow

---

## 🔒 Privacy Model

| What | Visible to public? |
|------|-------------------|
| `.local/` directory | ❌ No (gitignored) |
| CLAUDE.md contents | ❌ No |
| Your AI workflow | ❌ No |
| `.gitignore` entry | ✅ Yes, but it just says `.local/` |

**Bottom line**: Nobody knows you're using AI assistance unless you tell them.

---

## 🆘 Troubleshooting

**Claude Code isn't reading my instructions**
→ Make sure `CLAUDE.md` exists in project root (symlink or copy)

**State file is stale**
→ Update `claude/state/current-state.md` at session end. Always.

**AI keeps making the same mistakes**
→ Add the pattern to `claude/knowledge-base/lessons-learned.md`

**Want to update guidance for all future projects**
→ Edit files in `~/Code/tools/ai-dev-kit/.local/`, commit, push

---

*This directory is your AI's brain. Treat it well.* 🧠
