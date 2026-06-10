# Review — Entity metering Slice 10 fix (`2110`)

**Reviewer:** Grok (June 2026)  
**Verdict:** **Approve** — all F1–F5 delivered; tests green; ready to commit with Slice 10.

---

## Summary

Fix slice closes every nit from Slice 10 review. No scope creep; no payment work.

---

## Checklist

| Fix | Verdict | Notes |
|-----|---------|-------|
| F1 `provenance` on `EntityQuery` | Pass | Wired in `build_workload_spec`; scope_hash differs; `query_provenance` meter |
| F2 `full_duplicate` E2E | Pass | Cache hit still quotes production line |
| F3 `meter_first_delivery: false` E2E | Pass | First quote research-only; follow-up consumption |
| F4 `principal_required` outcome | Pass | Replaces generic `error`; dedicated response builder |
| F5 sponsor E2E | Pass | `sponsor_public` without principal → `principal_required` |

---

## Tests

- `test_entity_metering.py`: **20 passed**
- `test_entity_research_gate.py` + `test_entity_growth.py`: regression **OK**

---

## Nits

None blocking.

**Non-blocking (future):** `principal_required` not yet in program doc outcome table — add in Slice 11 doc pass or now.

---

## Recommendation

Commit with Slice 10 metering work (or immediately after). Suggested message from output.md stands.