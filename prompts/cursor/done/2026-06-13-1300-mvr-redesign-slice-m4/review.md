# Review — MVR redesign Slice M4 (indexes + step-1 resolve)

**Verdict:** **Approved**

**Reviewer:** Grok (Paul requested review, June 2026)

---

## CI (mandatory)

```bash
./bin/ci-local
```

| Step | Result |
|------|--------|
| `uv sync --all-extras` | OK |
| `admin-ui` build | OK |
| `ruff` | All checks passed |
| smoke pytest | **323 passed**, 26 deselected (+7 new) |

---

## Delivery verification

`output.md` claims match `git diff` + new files: `field_index.py`, `target_resolve.py`, `test_mvr_target_resolve.py`, and listed modifications. **Complete delivery** (unlike M3).

---

## Spec compliance (M4)

| Requirement | Status |
|-------------|--------|
| Per-field inverted indexes on MVR bind fields | Pass — `field_index.py`, rebuild on load/save in `entity_registry.py` |
| AND lookup intersection | Pass — `intersect_lookup()` + `lookup_by_target_lookup()` |
| Unknown `id` → `not_found`, no delivery | Pass — tested |
| Step-1 graph: `id`/`lookup` → `lookup_resolved` + `issue_delivery()` | Pass — `target_resolve_node`, START → `target_resolve` routing |
| `requested_attributes` + `provenance` in `DeliveryScope` | Pass — tested on lookup query |
| Legacy `entity_key` unchanged | Pass — defers to supervisor; `found` outcome test |
| No step-2 deliver | Pass |
| No fuzzy index widening | Pass |
| Metering on step 1 | Deferred to M6 — documented in `output.md` (`lookup_resolved` even when metering enabled) |

---

## Non-blocking nits

| # | Nit | Polish |
|---|-----|--------|
| N1 | `_entity_field_value` hard-codes `name`/`employer` only | Generalize when bind_fields expand beyond CRM (M7+) |
| N2 | M4 tests use `run_query` + real seed import | Acceptable; borderline full — keep smoke unless CI slows |

---

## For Paul

- **Committed locally** by Grok after this review; **not pushed**.
- **M5 unblocked** — step-2 deliver via `delivery_id` (metering off).

Suggested commit message (used):

```
feat: per-field indexes and step-1 lookup_resolved (MVR redesign M4)

Add registry field indexes, target_resolve graph node, and delivery issuance
for id/lookup queries; legacy entity_key path unchanged.
```