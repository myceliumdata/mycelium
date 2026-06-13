# Program 2 — Slice 2: Read surfaces (provenance + admin)

## Summary

MVR bind field version history is now exposed on read paths. `provenance=true` query responses include `name` / `employer` when versioned specialist storage exists; admin entity drill-down and admin UI show expandable version timelines for bind fields alongside extended fields. Default flat `results[]` unchanged.

Bind fields without versioned specialist entries are omitted from provenance (backward compat during cutover).

## Changes

| Area | Change |
|------|--------|
| **`src/agents/query_provenance.py`** | Removed bind-field exclusion; all requested attrs resolved via taxonomy + specialist storage |
| **`src/network/introspection.py`** | `_bind_field_versions` loads `versions[]` from owning specialist; bind drill-down includes history |
| **`admin-ui/src/App.tsx`** | Bind rows use same `VersionHistoryPanel` as extended fields |
| **`src/models/state.py`** | `QueryResponse.provenance` description documents bind fields |
| **Tests** | Updated provenance + admin + status tests; added bind provenance smoke tests |
| **Docs** | `architecture.md`, `attribute-provenance-and-storage.md`, `mvr-redesign-entity-query-examples.md` |

## Example provenance (bind + extended)

```json
{
  "provenance": {
    "entities": [
      {
        "id": "…",
        "attributes": {
          "name": {
            "current_version_id": "v1",
            "versions": [{ "id": "v1", "value": "Paul Murphy", "actor": { "kind": "seed_bootstrap", … } }]
          },
          "employer": {
            "current_version_id": "v1",
            "versions": [{ "id": "v1", "value": "Acme Corp", … }]
          },
          "linkedin": { "current_version_id": "v1", "versions": […] }
        }
      }
    ]
  }
}
```

Display values on bind rows still come from entity cache; `versions[]` from specialist files.

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 375 passed, 26 deselected
# admin-ui build OK · ruff OK
```

## For Grok + Paul

- **Slice complete** — read surfaces for MVR bind field versions (provenance + admin).
- **Hands-on:** Seed-import CRM entity → admin drill-down on Andrea Kalmans shows bind field version cards; `provenance=true` query with `name`/`employer` requested returns version blocks.
- **Out of scope (Slice 3):** research operator deference, `bind_provisional_from_scope` generalization polish.
- **Not committed** — awaiting review.
- **TODO.md:** Mark Program 2 Slice 2 done; queue Slice 3 when ready.

Suggested commit message:

```
feat: expose MVR bind field versions on provenance and admin read paths

Include name/employer in QueryResponse.provenance when specialist storage
has versions; admin drill-down and UI show bind version timelines; omit
bind attrs without versioned entries for cutover compat.
```
