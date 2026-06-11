# Legacy ingest and SQLite people — historical reference

**Status:** Archival only (June 2026). The modules and APIs described here were **removed** from the repo. Future ingestion, validation, and storage should be designed against `entities.json` and the entity protocol — **do not restore deleted files**.

---

## Timeline

| Era | What changed |
|-----|----------------|
| 2025-06 | Public ingest removed — query-only CLI/MCP; `EntityQuery.provided_data` dropped |
| 2025-06 | Graph simplified — `enrich` → `validator` loop removed; brief `core_data` specialist then eliminated |
| 2026-06 | Seed elimination — `agents.seed` removed; `import_seed_file` + `entities.json` canonical |
| 2026-06 | **This removal** — `enrich.py`, `validator.py`, `person_prep.py`, SQLite `people` API deleted |

---

## Old ingest graph (never public after June 2025)

1. Client sent `provided_data` on `EntityQuery` (or CLI `ingest`).
2. **enrich** — assigned stable `id`, normalized bind fields via `person_prep.ensure_id`.
3. **validator** — legacy ingest validator (not today's `validate_entity` MVR node).
4. **supervisor** — persisted and routed (ingest-only path).

No current CLI, MCP, or graph node invokes this flow.

---

## `core_data` agent

A short-lived specialist owned core CRM lookups between ingest removal and the seed-data-context redesign. Removed June 2026; **supervisor + entity registry** resolve identity and assemble direct responses.

---

## SQLite `people` vs `entities.json` vs `checkpoints.sqlite`

| Artifact | Role (historical → current) |
|----------|-------------------------------|
| `entities.json` | **Canonical** identity store (`EntityRegistry`, bind index) |
| `seed.json` | Optional bootstrap fixture; imported via `import_seed_file` only |
| `mycelium.db` | Was SQLite `people(id, name, employer)` mirror; **no identity tables now** — optional empty file for bootstrap compatibility |
| `checkpoints.sqlite` | LangGraph thread state (unchanged) |

Queries never read identity from SQLite after registry migration.

---

## `agents.seed` module

Runtime seed loader (`get_seed_data`, `find_by_key`, `mycelium seed` CLI) was removed in the entity seed-elimination phase. Replacement: `network.seed_import.import_seed_file` at refresh/create/bootstrap only.

---

## Revival note

Internal data addition (bulk ingest, alternative stores, enrichment pipelines) should be specified against:

- `EntityRegistry` / `entities.json`
- Entity protocol outcomes (`entity_unknown`, MVR, research gate)
- Negotiation/metering where applicable

Do **not** copy deleted `enrich.py`, `validator.py`, `person_prep.py`, or `seed_from_file` patterns back into `src/`.
