# Program 3 — Entity protocol legacy cleanup (draft)

**Status:** Draft — **next program** after Program 2 ships (Paul, June 2026)  
**Prerequisite:** Program 2 manual gate clear + push  
**Supersedes:** Prior “Program 3 = operator write” ordering — operator UI moves to **Program 4**

---

## Why

Program 2 unified MVR bind **storage** (specialist `versions[]`, taxonomy ownership), but several **resolution and operator surfaces** still treat `name` (and CRM-shaped `employer` / `bind_index`) as special. That confuses newcomers:

- `mycelium query` uses explicit `lookup` JSON (MVR-correct)
- `mycelium network status --entity "…"` treats a bare string as **display name** (legacy convenience)
- Registry row still caches `name` / `employer` columns; extra `mvr.bind_fields` are not generic on the entity row
- Internal helpers (`lookup_by_name`, `entity_key`, `resolve_entity_for_lookup`) predate the target two-step protocol

**Goal:** One coherent story — **identity resolution = `id` or `lookup` map keyed by `mvr.bind_fields`** everywhere public; no parallel “name is implied” paths.

---

## Legacy backlog (to lock in planning)

| Area | Today | Target direction |
|------|--------|------------------|
| **CLI `network status`** | `--entity KEY` → name or UUID | `--lookup-json` and/or `--id` (same vocabulary as `query`); drop bare-string “entity” |
| **Registry resolution** | `lookup_by_name()`, `entity_key` paths | MVR field indexes only; UUID for id |
| **Entity row cache** | `name`, `employer` columns + `bind_index(name, employer)` | Generic bind-field cache aligned with `mvr.bind_fields` (schema + indexes) |
| **MVR helpers** | `required_bind_fields` assumes `entity_key` satisfies `name` | Remove legacy `entity_key` satisfaction rules |
| **Admin / introspection** | `resolve_entity_for_lookup(entity_key)` | Explicit lookup map or id |
| **Docs / help text** | Mixed “entity”, “entity_key”, “name” | Target protocol vocabulary only |
| **Internal gates** | `MYCELIUM_ALLOW_LEGACY_ENTITY_KEY`, suppressed CLI flags | Remove or hard-fail everywhere |
| **Operator write UI** | Was “Program 3” | **Program 4** — after protocol is legible |

---

## Explicit non-goals (until locked)

- Slice breakdown and Cursor prompts (planning session with Paul + Grok)
- Operator edit / force re-research UI (Program 4)
- Migration of production networks beyond documented refresh posture (unless Paul asks)

---

## Next steps (after Program 2 gate)

1. Paul finishes [`2026-06-13-program2-post-program-gate.md`](../manual-checks/2026-06-13-program2-post-program-gate.md).
2. Grok + Paul lock Program 3 scope and slices (likely: CLI/status → registry schema/indexes → admin → docs/hygiene).
3. Bump `TODO.md` when ready (Grok + Paul only).

---

*Created: 2026-06-14 — Paul: legacy cleanup is next program; operator write deferred.*