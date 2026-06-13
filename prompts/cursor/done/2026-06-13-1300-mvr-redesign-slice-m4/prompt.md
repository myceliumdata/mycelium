# MVR redesign — Slice M4 (indexes + step-1 resolve)

**Program:** [`docs/plans/mvr-redesign-program.md`](../../docs/plans/mvr-redesign-program.md)  
**Prerequisite:** M3 reviewed and approved  
**Depends on:** M2 `DeliveryStore` / `issue_delivery()`; M3 `EntityQuery` target fields + `lookup_resolved`

---

## Objective

Build **per-field inverted indexes** on `entities.json` MVR fields and wire **step-1 graph resolve** for target protocol queries (`id` or `lookup`) → `lookup_resolved` with `total_matches` + `issue_delivery()`. **Legacy `entity_key` path remains** until M7 (dual-path gate on query shape).

**Not in M4:** step-2 deliver (M5), metering quote on step 1 (M6), create-on-0 (M7).

---

## Read first

- [`docs/plans/mvr-redesign-entity-query-examples.md`](../../docs/plans/mvr-redesign-entity-query-examples.md)
- [`src/agents/entity_resolution.py`](../../src/agents/entity_resolution.py)
- [`src/network/delivery.py`](../../src/network/delivery.py)
- [`src/models/state.py`](../../src/models/state.py) — `entity_query_is_delivery_step()`
- Graph resolve node(s) under `src/graphs/` or `src/agents/`

---

## Tasks

1. **Per-field index** — build/maintain inverted index per `mvr.bind_fields[]` entry on entity rows (normalized value → `[uuid, …]`). Rebuild on entity load/import; document normalization (case-fold, strip).

2. **Lookup resolve (AND)** — given `lookup` map, intersect uuid sets per field; return match count + entity ids. Unknown `id` → `not_found` (no delivery).

3. **Step-1 graph gate** — when query is **not** delivery step and has `id` or non-empty `lookup` (not legacy-only `entity_key`), run new resolve path:
   - `outcome: lookup_resolved`
   - `total_matches: N`
   - `results: []`
   - `delivery: { delivery_id, expires_at }` via `issue_delivery()` + `DeliveryStore.put()`
   - Bind `requested_attributes` + `provenance` into `DeliveryScope`

4. **Metering off only in M4** — when `metering.enabled`, step-1 target queries may return `quote_required` stub or defer to M6; document choice in `output.md` if not implemented.

5. **Tests** — smoke: index AND match, id resolve, `lookup_resolved` response shape, legacy `entity_key` still hits old path.

---

## Constraints

- **Do not edit `TODO.md`.**
- **Do not** implement step-2 deliver (M5).
- **Do not** remove `entity_key` resolution yet.
- **Do not** widen fuzzy index (R13).

---

## Governance (mandatory)

- **Do not edit `TODO.md`.** Roadmap updates are for Grok + Paul after review.
- In `output.md`, add **"For Grok + Paul"**: what to check off, any roadmap notes.
- Cursor delivers: code, tests, task-scoped docs, and `output.md` only.

---

## Verification

```bash
./bin/ci-local
```

---

## Output

`prompts/cursor/done/2026-06-13-1300-mvr-redesign-slice-m4/` — queue M5 in For Grok + Paul.

Do not commit until review.

---

## Exit criteria

- Per-field indexes built and used for AND lookup
- Target step-1 queries return `lookup_resolved` + `delivery_id`
- Legacy `entity_key` queries unchanged
- Smoke green