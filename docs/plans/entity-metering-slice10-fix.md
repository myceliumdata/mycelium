# Metering Slice 10 — fix slice

**Status:** Ready for Cursor  
**Depends on:** Slice 10 shipped (`prompts/cursor/done/2026-06-09-2100-entity-metering-implementation/`)  
**Program:** [`entity-protocol-and-registry-program.md`](entity-protocol-and-registry-program.md)

---

## Objective

Close review nits from Slice 10 metering implementation without expanding scope to payment (Slice 11).

---

## Fixes (locked)

| # | Gap | Fix |
|---|-----|-----|
| F1 | `WorkloadSpec.provenance` hardcoded `false` | `EntityQuery.provenance: bool = False`; wire through `build_workload_spec`; affects `scope_hash` and `query_provenance` meter |
| F2 | No `full_duplicate` E2E | Integration test: cache hit + `default_funding_model: full_duplicate` → production line on quote |
| F3 | No `meter_first_delivery: false` E2E | Integration test: first quote production-only; follow-up query still consumption |
| F4 | Principal missing → generic `error` | New outcome `principal_required` + `response_principal_required()`; message names funding model |
| F5 | Sponsor path untested E2E | Integration test: `sponsor_public` + no principal → `principal_required` |

---

## Non-goals

- Payment / x402 (Slice 11)
- Freshness meters
- Pluggable QuoteProvider loading
- Admin UI
- **Do not edit `TODO.md`**

---

## Tests

Extend `tests/test_entity_metering.py`:

- `test_provenance_meter_on_quote` — `provenance=true` → `query_provenance` line; scope_hash differs from `false`
- `test_full_duplicate_cache_hit_includes_production`
- `test_meter_first_delivery_false_first_quote`
- `test_sponsor_public_principal_required_e2e`

Regression: existing 16 tests + entity protocol smokes unchanged.

---

## Doc touch-ups

- `EntityQuery` / `QueryResponse` outcome descriptions
- `describe_network` / introspection — `provenance` field + `principal_required`
- Program doc outcome table — add `principal_required`