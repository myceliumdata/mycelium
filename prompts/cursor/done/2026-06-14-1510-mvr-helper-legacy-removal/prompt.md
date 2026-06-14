# Program 3 — Slice 1510: MVR helper legacy removal (item 5)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` before starting.

**Program:** [`docs/plans/entity-protocol-legacy-cleanup-program.md`](../../docs/plans/entity-protocol-legacy-cleanup-program.md)  
**Prerequisite:** Slice **1500** approved (generic `bind_values` on registry).

**Paul:** One MVR completeness rule — **`missing_mvr_bind_fields(lookup)`** only. Delete `entity_key satisfies name`.

---

## Objective

Remove legacy MVR negotiation helpers that assume step-1 was `entity_key` + `binding`. Target protocol already uses `lookup` maps.

---

## Read first

- [`src/network/mvr.py`](../../src/network/mvr.py) — `required_bind_fields`, `required_fields_for_entity_key`, `allowed_binding_keys`, `normalize_binding`
- [`src/agents/entity_resolution.py`](../../src/agents/entity_resolution.py) — callers of `required_bind_fields`
- [`src/agents/responses.py`](../../src/agents/responses.py) — `response_entity_unknown` uses `required_fields_for_entity_key`
- [`src/network/mvr.py`](../../src/network/mvr.py) — `missing_mvr_bind_fields` (keep)

---

## Locked design

### 1. Delete from `MvrPolicy`

- `required_bind_fields(entity_key, binding)` — **remove**
- `required_fields_for_entity_key(entity_key)` — **remove**
- `allowed_binding_keys()` — **remove** if only used for legacy `binding`
- `normalize_binding()` — **remove** if only used for legacy `EntityQuery.binding`

Keep: `missing_mvr_bind_fields`, `is_full_mvr_lookup`, `normalized_lookup_values`, `can_create_on_zero_matches`, `load_mvr`.

### 2. Replace callers (until slice 1530 removes legacy graph)

Legacy paths still exist briefly — update to use **`missing_mvr_bind_fields`** with an explicit lookup map:

| Legacy input | Lookup map for helper |
|--------------|----------------------|
| `entity_key="Paul Murphy"` only | `{"name": "Paul Murphy"}` |
| `entity_key` + `binding.employer` | `{"name": entity_key, "employer": binding["employer"]}` |

Do **not** reintroduce “non-empty entity_key ⇒ name satisfied” anywhere.

### 3. `response_entity_unknown` / legacy responses

If still present (removed in 1530), switch to `missing_mvr_bind_fields` built from a lookup map. Slice 1530 may delete these functions — this slice only fixes compile/runtime if 1500 left callers.

---

## Tests (smoke — mandatory)

| Test | Assert |
|------|--------|
| **New:** `test_missing_mvr_bind_fields_partial_name` | `{"name":"Paul"}` → `["employer"]` for CRM MVR |
| **New:** `test_missing_mvr_bind_fields_employer_only` | `{"employer":"Acme"}` → includes `name` (not empty) |
| **New:** `test_mvr_policy_has_no_required_bind_fields_entity_key` | `MvrPolicy` has no `required_bind_fields` method |

No test should call deleted methods. `./bin/ci-local` green.

---

## Out of scope

- Removing `EntityQuery.binding` model field (1530)
- Status `resolve` JSON (1520)

---

## Docs

Do not edit `TODO.md`.

---

## Deliverable

`prompts/cursor/done/2026-06-14-1510-mvr-helper-legacy-removal/` — suggested commit:

```
refactor(mvr): drop entity_key satisfaction from bind field helpers
```