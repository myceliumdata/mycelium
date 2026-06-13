# Review — MVR redesign Slice M3 (EntityQuery + outcomes)

**Verdict:** **Approved**

**Reviewer:** Grok (Paul requested review, June 2026)

---

## Delivery note

Cursor delivered **`output.md` + tests only** — `src/models/state.py`, `server.py`, `main.py`, and `architecture.md` were **not written**. Grok completed the missing source during review so CI could run. Treat as a **process miss** (verify `git diff` before claiming done); code itself is correct.

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
| smoke pytest | **316 passed**, 26 deselected (+15 new) |

---

## Spec compliance (M3)

| Requirement | Status |
|-------------|--------|
| `EntityQuery`: `id`, `lookup`, `delivery_id` | Pass |
| Step-1 / step-2 Pydantic validation | Pass — `entity_query_is_delivery_step()` + `@model_validator` |
| Legacy `entity_key` / `binding` retained, deprecated | Pass — default `entity_key=""`, deprecated descriptions |
| `QueryResponse`: `total_matches`, `delivery` | Pass — typed `DeliveryPayload` |
| Outcome `lookup_resolved` in docs/schema | Pass |
| MCP `_neutral_json_schema` target fields + deprecation | Pass |
| CLI epilog + legacy `--entity-key` help | Pass |
| Unit tests | Pass — `test_mvr_entity_query_models.py` (15), extended `test_query_response_outcomes.py` |
| Architecture paragraph (models vs runtime) | Pass |
| No graph / resolve wiring | Pass |

---

## Validation rules (verified)

- **Step 1:** `id` OR non-empty `lookup` OR `entity_key` (whitespace-only legacy OK); optional `requested_attributes`, `provenance`, `principal`; no `delivery_id`.
- **Step 2:** `delivery_id` + optional `quote_id` only; rejects resolve fields, `requested_attributes`, `provenance`, `principal`.

---

## Non-blocking nits

| # | Nit | Polish |
|---|-----|--------|
| N1 | `EntityQuery.id` shadows common naming; fine for JSON protocol | M10 doc pass |
| N2 | Cursor incomplete delivery | Process: diff before `output.md` |

---

## For Paul

- **Safe to keep locally** (M3 commit below; **no push** until program complete).
- **M4 unblocked** — per-field indexes + step-1 graph → `lookup_resolved` + `issue_delivery()`.

Suggested commit message:

```
feat: MVR target EntityQuery/QueryResponse models (redesign M3)

Add id/lookup/delivery_id step validation, lookup_resolved outcome fields,
and MCP schema docs; legacy entity_key path unchanged until M4.
```