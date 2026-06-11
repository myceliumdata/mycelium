# Task: Phase 2 — remove legacy ingest modules and SQLite people layer

> **READY** — Paul signed off June 2026: delete legacy code; archival doc only (no code preservation). Move to `in-progress/` before starting.

**Read first:**

- [`docs/plans/legacy-ingest-storage-removal.md`](../../docs/plans/legacy-ingest-storage-removal.md)
- [`docs/architecture.md`](../../docs/architecture.md)
- [`docs/plans/historical-assumptions-audit.md`](../../docs/plans/historical-assumptions-audit.md) §7 P5/P6

**Depends on:** `main` green at `fd02271` or later.

---

## Objective

Delete unwired pre–registry ingest code and the unused SQLite `people` identity API. Replace with a **short historical reference doc** for future first-principles redesign of ingestion and storage — not revived code.

---

## 1. Delete modules

Remove entirely:

- `src/agents/enrich.py`
- `src/agents/validator.py`
- `src/agents/person_prep.py`
- `tests/test_core_data_agent.py`

Confirm no remaining imports in `src/` or `tests/` (grep).

---

## 2. Slim `storage/core.py`

Remove SQLite **people** identity layer (see plan). **Do not** remove `validate_entity` or graph `validation_passed` fields.

After change:

- `get_storage()` still callable for MCP `health_check` / bootstrap
- Drop `seed_path` and `auto_seed` parameters
- No `people` table DDL; no identity CRUD methods
- Minimal behavior: resolve `MYCELIUM_DB_PATH`, ensure parent dir (and file if needed) — **no seed import**

Update call sites:

- `src/main.py`
- `src/mycelium_mcp/server.py`
- `src/mycelium_admin/server.py`

Update `src/storage/__init__.py` exports if API changes.

---

## 3. Archival doc

Create **`docs/legacy-ingest-and-storage-reference.md`** per plan (max ~2 pages):

- Old enrich → validator ingest path
- Removed `core_data` agent
- SQLite `people` vs `entities.json` vs `checkpoints.sqlite`
- Removed `agents.seed` (point to seed elimination)
- Explicit: future work designs from registry; do not restore deleted files

Add one-line links from:

- `docs/architecture.md`
- `docs/plans/README.md` (active backlogs or “Historical reference” row)

---

## 4. Living doc trim

Update:

- `docs/full-code-walkthrough.md` — remove “legacy on disk” bullets for deleted modules
- `docs/database-notes.md` — reflect no `people` table; checkpoints unchanged

---

## 5. Tests

- Fix any broken fixtures after `CoreStorage` API change (many tests use `CoreStorage` only as env/bootstrap type)
- Optional smoke: `test_no_legacy_ingest_imports` — grep-level or importlib guard
- Full suite must pass

---

## Out of scope

- `entity_validation.py` / `validate_entity` node
- `validation_passed` / `validation_errors` on `MyceliumGraphState`
- `seed.json`, `import_seed_file`, network bootstrap
- `TODO.md`
- Historical `docs/plans/*` slice specs (except README link)
- `prompts/resets/*`, `prompts/cursor/done/*`

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- **Do not create `review.md`.**
- In `output.md`, add **"For Grok + Paul"**: mark Phase 2 legacy cleanup done; historical-assumptions audit exit criteria.
- **Do not commit** before Grok + Paul review.

---

## Verify

```bash
uv run ruff check src tests bin/
rg 'agents\.(enrich|validator|person_prep)|from agents\.person_prep|seed_from_file|find_persons|upsert_person|auto_seed' src/ tests/
test ! -f src/agents/enrich.py
LANGCHAIN_TRACING_V2=false uv run pytest -q
```

Report pytest count in `output.md`.

---

## Suggested commit message

```
Remove legacy ingest modules and SQLite people identity layer.

Delete unwired enrich/validator/person_prep; slim CoreStorage;
add docs/legacy-ingest-and-storage-reference.md for future redesign.
```