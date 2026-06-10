# Review — Entity metering Slice 11 fix (`2210`)

**Reviewer:** Grok (June 2026)  
**Verdict:** **Approve** — all F1–F6 delivered; 44 tests green; ready to commit.

---

## Summary

Fix slice closes every nit from Slice 11 review plus doc hygiene. Credit settlement ordering is correct (deduct after `mark_paid` with `revert_paid` rollback). Expiry is enforced consistently in `settle_quote` and `accept()`. No Slice 12 scope creep.

---

## Checklist

| Fix | Verdict | Notes |
|-----|---------|-------|
| F1 Quote expiry in `settle_quote` | Pass | `quote_is_expired()` shared; `accept()` DRY |
| F2 Credit after `mark_paid` | Pass | `has_sufficient_balance()` validate-only; `_deduct_credit_after_paid()` + `revert_paid()` |
| F3 MCP `pay_quote` test | Pass | `test_mcp_pay_quote_round_trip` → `assembled` |
| F4 Doc exit criteria | Pass | Implementation specs `[x]`; program doc updated |
| F5 X402 env note | Pass | `payment.py` docstring + `architecture.md` |
| F6 Expired paid quote gate | Pass | Re-issues `quote_required` with new quote_id |

---

## Tests

- `test_entity_payment.py`: **12 passed** (4 new)
- `test_entity_metering.py`: **20 passed**
- research_gate + growth: **12 passed**
- **Total: 44 passed**
- Ruff: clean on touched files

---

## Nits

None blocking.

---

## Recommendation

Commit with Slice 11 (or immediately after). Suggested message from `output.md` stands.