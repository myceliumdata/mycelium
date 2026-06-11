# Phase 2 — legacy ingest and SQLite people removal

## Summary

Deleted unwired pre-registry ingest modules and the unused SQLite `people` identity API. `CoreStorage` is now a minimal DB-path bootstrap for MCP health checks. Added archival reference doc and smoke guards so the removed surface cannot creep back in.

## Changes

| Area | Change |
|------|--------|
| **Deleted** | `src/agents/enrich.py`, `validator.py`, `person_prep.py`, `tests/test_core_data_agent.py` |
| **`src/storage/core.py`** | Removed `people` DDL and identity CRUD; `get_storage(db_path=...)` only (no `seed_path` / `auto_seed`) |
| **Call sites** | `src/mycelium_mcp/server.py`, `src/mycelium_admin/server.py`, `src/storage/__init__.py` |
| **New** | `docs/legacy-ingest-and-storage-reference.md`, `tests/test_legacy_ingest_removed.py` |
| **Docs** | `docs/architecture.md`, `docs/full-code-walkthrough.md`, `docs/database-notes.md`, `docs/plans/README.md` |

**Unchanged (per scope):** `entity_validation.py`, graph `validation_passed` / `validation_errors`, `seed.json` / `import_seed_file`, network bootstrap.

## Verification

```bash
uv run ruff check src tests bin/                    # All checks passed
rg 'agents\.(enrich|validator|person_prep)|seed_from_file|find_persons|upsert_person|auto_seed' src/ tests/
# no matches in src/ (only symbol names in test_legacy_ingest_removed.py guards)
test ! -f src/agents/enrich.py                      # ok
LANGCHAIN_TRACING_V2=false uv run pytest -q         # 307 passed in 41.73s
```

## For Grok + Paul

- **Phase 2 legacy cleanup done** — unwired enrich/validator/person_prep removed; SQLite `people` identity layer removed from `CoreStorage`.
- **Historical-assumptions audit exit criteria (P5/P6):** legacy ingest modules and duplicate SQLite identity storage are gone; canonical identity is `entities.json` via registry/bootstrap; archival context lives in `docs/legacy-ingest-and-storage-reference.md` (do not restore deleted files).
- **Not committed** — awaiting review. May be combined with staged CI framework-specialists slice from prior prompt.
- Suggested commit message in `prompt.md`.
