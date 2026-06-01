# Output: Redesign ingestion handshake

## Prior behavior (documented)

After task 1912, the supervisor stubbed all ingestion:
- Any `provided_data` or `validation_passed` → `"Ingestion flow is not yet implemented."`
- Missing person queries → same stub text
- Enrich/validator nodes existed but were unreachable from ingest requests

## Design (chosen)

**Single-step ingest** via existing `PersonQuery.provided_data` (no `DataRequest` model, no two-phase state machine).

| Caller intent | Mechanism | Response |
|---------------|-----------|----------|
| Lookup | `person_key` only | `results` + found / researching messages |
| Person missing | `person_key` only | Empty `results`; `message` explains `provided_data` + CLI/MCP paths |
| Add person | `provided_data` with `name` + `employer` | Graph: supervisor → enrich (prepare) → validator → supervisor (persist + respond) |

**Success:** `results=[core dict]`, `message="Added core record for {name}."`, `debug` with `outcome=ingested`.

**Failure:** `results=[]`, `message="Could not add core record: …"`, `debug` with `outcome=ingest_failed`.

**Persist only after validation:** Enrich prepares the record; supervisor calls `upsert_person` only when `validation_passed` is true (fixes pre-validation writes).

## Files modified

| File | Change |
|------|--------|
| `src/agents/supervisor.py` | Restored ingest routing; guidance + success/failure responses |
| `src/agents/enrich.py` | Prepare only; no storage write |
| `src/mcp/server.py` | Instructions/docstring for working ingest |
| `docs/architecture.md` | "Core Ingestion Handshake" section |
| `tests/test_core_graph.py` | Ingest success + validation failure tests |
| `TODO.md` | Marked complete; updated follow-ups |

## Verification

- `uv run pytest` — **6 passed**
- `uv run ruff check src tests` — clean

## Follow-ups (in TODO.md)

- Stronger validation rules
- Whether ingest should trigger specialist work
- Machine-readable error categories
- Dead-code cleanup (`2026-06-02-1010` queued)

## In-progress cleanup

Removed only `prompts/cursor/in-progress/2026-06-02-1000-redesign-ingestion-handshake.md`.
