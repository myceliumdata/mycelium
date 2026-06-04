# reset-mycelium-cleanup — delivery

## Changes (bin/reset-mycelium only)

1. **Dead code removed** — unreachable `if dry_run` inside the registry `git add` block.
2. **Plan header** — `specialists:` line only when `--specialists` or `--all`; `--specialist` alone shows only `specific:`.
3. **Smarter git add** — `_prune_registry` returns `registry_changed`; registry file is written and `git add` runs only when at least one agent was actually removed from the registry.

## Verification

### Dry-run header (no `specialists: False`)

```
=== reset-mycelium ===
  base:        False
  categories:  False
  specific:    demographic_specialist
  dry-run:     True
  git:         enabled
```

### Dry-run --all

```
  specialists: True
```

### Edge case: nonexistent specialist

```
  specific:    nonexistent_specialist
```

No `registry written`, no `M data/agent_registry.json` in `git status --short -- data/agent_registry.json`.

### Full `--all --no-git`

Registry only `core_data`; zero `*_specialist.py` files.

## Scope

Only `bin/reset-mycelium` edited. File remains untracked (`??`); `git diff --stat bin/reset-mycelium` empty until first add/commit.
