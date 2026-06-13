# MVR redesign — Slice M6 (metering + quote_id)

## Summary

Metering wired into the target two-step protocol: metered step-1 with attrs → `quote_required` (+ `delivery_id`); step-2 requires `quote_id` when `metering.enabled`; batch line items scale × N entities. Legacy `entity_key` metering unchanged.

## Changes

| Area | Change |
|------|--------|
| **`src/network/quotes.py`** | `WorkloadSpec` gains `delivery_id` + `entity_ids`; scope hash for delivery workloads; batch pricing × entity count |
| **`src/agents/target_metering.py`** | **New** — delivery workload, batch cache state, step-1/2 quote gate |
| **`src/agents/dispatch.py`** | `target_resolve_node` integrates metering for step-1 and step-2 |
| **`src/agents/metering_gate.py`** | Skip duplicate gate only for target step-2 with pre-accepted quote |
| **`src/agents/responses.py`** | `response_quote_required` accepts `total_matches` + `delivery` |
| **`tests/test_mvr_target_metering.py`** | **New** — 5 smoke tests |
| **`docs/architecture.md`** | M6 metering paragraph |

**Untouched:** create-on-0 (M7), batch provenance shape (M8), CLI/MCP migration (M9).

## Protocol behavior

| Step | Metering off | Metering on |
|------|--------------|-------------|
| Step-1, attrs | `lookup_resolved` | `quote_required` + `delivery` + `quote` |
| Step-1, identity only | `lookup_resolved` | `lookup_resolved` (quote on step-2) |
| Step-2 | `found` / `assembled` | `quote_required` until `quote_id` accepted |

## Verification

```bash
./bin/ci-local
# uv sync OK · admin-ui build OK · ruff OK · 335 smoke passed, 26 deselected
```

## For Grok + Paul

- **M6 complete** — target protocol metering + quote_id gate.
- **M7 unblocked** — create-on-0 (full MVR lookup, 0 matches).
- **TODO.md:** mark M6 done; queue M7 (`mvr-redesign-slice-m7`).
- **Not committed** — awaiting review.

Suggested commit message:

```
feat: target protocol metering and quote_id gate (MVR redesign M6)

Quote step-1 attrs via delivery_id workload; gate step-2 on quote_id;
batch line items scale by entity count in delivery scope.
```
