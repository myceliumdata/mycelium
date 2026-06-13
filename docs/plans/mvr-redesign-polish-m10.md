# MVR redesign — polish backlog (slice M10)

**Status:** Open — accumulate during M1–M9 review; address in **M10**  
**Program:** [`mvr-redesign-program.md`](mvr-redesign-program.md)

---

## Purpose

Non-blocking nits from Grok review of MVR slices **M1–M9** are logged here **and** in each slice `review.md`. **M10** works this backlog — do not insert these into the main M1–M9 sequence.

**Blocking nits** do **not** go here. They become **fix / remedial slices** queued before the next planned slice (see `prompts/cursor/WORKFLOW.md` §4).

---

## Backlog

| # | Source | Nit | Suggested fix |
|---|--------|-----|----------------|
| P1 | M2 | Duplicate `_env_int` in `delivery.py` and `quotes.py` | Shared `network/env_util.py` or quotes import |
| P2 | M3 | `EntityQuery.id` shadows common naming | M10 doc pass only |
| P3 | M3 | Cursor incomplete delivery (process) | WORKFLOW §3 checklist (done) |
| P4 | M4 | `_entity_field_value` hard-codes `name`/`employer` only | Generalize from `mvr.bind_fields` |
| P5 | M4 | M4 tests use `run_query` + seed import (borderline full) | Re-category or keep smoke if CI ok |
| P6 | M5 | Specialist + jinja churn for `graph_requested_attributes()` | Document regen; optional helper consolidation |
| P7 | M5 | Step-2 provenance on identity-only deliver not smoke-tested | Add test in M8 or M10 |
| P8 | M6 | Orphan `delivery_id` if quote abandoned / `principal_required` | Document TTL; operator guide |
| P9 | M6 | `response_quote_required` dropped `_make_response` wrapper | Verify parity; unify response builders |
| P10 | M6 | `_target_metering_block_response` untyped `query` | `EntityQuery` annotation |
| P11 | M6 | Target metering duplicates accept/payment logic vs `metering_gate` | `accept_quote_for_workload()` helper |
| P12 | M6 | No tests: `principal_required` / `payment_required` on target path | M10 smoke |
| P13 | M6 | Provenance-only step-1 quote not tested | M10 smoke |
| P14 | M7 | `bind_provisional_from_scope` hard-codes `name`/`employer` | Generalize from `mvr.bind_fields` (merge with P4) |
| P15 | M7 | `is_full_mvr_lookup` — document empty-value behavior | Doc comment or operator guide |
| P16 | M7 | Metered create-on-deliver path untested | `crm-metering` smoke |
| P17 | M7 | `architecture.md` slice header bullets missing M7+ one-liners | Doc sync in M10 |
| P18 | M8 | `partition_attribute_buckets` ignores per-entity contribution status | Pass `entity_id` or aggregate conservatively for batch `message` |
| P19 | M8 | No smoke for batch step-2 identity-only (`found`, N rows, no attrs) | Optional M10 |
| P20 | M8 | Sequential N×M specialist invocations on batch deliver | Document; parallelize only if perf requires |
| P21 | M8 | `architecture.md` slice header bullets omit M8 batch line | Merge into M10 doc sync (with P17) |

*Add rows as M9 review lands.*

---

## Exit criteria (M10)

- [ ] All open rows addressed or explicitly waived
- [ ] `./bin/ci-local` green
- [ ] `review.md` for M10 references closed row ids