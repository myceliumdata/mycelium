# Legacy ingest & SQLite people removal (Phase 2)

**Status:** Queued for Cursor (June 2026)  
**Decision (Paul):** Delete unwired legacy code from the repo. Do **not** preserve implementation for reuse — future ingestion, validation, and alternative storage will be designed from first principles. Keep one **short archival doc** describing how the old paths worked.

---

## Goal

Remove dead pre–registry-era modules and the unused SQLite `people` table API. Runtime truth stays: **`entities.json`** + **`validate_entity`** graph node + optional **`seed.json`** bootstrap import.

---

## Delete from codebase

| Path | Why |
|------|-----|
| `src/agents/enrich.py` | Unwired; references removed `person` / `provided_data` |
| `src/agents/validator.py` | Unwired legacy ingest validator (not `validate_entity`) |
| `src/agents/person_prep.py` | Only used by `enrich.py` |
| `tests/test_core_data_agent.py` | Skip-only placeholder for removed `core_data` agent |

### Slim `src/storage/core.py`

Remove SQLite **people** identity layer:

- `people` table schema and indexes
- `seed_from_file`, `upsert_person`, `get_person_by_id`, `find_persons`, `_row_to_person`
- `auto_seed` / `seed_path` on `get_storage()`

**Keep** a minimal `get_storage()` / `CoreStorage` (or equivalent) so MCP `health_check` and bootstrap paths still succeed — e.g. ensure `MYCELIUM_DB_PATH` parent exists and optionally open an empty SQLite file **without** a `people` table. No identity reads/writes.

Update callers: `main.py`, `mycelium_mcp/server.py`, `mycelium_admin/server.py` — drop `seed_path=` kwargs.

---

## Do NOT remove (active graph)

| Symbol | Role |
|--------|------|
| `validate_entity` / `entity_validation.py` | Registry MVR validation (Slice 5) |
| `validation_passed`, `validation_errors`, `validation_contributions` on `MyceliumGraphState` | Used by dispatch, research gate, metering |
| `import_seed_file`, `seed.json`, `--seed` | Bootstrap fixture only |
| `entities.json` / entity registry | Canonical identity |

---

## Archival doc (create)

**New file:** `docs/legacy-ingest-and-storage-reference.md` (~1–2 pages max)

Sections:

1. **Timeline** — query-only migration (2025-06) → seed elimination (2026-06) → this removal
2. **Old ingest graph** — `provided_data` → enrich → validator → supervisor (never public CLI/MCP)
3. **`core_data` agent** — removed 2026-06; supervisor + registry replaced it
4. **SQLite `people` table** — was identity mirror; queries moved to `entities.json`; `mycelium.db` ≠ `checkpoints.sqlite`
5. **`agents.seed` module** — removed in seed elimination; replaced by `import_seed_file` + registry
6. **Revival note** — future internal data addition should design against registry + negotiation; **do not revive deleted modules**

Link from `docs/architecture.md` (one line under a “Historical reference” or footnote) and `docs/plans/README.md` active backlogs.

---

## Living doc updates

| Doc | Change |
|-----|--------|
| `docs/architecture.md` | Remove “legacy enrich/validator/person_prep on disk”; link archival doc |
| `docs/full-code-walkthrough.md` | Remove legacy-on-disk bullet |
| `docs/database-notes.md` | Rewrite: checkpoints canonical; `mycelium.db` no longer has `people` (or file optional/empty) |

**Out of scope:** `docs/plans/*` historical slice specs, `prompts/cursor/done/*`, `prompts/resets/*`.

---

## Tests

- Remove `test_core_data_agent.py`
- Entity test fixtures may keep `CoreStorage` type hints — update if class API changes
- Full smoke + full suite green
- Add smoke grep guard: no imports of `agents.enrich`, `agents.validator`, `agents.person_prep`

---

## Verify

```bash
uv run ruff check src tests
rg 'agents\.(enrich|validator|person_prep)|seed_from_file|find_persons|upsert_person|auto_seed' src/ tests/
LANGCHAIN_TRACING_V2=false uv run pytest -q
```