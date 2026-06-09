# Seed vs specialists boundary — Phase 7 spec (draft)

**Status:** Draft for Paul review (batch 2: slices 5–7)  
**Depends on:** Slices 4–6

---

## Problem

`name` / `employer` live in seed, registry, and specialist `storage.json`. Specialists re-derive identity from `context.seed`. Paul wants registry as SoT for bind fields; specialists own **extended** attributes only.

---

## Objective

- Supervisor/registry: entity resolution + bind fields  
- Specialists: `current_id` + `target_fields` only for identity context  
- Stop writing `name` / `employer` into new specialist storage entries  
- Update Jinja factory template + `context.py` + `build_context`

**Non-goals:** Bulk migration of existing demo storage; delete `seed.json`.

---

## Context shape (proposal)

`build_context` supplies specialists:

```python
{
  "entity_id": "<uuid>",
  "bind": { "name": "…", "employer": "…" },  # read-only from registry/seed resolution
  "storage": { ... extended attrs only ... }
}
```

Remove reliance on full `context.seed` blob in generated specialists (reference modules in `src/agents/specialists/` may stay until regen).

---

## Specialist template changes

- Research prompts use `bind.name` / `bind.employer` for disambiguation only  
- Persisted `storage.json` schema: extended attrs only (no `name`/`employer` keys in new writes)  
- `storage_strategy.json` documents boundary

---

## Existing networks

**Proposal:** Best-effort read: if legacy storage contains `name`/`employer`, ignore for merge; registry/seed wins. No automatic file rewrite.

*Paul: OK to leave legacy keys in old storage.json, or run one-time strip on read?*

---

## Tests

- New specialist creation via factory → storage.json lacks name/employer  
- Query validated entity + email → research uses bind from context, not storage copy

---

## Admin backlog

Add item #8: show registry vs specialist-owned fields separately in entity drill-down.

---

## Open questions for Paul

1. **Legacy storage:** ignore-on-read (proposal) vs migrate-on-read?

2. **Regen committed reference specialists** (`src/agents/specialists/*`) in this slice or only factory template for new/generated modules?

3. **`core_identity.py`:** delete, or leave unwired with comment?