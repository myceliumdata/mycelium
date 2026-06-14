# Program 3 — Entity protocol legacy cleanup

**Status:** **Complete** — slices 1500–1560 queued in `prompts/cursor/` (June 2026); manual gate pending Paul  
**Prerequisite:** Program 2 manual gate **CLEAR** (2026-06-14) — tag `program_2`  
**Supersedes:** Prior “Program 3 = operator write” ordering — operator UI moves to **Program 4**

---

## Goal

One identity story everywhere public and on disk:

> Resolve by **`id`** or **`lookup` map keyed by `mvr.bind_fields`** — no parallel “bare name implies entity” or CRM-shaped registry columns.

Program 2 fixed bind **storage** (specialist `versions[]`). Program 3 removes legacy **protocol** and **schema** assumptions from the entity-registry era.

---

## Locked decisions (Paul + Grok, June 2026)

### D1 — Registry row shape: **Option A**

- `entities.json` entity rows use **`bind_values: dict[str, str]`** only (no top-level `name` / `employer` columns).
- **`bind_index`** compound key is **generic**: normalized values for every `mvr.bind_fields` entry, joined in policy order (CRM: `name|employer`).
- **Hard cutover** — refresh networks; no lazy migration on read.
- Query `results[]` may still expose flat `name` / `employer` for display — derived from `bind_values`, not a second canonical store.

### D2 — Status surfaces: **D2-b**

- **Input:** CLI/admin `--id` / `?id=` and `--lookup-json` / `?lookup=` only; remove `--entity` / `?entity=`.
- **Output:** mirror query step-1:

```json
{
  "resolve": { "id": null, "lookup": { "name": "…", "employer": "…" } },
  "resolve_matches": 1,
  "resolve_kind": "exact",
  "entity_fields": [ … ]
}
```

- Rename resolution fields: `entity_matches` → `resolve_matches`, `entity_resolution_kind` → `resolve_kind`, etc.
- **No** `entity_key` on status JSON.
- Inspect stays **exact AND** only — no fuzzy `lookup_suggested` on `GET /status`.

### Other locks

| Topic | Decision |
|-------|----------|
| **MVR helpers (item 5)** | Delete `required_bind_fields(entity_key, binding)`; `missing_mvr_bind_fields(lookup)` only |
| **Legacy graph** | Remove `EntityQuery.entity_key` / `binding`, `resolve_entity()`, `MYCELIUM_ALLOW_LEGACY_ENTITY_KEY` |
| **`lookup_by_name`** | Remove; use name field index internally |
| **`describe_network` policy** | Target protocol only on primary policy surface |
| **Operator write UI** | Program 4 |

---

## Slice map (Cursor queue)

| Order | Prompt | Scope |
|-------|--------|--------|
| 1 | `2026-06-14-1500-registry-generic-bind.md` | `bind_values`, generic `bind_index`, `attribute_write`, `seed_import`, `field_index` |
| 2 | `2026-06-14-1510-mvr-helper-legacy-removal.md` | Remove `required_bind_fields(entity_key,…)`, legacy `binding` on `MvrPolicy` |
| 3 | `2026-06-14-1520-status-surfaces-target.md` | CLI/admin status `id`/`lookup`; `resolve` JSON; admin-ui |
| 4 | `2026-06-14-1530-legacy-graph-removal.md` | Remove legacy resolution graph, models, responses, supervisor gate |
| 5 | `2026-06-14-1540-test-migration.md` | Migrate/delete legacy `entity_key` test corpus; drop conftest env flag |
| 6 | `2026-06-14-1550-policy-docs-hygiene.md` | `describe_network`, docs, manual gates, program complete |
| 7 | `2026-06-14-1560-program3-polish.md` | Review nits — see [`entity-protocol-legacy-cleanup-polish.md`](entity-protocol-legacy-cleanup-polish.md) |

Each slice: smoke tests + `./bin/ci-local`. Cursor does **not** edit `TODO.md`.

**Program final slice:** `1560` (polish) — Grok runs full integration (`pytest -m full`) at review.

---

## Explicit non-goals

- Operator edit / force re-research UI (Program 4)
- Fuzzy suggestions on `GET /status`
- Production network migration beyond documented refresh posture

---

*Updated: 2026-06-14 — D1 Option A + D2-b locked; slices queued.*