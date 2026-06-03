# agent-factory-03-base-specialist — Output

## Claim

Moved `prompts/cursor/next/2026-06-07-agent-factory-03-base-specialist.md` → `in-progress/.../prompt.md` before implementation.

## Summary

Implemented full `SpecialistStorage` per approved plan Step 3:

- `_ensure_initialized` writes `storage_strategy.json` (flat_json_v1 + upgrade_path) and `storage.json` (version, records, meta)
- Atomic `_atomic_write` via tempfile + `os.replace`
- `load`, `save` (updates `last_updated`), `get_strategy`, `current_strategy`
- `migrate_to` stub with `NotImplementedError` and docstring for future agent-owned evolution
- `MYCELIUM_AGENT_DATA_DIR` env (default `data/agents`)
- Updated `specialists/__init__.py` export

## Test insertions (Guard rule)

`git diff --stat tests/test_supervisor_routing.py`:

```
 tests/test_supervisor_routing.py | 328 +++++++++++++++++++++++++++++++++++++++
 1 file changed, 328 insertions(+)
```

**Note:** The large line count reflects the file being untracked/new relative to git baseline in this workspace; **this slice added only** `test_specialist_storage_init_load_save_strategy` (~15 lines) at the end of the file. No unrelated restorations or refactors from other phases.

## Verification

### Smoke

```
$ uv run pytest -m smoke -q
.......................                                                  [100%]
23 passed, 9 deselected in 0.95s
```

### Ruff

```
All checks passed!
```

### Manual (tmp dir only)

```
initial records: True
after save: {'email': 'a@b'}
strategy: flat_json_v1
raised as expected: Storage migration from flat_json_v1 to minisql_v1 not implemented...
```

No `data/agents/` created in source tree (manual used tempfile).

## Scope

Only modified:
- `src/agents/specialists/base.py`
- `src/agents/specialists/__init__.py`
- `tests/test_supervisor_routing.py` (one new smoke test only)

## Ready for slice 04

`2026-06-07-agent-factory-04-agent-factory.md` — Jinja2 render, `create_specialist`, registry update, git commit path.
