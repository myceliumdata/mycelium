# Slice 11 fix — Payment settlement nits

## Summary

Closed six review nits from Slice 11 payment settlement. No Slice 12 scope; CRM `payment.enabled: false` unchanged.

## Fixes

| # | Fix |
|---|-----|
| F1 | `quote_is_expired()` in `quotes.py`; `settle_quote()` rejects expired quotes; `accept()` refactored to use helper |
| F2 | Credit provider validates balance only; deduct after `mark_paid`; `revert_paid()` on deduct failure |
| F3 | `test_mcp_pay_quote_round_trip` — direct `pay_quote` → `assembled` |
| F4 | Exit criteria `[x]` in payment + metering implementation specs; program doc Slice 11 fix subsection |
| F5 | `MYCELIUM_X402_FACILITATOR_URL` noted in `payment.py` docstring + `architecture.md` |
| F6 | `test_accept_rejects_expired_paid_quote` — expired paid quote re-issues `quote_required`, not `assembled` |

## Code changes

- `src/network/quotes.py` — `quote_is_expired()`, `revert_paid()`, DRY `accept()`
- `src/network/credits.py` — `has_sufficient_balance()`
- `src/network/payment.py` — expiry check, credit ordering, x402 env docstring
- `tests/test_entity_payment.py` — 4 new tests (12 total)

## Tests

**44 passed** — 12 payment + 20 metering + 12 entity regression.

```bash
uv run pytest tests/test_entity_payment.py tests/test_entity_metering.py \
  tests/test_entity_research_gate.py tests/test_entity_growth.py -q
```

## For Grok + Paul

- Mark **Slice 11 fix (`2210`)** done in `TODO.md`
- Slice 11 parent already **review approved**; this fix slice ready for review
- Review folder: `prompts/cursor/done/2026-06-09-2210-entity-metering-payment-slice11-fix/`
- Suggested commit message (after review):

```
Fix payment settlement nits (Slice 11 fix): expiry, credit ordering, MCP test.

Reject expired quotes in settle_quote; deduct credits after mark_paid with
revert on failure. Add pay_quote MCP round-trip and expired-paid gate tests.
```

- **Did not edit `TODO.md`** (per governance)
