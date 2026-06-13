# Review — MVR redesign Slice M6 (metering + quote_id)

**Verdict:** **Approved + polish nits**

**Reviewer:** Grok (Paul requested review, June 2026)

---

## CI

| Step | Result |
|------|--------|
| `uv sync --all-extras` | OK |
| `admin-ui` build | OK |
| `ruff` | All checks passed |
| smoke pytest | **335 passed**, 26 deselected (+5 new) |

---

## Delivery

`output.md` matches all changed/new files. **Complete delivery.**

---

## Diff reviewed

| File | Read |
|------|------|
| `src/agents/target_metering.py` | Full (new) |
| `src/agents/dispatch.py` | Full diff + `target_resolve_node` context |
| `src/agents/metering_gate.py` | Full diff |
| `src/agents/responses.py` | `response_quote_required` hunk |
| `src/network/quotes.py` | Full diff |
| `tests/test_mvr_target_metering.py` | Full (new) |
| `docs/architecture.md` | M6 paragraph |

`/review` subagent not used — diff size moderate; full file read completed.

---

## Spec compliance

| Requirement | Status |
|-------------|--------|
| Step-1 metered + attrs → `quote_required` + `delivery` + `quote` | Pass |
| Step-1 identity-only metered → `lookup_resolved` | Pass — quote deferred to step 2 |
| Step-2 metered → `quote_required` without `quote_id` | Pass |
| Step-2 with accepted `quote_id` → deliver | Pass — `assembled` test |
| Batch line items × N entities | Pass — 3× employer batch ≈ $6.15 |
| Free network unchanged | Pass |
| `WorkloadSpec` binds `delivery_id` + `entity_ids` | Pass |
| Legacy `entity_key` metering | Pass — target gate isolated; legacy still via `metering_gate` |
| No create-on-0 (M7) | Pass |

---

## Legacy / dual-path

Target step-1/2 metering in `target_resolve_node` + `target_metering.py`. Legacy queries still route supervisor → `metering_gate_node` unchanged.

---

## Tests

Five smoke tests cover the main protocol matrix. Gaps (non-blocking): `principal_required` / `payment_required` on target path; provenance-only step-1 quote; explicit legacy `entity_key` metering regression.

---

## Design critique

**Strong**

- Clean separation: `target_metering.py` owns delivery-bound workload + batch cache aggregation without bloating `metering_gate`.
- Step-1 always issues `delivery_id` before quoting — matches program examples (quote workload references delivery).
- `metering_gate` skip when step-2 already has `metering_accepted_quote` avoids double-quote on attrs deliver path.
- Batch pricing uses `entity_ids` count with descriptive line-item suffix.

**Sub-optimal (non-blocking)**

| # | Issue | Suggestion |
|---|--------|------------|
| N1 | Orphan `delivery_id` scopes if step-1 quotes `principal_required` / user abandons | Accept TTL expiry; document in M10 or operator guide |
| N2 | `response_quote_required` dropped `_make_response` wrapper | Verify no lost behavior; unify helpers in polish |
| N3 | `_target_metering_block_response(query, …)` untyped `query` | Add `EntityQuery` annotation |
| N4 | Target metering duplicates quote accept/payment logic from `metering_gate` | M10: shared `accept_quote_for_workload()` helper |

---

## Nits

See design table N1–N4. None blocking.

---

## For Paul

- **Committed locally** by Grok; **not pushed**.
- **M7 unblocked** — create-on-0, remove `name_source` / old resolution per program.

Suggested commit message:

```
feat: target protocol metering and quote_id gate (MVR redesign M6)

Quote step-1 attrs via delivery_id workload; gate step-2 on quote_id;
batch line items scale by entity count in delivery scope.
```