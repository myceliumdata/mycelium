# Program 1 — Extended attribute provenance (versioned storage)

**Status:** Locked (Paul, June 2026)  
**Architecture:** [`attribute-provenance-and-storage.md`](attribute-provenance-and-storage.md) (Program 2 = MVR/entity — **deferred**)  
**Breaking changes:** Yes — flat `flat_json_v1` field blobs are **removed**; no lazy migration.

---

## Objective

Versioned provenance for **extended** specialist attributes (`linkedin`, `email`, `phone`, …). Append-only `versions[]` per field; research writes append; admin and `provenance=true` expose history.

**Out of scope (Program 2):** MVR fields on `entities.json`, `bind_versions[]`, `bind_index` replace policy, specialist-owned employer/name.

---

## Locked decisions (Program 1)

| # | Decision |
|---|----------|
| P1-1 | **Hard cutover** — code reads/writes versioned shape only; flat v1 entries are **invalid** (fail loud on read) |
| P1-2 | **No lazy migration** — operators refresh example networks or wipe `agents/*/storage.json`; tests use v2 fixtures only |
| P1-3 | **Unlimited** `versions[]` retention |
| P1-4 | Version **all statuses**: `found`, `na`, `pending` |
| P1-5 | **v1 timestamps:** `at` per version only; sources are `{ "url": "..." }` |
| P1-6 | **Actor** on each version: `research` + `category` + `specialist` for research writes |
| P1-7 | **Default query** — flat `results` unchanged |
| P1-8 | **`provenance=true`** — new structured block on `QueryResponse` (metering promise) |
| P1-9 | Registry `attr_sources` / `last_researched_at` unchanged (summary pointers; timestamp = current version `at`) |
| P1-10 | **`last_researched_at` = last research attempt** — use current version `at` for any status (`found`, `na`, `pending`); not “last successful found” only |
| P1-11 | **Pending retry = in-place update** — same version id; update `at`, `last_error` (preserve `started_at`). **Append** only on status transitions (`empty→pending`, `pending→found`, `pending→na`, `na→found`, etc.) |

---

## Version write rules (P1-11)

| Transition | Action |
|------------|--------|
| No entry → first `pending` | Append `v1` pending |
| `pending` → `pending` (retry / error) | Update current pending version in place |
| `pending` → `found` or `na` | Append new version; set `current_version_id` |
| `na` → `found` (re-research) | Append new version |
| Current `found` → error / partial fail | **No write** (preserve found) |

Rationale: meaningful status changes stay append-only for audit; pending retries are operational noise and preserve `started_at` for stale-retry gates. Safe under async — each research pass still does load → mutate → atomic save on one storage file.

---

## Storage format (`versioned_provenance_v1`)

Bump per-category `storage_strategy.json`:

```json
{
  "strategy": "versioned_provenance_v1",
  "stored_fields": "extended_attributes_only",
  "bind_field_ownership": "registry_or_seed"
}
```

### Per-field shape

```json
"linkedin": {
  "current_version_id": "v1",
  "versions": [
    {
      "id": "v1",
      "at": "2026-06-11T05:26:46.061007+00:00",
      "status": "found",
      "value": "https://www.linkedin.com/in/example",
      "confidence": 0.775,
      "sources": [{ "url": "https://www.linkedin.com/in/example" }],
      "actor": {
        "kind": "research",
        "category": "social",
        "specialist": "social_specialist"
      }
    }
  ]
}
```

**`na` version:**

```json
{
  "id": "v2",
  "at": "2026-06-11T06:00:00+00:00",
  "status": "na",
  "reason": "Insufficient evidence from search results",
  "actor": { "kind": "research", "category": "social", "specialist": "social_specialist" }
}
```

**`pending` version:**

```json
{
  "id": "v1",
  "at": "2026-06-11T05:00:00+00:00",
  "status": "pending",
  "started_at": "2026-06-11T05:00:00+00:00",
  "last_error": "No proposal returned for field 'email'",
  "actor": { "kind": "research", "category": "contact", "specialist": "contact_specialist" }
}
```

### Version id allocation

Monotonic per field: `v1`, `v2`, … (parse trailing int from latest id).

### Flat v1 rejection

If a field entry is a dict with top-level `status` and **no** `versions` key, raise `ValueError` with operator message:

> Storage uses deprecated flat field format; refresh the network or delete `agents/<category>/storage.json`.

No automatic conversion.

---

## Shared module: `src/agents/specialist_fields.py`

Central helpers (used by research, specialists, introspection, query provenance):

| Function | Role |
|----------|------|
| `is_versioned_field(entry) -> bool` | True when `versions` present |
| `validate_versioned_field(entry, *, field_name, category)` | Fail loud on flat v1 |
| `current_version(entry) -> dict \| None` | Resolve `current_version_id` |
| `current_status(entry) -> str` | `pending` / `found` / `na` / `empty` |
| `current_value(entry) -> str \| None` | Display value for merge/results |
| `append_version(entry, version_body) -> dict` | Append + set `current_version_id` |
| `next_version_id(entry) -> str` | `v1` or increment |
| `field_has_value(entry) -> bool` | Hot-path (replaces template helper semantics) |
| `field_is_pending(entry) / field_is_na(entry)` | Status checks on current version |

---

## Query provenance response (Slice 3)

Add optional top-level field on `QueryResponse`:

```json
{
  "outcome": "assembled",
  "results": [{ "id": "…", "linkedin": "https://…" }],
  "provenance": {
    "entities": [
      {
        "id": "…",
        "attributes": {
          "linkedin": {
            "current_version_id": "v1",
            "versions": [ … ]
          }
        }
      }
    ]
  }
}
```

- Present only when `EntityQuery.provenance=true` **and** response has assembled/found results with extended attrs.
- Omit or `null` when `provenance=false` (default).
- MVR attrs (`name`, `employer`) excluded in Program 1.

---

## Admin introspection (Slice 2)

Extend `EntityFieldStatus` (or parallel JSON field `versions`) so `GET /status?entity=…` returns version arrays for extended fields. Admin UI: expandable row per field (read-only).

---

## Slice map

| Slice | Spec | Cursor prompt | Scope |
|-------|------|---------------|--------|
| **1** | [`attribute-provenance-program1-slice1.md`](attribute-provenance-program1-slice1.md) | `2026-06-11-1100-attribute-provenance-slice1` | `specialist_fields.py`, research append, `entity_growth`, strategy bump, tests |
| **2** | [`attribute-provenance-program1-slice2.md`](attribute-provenance-program1-slice2.md) | `2026-06-11-1200-attribute-provenance-slice2` | Template + regen specialists, introspection + admin types |
| **3** | [`attribute-provenance-program1-slice3.md`](attribute-provenance-program1-slice3.md) | `2026-06-11-1300-attribute-provenance-slice3` | `QueryResponse.provenance`, MCP schema, docs |

**Order:** 1 → 2 → 3 (each reviewed before the next).

---

## Explicit non-goals (Program 1)

- Operator write / correction UI (Program 3, after Program 2)
- `bind_versions[]` / MVR specialist ownership (Program 2)
- Per-source `retrieved_at`
- History compaction
- Migrating flat v1 on read

---

## Verification

Each slice: `./bin/ci-local` or full pytest before review. Slice 1+ must keep smoke green with **v2-only** test fixtures.

*Last updated: June 2026*