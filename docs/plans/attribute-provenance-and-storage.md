# Attribute provenance, storage, and entity model — architecture

**Status:** Architecture doc (June 2026) — **Program 1 complete**; **Program 2 locked** — [`attribute-provenance-program2.md`](attribute-provenance-program2.md)  
**Program 1:** [`attribute-provenance-program1.md`](attribute-provenance-program1.md) — **shipped**
**Depends on:** Entity protocol Slices 1–8, seed elimination, Slice 8 attribution  
**Blocks:** Operator attribute correction (after Program 2), full unified write API  
**Related:** `TODO.md` — Program 1 queue, Program 2 MVR/entity

---

## Problem

Extended attributes and MVR bind fields (`name`, `employer`, …) use versioned specialist storage (Programs 1–2). Registry rows cache current MVR values and hold protocol metadata; canonical bind-field history lives in taxonomy-owned specialist `versions[]`. Bind resolution uses `bind_index` plus per-field indexes (MVR redesign). Operator corrections use unified write (Program 2); operator edit UI is Program 3.

Paul Murphy LinkedIn (wrong post URL) is the motivating case: we need an audit trail of *what was stored, when, by whom, from which sources* — including `na` / `pending` states for debugging.

---

## Locked decisions (Paul, June 2026)

| # | Decision |
|---|----------|
| P1 | **Version history** per attribute: append-only `versions[]`; unlimited retention for now |
| P2 | **v1 timestamps:** one `at` per version; no per-source `retrieved_at` until the research layer captures it |
| P3 | **Version all statuses:** `found`, `na`, `pending`, operator edits — not only successful `found` |
| P4 | **Registry summary only:** keep `attr_sources` + `last_researched_at` as pointers; no full citation lists on `entities.json`. `last_researched_at` = current version `at` (last attempt, any status) |
| P5 | **Bind corrections:** append version in **specialist storage**; update cached `employer` / `name` on entity row (no `bind_versions[]` on entity row — locked June 2026) |
| P6 | **Bind key change policy:** **replace** — update canonical value + `bind_index`; **do not** retain old bind-key aliases |
| P7 | **Denormalized MVR cache:** keep current `name` / `employer` on the entity row for fast reads; not source of truth |
| P8 | **Canonical values:** specialist-owned (or unified attribute store) with `versions[]`; entity row holds protocol + indexes + cache |
| P9 | **Indexes:** `bind_index` (and optionally `name_index`) on `entities.json`; updated atomically on every canonical write |
| P10 | **Specialist-owned indices:** valid future direction; **deferred** — see `TODO.md` |

---

## Three-layer model

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Canonical attribute values (versioned, source of truth)   │
│    name, employer, linkedin, email, …                       │
│    → specialist storage (per category) OR unified attr doc  │
│    → each field: versions[] + denormalized current view     │
└─────────────────────────────────────────────────────────────┘
                              │ single write API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Search indexes (derived, O(1) bind resolution)           │
│    bind_index:  normalized(name)|normalized(employer) → id  │
│    name_index:  normalized(name) → [ids]  (optional)        │
│    → lives on entities.json; no scanning specialist files   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Entity protocol record (small, graph/admin metadata)     │
│    id, validation_state, field_states, source, created_at   │
│    attr_sources, last_researched_at (summary pointers)        │
│    cached name / employer (denormalized current)            │
└─────────────────────────────────────────────────────────────┘
```

**Protocol metadata** drives the query state machine (`entity_unknown` → bind → `entity_validated` → research gate). It is not a person fact. **`validation_state`** means “has this network accepted the bind as well-formed enough to research extended attrs?” — not “is this person valid in the real world.”

**Attribute values** are facts with versioned provenance. MVR fields (`name`, `employer`) follow the same rules as extended attrs once handed to specialists.

---

## Extended attribute shape (specialist storage)

Replace flat overwrite with versioned field:

```json
"linkedin": {
  "current_version_id": "v3",
  "versions": [
    {
      "id": "v1",
      "at": "2026-06-11T05:26:46.061007+00:00",
      "status": "found",
      "value": "https://www.linkedin.com/posts/ormilabs_...",
      "confidence": 0.775,
      "sources": [
        { "url": "https://www.linkedin.com/posts/ormilabs_..." }
      ],
      "actor": {
        "kind": "research",
        "category": "social",
        "specialist": "social_specialist"
      }
    }
  ]
}
```

**Hot path:** specialists and merge logic read denormalized **current** (latest version or explicit `current_version_id`). **Audit path:** admin and `provenance=true` expose `versions[]`.

**Pending retries (Program 1, P1-11):** update the current `pending` version in place (same id; refresh `at` / `last_error`; keep `started_at`). Append a new version only when status changes. See program spec for the full transition table.

**Actor kinds (v1):** `research`, `operator`, `bind` (query-time provisional bind), `seed_bootstrap`. Extend later for external agents.

**`at` vs `retrieved_at` (deferred):** `at` = when this version was recorded. Per-source `retrieved_at` = when a URL was fetched in the tool loop; add when `research.py` logs per-hit times. Until then, sources are `{ "url": "..." }` only.

Category-level `meta.research_audit` may remain as a coarse pass log; field `versions[]` is the product-facing audit trail.

---

## Bind / MVR attribute shape (specialist storage)

**Canonical history** for bind fields lives in taxonomy-owned specialist `storage.json` (`versions[]`), same as extended attrs. The entity row holds **cached** `name` / `employer` only.

**Bind key correction (replace policy):**

1. Append new version in owning specialist storage (`employer.versions[]`, etc.).
2. Update cached value on entity row.
3. **Replace** `bind_index` and per-field indexes: remove old normalized keys, add new → same `id`.
4. Do **not** keep old bind key as alias.

Duplicate-bind collision (two entities, same new key) is a separate UX/policy problem; v1 fails loud or surfaces operator disambiguation.

---

## MVR values and specialists

MVR fields can be **specialist-owned** like any other attribute:

| MVR field | Owning specialist (CRM) | Resolution |
|-----------|-------------------------|------------|
| `name` | `demographic_specialist` | `attribute_map["name"]` → category → agent |
| `employer` | `professional_specialist` | `attribute_map["employer"]` → category → agent |

**v1:** keep inline rule checks in `validate_entity`; specialists store values + versions when written via unified write API. **Later:** optional full specialist invoke for MVR validation.

`validation_state` / `field_states` remain on the entity protocol record regardless of where values live.

---

## Write path (required discipline)

All attribute and bind writes go through **one framework API** (`attribute_write.py`) that:

1. Dispatches to the owning specialist (`agents.specialists.protocol`) to append versions in **specialist-owned** storage.
2. Updates denormalized cache on entity row (MVR fields) from dispatch return values.
3. Updates `bind_index` when bind fields change.
4. Updates registry summary (`attr_sources`, `last_researched_at`) for extended attrs.
5. Persists registry with `EntityRegistry._save`.

Framework code outside `src/agents/specialists/` must not call `SpecialistStorage` directly (tag `specialist_isolation`, June 2026). Direct JSON edits bypassing this path are unsupported for operators once write UI ships.

---

## Read surfaces

| Surface | v1 behavior |
|---------|-------------|
| **Default CLI/MCP query** | Unchanged flat `results` (`id`, attr values as strings) |
| **`provenance=true`** | Add structured attribution block (extended + MVR bind fields with versioned specialist storage); flat keys retained |
| **Admin entity drill-down** | Current value + expandable version timeline per field (extended + bind) |
| **`describe_network`** | Document version schema and actor kinds |

---

## Implementation phases (by program)

See [`attribute-provenance-program1.md`](attribute-provenance-program1.md) for Program 1 slices 1–3.

Program 2 Slice 1 (shipped): MVR canonical values in taxonomy-owned specialist `versions[]`; entity row = cache + protocol + indexes (no `bind_versions[]`). **June 2026 refactor:** writes/reads cross the specialist boundary via `protocol` + normalized snapshots (`docs/architecture.md` § Specialist I/O protocol). Slice 2 (shipped): `provenance=true` and admin drill-down expose bind-field history via dispatch. Slice 3 (shipped): dynamic `mvr.bind_fields` on create-on-deliver; research operator deference in prompts. See [`attribute-provenance-program2.md`](attribute-provenance-program2.md).
Program 3 (TBD): Operator write surfaces.

---

## Explicit non-goals (this program)

- Specialist-maintained secondary indices (deferred)
- Per-source `retrieved_at` in v1
- Bind-key alias retention after correction
- Full specialist invoke for MVR validation in v1
- History compaction / archival (revisit when files grow)

---

## Locked decisions (Program 2 — June 2026)

| # | Question | Locked answer |
|---|----------|---------------|
| Q1 | Bind-field history location? | **Specialist `versions[]` only** — no `bind_versions[]` on entity row |
| Q2 | MVR → specialist mapping? | **`categories.json` `attribute_map`** (taxonomy); `mvr.bind_fields` = required bind set |
| Q3 | `provenance=true` response shape? | **Locked Program 1** — parallel top-level block; Slice 2 adds bind fields |
| Q4 | Re-research after operator override? | **Allow** new versions; **prompt deference** when current is `actor: operator` |
| Q5 | Migrate legacy registry-only MVR? | **Hard cutover** — refresh / wipe storage |

---

## Implementation programs (split)

| Program | Scope | Status |
|---------|--------|--------|
| **1 — Provenance** | Extended attrs: `versions[]`, research append, admin read, `provenance=true` | **Complete** (June 2026) — [`attribute-provenance-program1.md`](attribute-provenance-program1.md) |
| **2 — MVR / entity** | Specialist-owned MVR, unified write, taxonomy ownership, read surfaces, research deference | **Complete** (June 2026) — [`attribute-provenance-program2.md`](attribute-provenance-program2.md) |
| **3 — Operator write** | Admin edit, re-research policy | After Program 2 |

---

## Paul review checklist (Program 2 architecture)

- [x] Three-layer model (canonical / indexes / protocol) matches mental model
- [x] Replace bind-key policy (no aliases) acceptable for CRM and future networks
- [x] No entity-level bind history — specialist `versions[]` only
- [x] Taxonomy ownership via `attribute_map`
- [x] Research allows override with prompt deference for operator versions
- [x] Program 2 slice map (3 slices) — see [`attribute-provenance-program2.md`](attribute-provenance-program2.md)