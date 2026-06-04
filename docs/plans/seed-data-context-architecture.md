# Plan: Evolving Mycelium to Seed Data + Supervisor-Provided Context Model

**Implemented:** June 2026 via Cursor slices `2026-06-09-1500` (seed loader) through `1600` (integration). See `prompts/cursor/done/2026-06-09-*-reprocess/` and `docs/architecture.md` for the live system description.

## Context & Motivation

The supervisor treats committed `data/seed.json` as read-only origin data, assigns stable `person_id` values at load time, builds a union of seed + specialist storage for each query, and invokes all required generated specialists sequentially. Specialist-owned data overrides seed on conflicts. There is no privileged core specialist.

## Target slices (completed)

| Slice | Focus |
|-------|--------|
| 1500 | `data/seed.json` + `agents/seed.py` |
| 1510 | `matched_persons`, `context`, `current_person_id`, `target_fields` on graph state |
| 1520 | Unified `PersonResponse` builders (no "core record" language) |
| 1530 | Remove `core_data` agent and registry entry |
| 1540 | Specialist Jinja template (3 scenarios, `specialist_contrib`) |
| 1550 | `context.py` + graph nodes `build_context` / `invoke_specialists` / `assemble_response` |
| 1600 | Integration: reset tool, docs, re-gen six specialists |

## Deferred (post-1600)

- Expose `person_id` in public `results` (slice 1700) — **done**
- Eliminate `CORE_PERSON_FIELDS` / `non_core_attributes` (slice 1710) — **done**
- Eliminate legacy `id` from seed transform; public `results["id"]` = UUID (slice 1720) — **done**
- Eliminate core vs non-core attribute split in assembly (1710)
- Seed transform without legacy `id` field (1720)
- Robust pending/research threads; peer context retrieval; real LLM+tools research
