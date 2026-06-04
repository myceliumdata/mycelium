# reset-mycelium — delivery

## Deliverable

- **`bin/reset-mycelium`** — Python dev/ops script (replaces prior bash implementation)
- Shebang: `#!/usr/bin/env python` (run with venv on PATH, or `uv run python bin/reset-mycelium`)
- Scope: **only** this file edited for the slice

## Verification (2026-06-03)

### 1. chmod +x

```bash
chmod +x bin/reset-mycelium
```

### 2. --help

```
usage: bin/reset-mycelium [-h] [-b] [-c] [-s] [--specialist NAME] [-a] [-n]
                          [-y] [--no-git]

Reset Mycelium dev data on canonical source paths only (ignores MYCELIUM_* env redirection). Keeps agent_registry.json in sync when removing generated specialists.

options:
  -h, --help         show this help message and exit
  -b, --base         Reset data/mycelium.db
  -c, --categories   Reset data/categories.json
  -s, --specialists  Remove all generated specialists
  --specialist NAME  Remove specific specialist(s); repeat or use comma-separated list
  -a, --all          Equivalent to --base --categories --specialists
  -n, --dry-run      Print plan only; no filesystem or git changes
  -y, --yes          Skip confirmation
  --no-git           Filesystem only; skip git rm / git add

Examples:
  bin/reset-mycelium --dry-run --all
  bin/reset-mycelium --specialist financial_specialist
  bin/reset-mycelium --specialists --yes
  bin/reset-mycelium --base --categories
  bin/reset-mycelium --specialist demographic_specialist,financial_specialist --no-git
```

Invocation note: `./bin/reset-mycelium` requires `python` on PATH (e.g. `PATH=".venv/bin:$PATH"`). `uv run python bin/reset-mycelium` always works.

### 3. Dry-run — one specialist

```
=== reset-mycelium ===
  specific:    demographic_specialist
  dry-run:     True
...
registry entry removed: demographic_specialist
  (would clean data dir) .../data/agents/demographic
  (would clean specialist py) .../demographic_specialist.py
Dry-run only — no changes were made.
```

### 4. Dry-run — all

Plans base unlink, categories unlink, both specialists + data dirs. No writes.

### 5. Surgical `--specialist demographic_specialist --yes --no-git`

- `ls src/agents/specialists/*_specialist.py` → only `financial_specialist.py`
- Registry: `core_data` + `financial_specialist`
- `data/agents/` → only `financial/`
- `git status --short` → `M data/agent_registry.json`, `D` demographic paths/py

### 6. Restore

`git checkout -- data/agent_registry.json src/agents/specialists/demographic_specialist.py data/agents/demographic/`

### 7. `--all --yes --no-git`

- Zero `*_specialist.py`
- Registry: only `core_data`
- `data/agents/` empty
- DB/categories re-seeded via `reset_storage`/`get_storage`, `reset_category_tree`/`get_category_tree`

### 8. Restore

`git checkout --` on registry, categories, specialist py files, agent data dirs.

### 9. `--base --categories --yes --no-git`

DB and `data/categories.json` recreated; specialists untouched.

### 10. git diff --stat (slice scope)

This slice **only adds** `bin/reset-mycelium` (untracked). The working tree has other pre-existing WIP from Agent Factory / classification work; those are **not** part of this deliverable.

```bash
git status --short bin/reset-mycelium
# ?? bin/reset-mycelium
```

## Behavior summary

| Flag | Effect |
|------|--------|
| `--base` | Unlink `data/mycelium.db`, reseed via storage singletons |
| `--categories` | Unlink `data/categories.json`, reseed embedded tree |
| `--specialists` / `--specialist` | Prune registry (Pydantic), remove py + `data/agents/<cat>/`, optional `git rm`/`git add` |
| `--all` | All three |
| `--dry-run` | Plan only |
| `--no-git` | FS only; prints skipped git commands |
| `--yes` | Skip confirmation |

Always uses canonical paths; ignores `MYCELIUM_*`. Ends with `reset_agent_registry`, `reset_agent_factory`, `reset_category_tree`, `reset_storage`.
