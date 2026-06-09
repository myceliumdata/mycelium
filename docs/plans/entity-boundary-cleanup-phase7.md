# Seed vs specialists boundary — Phase 7 spec

**Status:** Locked (Paul, June 2026)  
**Program:** [`entity-protocol-and-registry-program.md`](entity-protocol-and-registry-program.md)  
**Depends on:** Slices 4–6  
**Cursor prompt:** `prompts/cursor/next/2026-06-09-1600-entity-boundary-cleanup-phase7.md`

---

## Problem

`name` / `employer` live in seed, registry, and specialist `storage.json`. Specialists re-derive identity from `context.seed`. Paul wants registry as SoT for bind fields; specialists own **extended** attributes only.

---

## Objective

- Supervisor/registry: entity resolution + bind fields  
- Specialists: `current_id` + `target_fields` only for identity context  
- Stop writing `name` / `employer` into new specialist storage entries  
- Update Jinja factory template + `context.py` + `build_context`  
- **Delete** `src/agents/core_identity.py` and remove remaining imports/resets

**Non-goals:** Bulk migration of existing demo storage; delete `seed.json`.

---

## Context shape (locked)

`build_context` supplies specialists:

```python
{
  "entity_id": "<uuid>",
  "bind": { "name": "…", "employer": "…" },  # read-only from registry/seed resolution
  "storage": { ... extended attrs only ... }
}
```

Remove reliance on full `context.seed` blob.

**Clean slate (Paul Q7b):** update factory template **and** regen/update all committed reference specialists under `src/agents/specialists/` and per-network copies as needed.

---

## Specialist template changes

- Research prompts use `bind.name` / `bind.employer` for disambiguation only  
- Persisted `storage.json` schema: extended attrs only (no `name`/`employer` keys in new writes)  
- `storage_strategy.json` documents boundary

---

## Legacy cleanup (locked — Paul Q7c)

| Item | Action |
|------|--------|
| `src/agents/core_identity.py` | **Delete** |
| `src/agents/routing.py` | Remove `core_identity` imports/usages (legacy routing) |
| `tests/conftest.py` | Remove `reset_core_identity` from fixture resets |
| Other test imports of `core_identity` | Remove or stub as needed for tests that still exercise legacy routing |

**Legacy specialist storage (Paul Q7a):** ignore-on-read — no migration. Operator wipe / `refresh-example-network` for demos.

---

## Tests

- New specialist creation via factory → storage.json lacks name/employer  
- Query validated entity + email → research uses bind from context, not storage copy  
- No remaining runtime imports of `core_identity`

---

## Admin backlog

Add item #8: show registry vs specialist-owned fields separately in entity drill-down.

---

## Paul decisions (locked)

| # | Decision |
|---|----------|
| Q7a | Ignore legacy `name`/`employer` in specialist storage — clean slate |
| Q7b | Clean slate — factory template + reference specialists, not half-migrated legacy |
| Q7c | **Delete `core_identity.py`** in Slice 7 + clean `routing.py` / `tests/conftest.py` resets |