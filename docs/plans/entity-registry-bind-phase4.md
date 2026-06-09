# Entity registry + provisional bind — Phase 4 spec (draft)

**Status:** Locked (Paul, June 2026)  
**Program:** [`entity-protocol-and-registry-program.md`](entity-protocol-and-registry-program.md)  
**Depends on:** Slices 1–3  
**Cursor slice:** TBD after Paul approves batch 1

---

## Problem

Slice 3 asks for employer but cannot persist. Visiting agents need to supply binding fields and get a stable `id` for follow-up turns. Networks must grow beyond bootstrap seed.

---

## Objective

Introduce **`<network_root>/entities.json`**, provisional bind on complete MVR, unified resolution (registry → seed → suggest → unknown). **No validation loop yet** (Slice 5) and **no email research** until Slice 6 gate.

---

## `EntityQuery` extension (locked: `binding`)

```python
binding: dict[str, str] = Field(
    default_factory=dict,
    description=(
        "Optional MVR bind fields (e.g. employer). Name comes from entity_key "
        "when network mvr.name_source is entity_key. Used to bind unknown entities."
    ),
)
```

- Keys must be subset of MVR `bind_fields` excluding `name` when `name_source=entity_key`
- Values non-empty strings (strip whitespace)
- Invalid keys → ignore or 400-style error in message — **see open question**

---

## `entities.json` (locked path)

Runtime file under `network_root`, gitignored (like `categories.json`). Atomic save pattern from `classification/engine.py`.

```json
{
  "version": "1.0",
  "last_updated": "2026-06-08T12:00:00+00:00",
  "entities": {
    "550e8400-e29b-41d4-a716-446655440000": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Paul Murphy",
      "employer": "Acme Corp",
      "validation_state": "provisional",
      "field_states": {
        "name": "provisional",
        "employer": "provisional"
      },
      "source": "query_bind",
      "created_at": "2026-06-08T12:00:00+00:00"
    }
  },
  "bind_index": {
    "paul murphy|acme corp": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

| Field | Notes |
|-------|-------|
| `id` | **uuid4** on new bind (not seed uuid5) |
| `validation_state` | `provisional` until Slice 5 → `validated` |
| `source` | `query_bind` \| future: `import`, `seed_promote` |
| `bind_index` | Normalized `lower(name)|lower(employer)` → id |

**Env:** `MYCELIUM_ENTITIES_PATH` derived from `network_root/entities.json` via `runtime_path()` (add to `_RUNTIME_ENV_FIELDS`).

---

## Resolution order (unified `resolve_entity`)

```
1. Registry bind_index exact match (name from entity_key + binding.employer)
2. Registry by id (if entity_key is UUID and in entities)
3. Seed find_by_key (exact) — bootstrap, pre-validated for gating
4. Suggest (Slice 1)
5. entity_unknown / entity_under_specified / bind attempt
```

**Seed rows:** not mirrored into registry on load (locked). Seed match skips registry.

---

## Bind flow

**Trigger:** No exact seed/registry match, not `entity_key_unresolved`, MVR satisfiable from `entity_key` + `binding`.

| MVR state | Outcome |
|-----------|---------|
| `binding` complete (employer provided) | Create provisional entity → `entity_bound_provisional` |
| `binding` partial / empty | `entity_under_specified` + `required_fields` |
| `binding` absent | `entity_unknown` (Slice 3 behavior) |

**Duplicate bind key** (`paul murphy|acme corp` exists): idempotent return — outcome per **Q4e** (Paul pending).

**Same name, different employer:** new uuid4, new row (two Paul Murphys allowed).

---

## `entity_bound_provisional` response (locked)

```json
{
  "outcome": "entity_bound_provisional",
  "results": [
    {
      "id": "550e8400-…",
      "name": "Paul Murphy",
      "employer": "Acme Corp"
    }
  ],
  "required_fields": [],
  "message": "Bound provisional record for Paul Murphy at Acme Corp. Core validation and attribute research are not available until a later step.",
  "thread_id": "…"
}
```

Include **`id` + `name` + `employer` in `results`** — id is the precise handle for follow-ups across threads. No requested attributes researched in Slice 4.

---

## Re-query after bind (locked)

**Preferred:** `entity_key: "<uuid>"` — direct registry lookup; works across threads without repeating MVR.

**Also supported:** `entity_key: "Paul Murphy"` + `binding: {"employer": "Acme Corp"}` — bind_index lookup.

**Name-only `entity_key`:** when registry has **0 or 2+** rows for that name, require `binding.employer` or uuid (no guessing).

---

## Supervisor / graph

- Replace `resolve_entity_key` with `resolve_entity` (registry + seed + suggest)
- On `entity_bound_provisional`: set `current_id`, still **no specialists** (Slice 6 gate)
- On provisional bind in same request as `requested_attributes: [email]`: bind first, return provisional outcome **without** researching email

---

## Tests (smoke)

| Case | Expected |
|------|----------|
| Murphy + `binding.employer` | provisional row in `entities.json`, `entity_bound_provisional` |
| Repeat same bind | idempotent (same id) |
| Murphy @ Acme + Murphy @ Beta | two ids |
| Murphy bound + `email` | provisional outcome or bound identity only — **no Tavily** |
| Seed `Aaron Holiday` | still seed path, no registry write |

---

## Explicit non-goals

- Validation orchestration (Slice 5)
- Research gate enforcement beyond "no specialists on bind turn" (Slice 6)
- Seed-from-queries export
- Empty-seed `network create`

---

## Paul decisions (locked)

| # | Decision |
|---|----------|
| Q4a | **`results` includes `id`, `name`, `employer`** on bind — id preferred for follow-ups |
| Q4b | **Uuid `entity_key` preferred** for follow-ups; name + `binding` also supported |
| Q4c | Name-only key → require **`binding.employer` or uuid** when 0 or 2+ registry matches |
| Q4d | **Ignore unknown `binding` keys** — MVR fields only; reduces malicious/extra-key injection |
| Q4e | **Option A (locked):** duplicate bind → **`found`** with same `id`; message notes already bound; **no email** until Slice 6 |