# Why specialist-owned data (no `core_data`)

**Status:** Shipped (seed elimination + Program 2, June 2026)  
**Mechanics:** [`architecture.md`](../../architecture.md) § Core Architectural Philosophy · [`attribute-provenance-and-storage.md`](../../plans/attribute-provenance-and-storage.md)

---

## The short answer

There is **no privileged core dataset** that the supervisor queries directly. Every fact — including MVR bind fields like `name` and `employer` — is owned by a **specialist agent** with its own storage. The supervisor **routes and coordinates**; it does not read or write specialist files.

The entity registry (`entities/<record_type>.json`) holds protocol metadata, search indexes, and a **denormalized cache** of current bind values for fast step-1 resolve. Canonical history lives in specialist `versions[]`.

---

## What problem we were solving

Early CRM prototypes treated a central `people` table / `core_data` specialist as the source of truth. That created recurring failures:

| Failure | Symptom |
|---------|---------|
| **God agent temptation** | Supervisor or “core” bypasses specialists → one place to break isolation |
| **Split ownership** | Seed said one employer; professional specialist researched another — who wins? |
| **Scale mismatch** | CRM web research and baseball warehouse stats need different storage strategies in one network |
| **No evolution path** | Central schema cannot adapt per domain without framework releases |

Paul’s constraint (June 2026): even **identity resolution** may require specialist participation — finding a person is not always a single SQL lookup on a universal table.

---

## Why the supervisor stays thin

The supervisor (`src/agents/supervisor.py`):

- Resolves registry matches and classifies `requested_attributes`
- Plans which specialists to invoke
- Does **not** assemble the final response when specialists run (that is `assemble_response` after `invoke_specialists`)
- Does **not** own storage or define derivative schemas centrally

**Benefits:**

1. **Explicit boundaries** — framework code uses `agents.specialists.protocol` dispatch; it never opens `agents/<category>/storage.json` directly.
2. **Network heterogeneity** — baseball `batting_specialist` can use warehouse SQL internally; CRM `professional_specialist` uses versioned JSON — same snapshot contract outward.
3. **Agent Factory hook** — new categories appear when classification demands them; storage strategy is per specialist (`storage_strategy.json`, future `migrate_to`).
4. **Audit clarity** — every `found` value has an `actor` (specialist, research, bind, operator) in version history.

---

## Why a registry cache still exists

Specialist storage is authoritative for **values and provenance**, but step-1 lookup cannot scan every specialist file on every query.

The registry therefore holds **derived** artifacts:

- `bind_index` and per-field indexes for O(1) resolve
- Cached current bind values on each entity row
- Protocol metadata (`validation_state`, `field_states`, summary pointers)

Writes flow **specialist first → registry sync** via `agents/attribute_write.py`. Reads for graph context use dispatch snapshots, not raw storage layout.

This is not a return to `core_data` — the registry does not own research logic or domain schemas.

---

## MVR bind fields are specialist-owned too

`name` and `employer` are not “registry-only” fields. When requested or corrected, they follow the same versioned storage rules as `linkedin` or `career_hr`:

- Taxonomy assigns an owning category (CRM: demographic / professional)
- `versions[]` records bind and operator history
- Entity row cache updates atomically with indexes

Bind corrections use **replace** policy: new canonical value, index updated, old bind key not kept as alias.

---

## What we deliberately did not do

| Alternative | Why we rejected it |
|-------------|-------------------|
| Central `people` SQLite table | One schema for all networks; bypasses specialist isolation |
| Supervisor reads specialist files | Breaks encapsulation; blocks storage migration (JSON → minisql) |
| Registry as source of truth for attrs | No version history; provenance and operator edits become second-class |
| Pre-defined derivative tables in core | Violates “specialists own their domains”; blocks emergent organization |

---

## Mental model

```text
Client query
    → supervisor (route only)
    → specialist(s) (read/write domain storage)
    → dispatch snapshots
    → assemble_response
    → registry cache/index sync on writes
```

**Rule of thumb:** if you are adding framework code that opens `agents/*/storage.json`, stop — add or extend dispatch and snapshots instead.