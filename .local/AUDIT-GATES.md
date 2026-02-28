# AUDIT-GATES.md — Powerflow
# Living registry of verifiable invariants. One gate per major design decision.
# Format: run the command → if output is non-empty, the gate FAILS.
# Rule: add a gate in the same commit as the feature that introduces the invariant.

## How to run all gates
```bash
bash ~/Dropbox/.nimbus-shared/scripts/audit-gates-check.sh ~/Code/powerflow
```

---

## D-PF-001 — Only SyncEngine writes to Notion
**Invariant:** `create_page` must only be called from `sync.py` (SyncEngine). No other module may write directly to Notion — prevents dedup bypass.
**Command:**
```bash
grep -rn "\.create_page(" src/powerflow/ --include="*.py" | grep -v "sync\.py\|notion\.py"
```
**Pass:** zero lines

---

## D-PF-002 — Every Notion write is guarded by dry_run
**Invariant:** All `create_page` calls in `sync.py` must be inside an `if not dry_run:` block to ensure dry-run mode never writes.
**Command:**
```bash
python3 -c "
lines = open('src/powerflow/sync.py').read().split('\n')
for i, line in enumerate(lines):
    if '.create_page(' in line and 'def create_page' not in line:
        context = '\n'.join(lines[max(0,i-15):i])
        if 'if not dry_run' not in context:
            print(f'Line {i+1}: create_page without dry_run guard: {line.strip()}')
"
```
**Pass:** zero output

---

## D-PF-003 — No hardcoded API key values in source
**Invariant:** No literal Pocket (`pk_`) or Notion (`ntn_`) key values may appear in `.py` files. Keys must come from environment variables only.
**Command:**
```bash
grep -rn 'pk_[a-f0-9A-F]\{40,\}\|ntn_[a-zA-Z0-9]\{40,\}' src/ --include="*.py"
```
**Pass:** zero lines

---

## D-PF-004 — AI summary completeness check required before every Notion write
**Invariant:** In `sync.py`, every `create_page` call must be preceded by an `is_summary_complete` check. Prevents syncing half-processed recordings.
**Command:**
```bash
python3 -c "
lines = open('src/powerflow/sync.py').read().split('\n')
for i, line in enumerate(lines):
    if '.create_page(' in line and 'def create_page' not in line:
        context = '\n'.join(lines[max(0,i-25):i])
        if 'is_summary_complete' not in context:
            print(f'Line {i+1}: create_page without is_summary_complete guard')
"
```
**Pass:** zero output

---

## D-PF-005 — update_last_sync only called when not dry_run
**Invariant:** `update_last_sync()` in `sync.py` must always be inside an `if not dry_run:` guard. Prevents timestamp corruption on dry runs.
**Command:**
```bash
python3 -c "
lines = open('src/powerflow/sync.py').read().split('\n')
for i, line in enumerate(lines):
    if 'update_last_sync()' in line:
        context = '\n'.join(lines[max(0,i-5):i])
        if 'not dry_run' not in context:
            print(f'Line {i+1}: update_last_sync without dry_run guard: {line.strip()}')
"
```
**Pass:** zero output

---

## D-PF-006 — Dedup check must precede every create_page in sync flow
**Invariant:** `batch_check_existing_pocket_ids` must be called before `create_page` in `sync.py`. Removing dedup silently causes duplicate Notion pages.
**Command:**
```bash
python3 -c "
content = open('src/powerflow/sync.py').read()
lines = content.split('\n')
create_lines = [i for i,l in enumerate(lines) if '.create_page(' in l and 'def create_page' not in l]
dedup_lines  = [i for i,l in enumerate(lines) if 'batch_check_existing_pocket_ids' in l]
for cl in create_lines:
    if not any(dl < cl for dl in dedup_lines):
        print(f'Line {cl+1}: create_page with no prior batch_check_existing_pocket_ids')
"
```
**Pass:** zero output
