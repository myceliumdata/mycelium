# Output — Entity metering implementation (Slice 10)

## Summary

Implemented v1 metering hooks in a **single slice**: policy load, builtin quotes, entitlements/quotes stores, `metering_gate` graph node, `quote_required` outcome, and Paul/Jan E2E tests. CRM default remains `metering.enabled: false`.

## Changes

| Area | Files |
|------|-------|
| Policy | `src/network/metering_policy.py` |
| Stores | `src/network/entitlements.py`, `src/network/quotes.py` |
| Gate | `src/agents/metering_gate.py` |
| Graph | `src/graphs/core.py` — `metering_gate` after `validate_entity` |
| Models | `EntityQuery.quote_id/principal`, `QueryResponse.quote`, graph metering fields |
| Responses | `response_quote_required()` |
| Paths | `entitlements_path`, `quotes_path` + env vars |
| Introspection | MCP policy strings for quote loop |
| CRM example | `network.json` metering block (`enabled: false`) |
| Tests | `tests/test_entity_metering.py` (16 tests) |

## Design notes

- **Checkpoint fix:** Clear `pending_quote` on accept/bypass so thread reuse does not re-emit `quote_required` after `quote_id` retry.
- **Entitlement write:** After accepted production quote + successful research in `invoke_specialists_node`.
- **Bypass:** `MYCELIUM_AUTO_ACCEPT_QUOTES=1` or `metering.enabled: false`.
- **Pricing:** Env overrides `MYCELIUM_METER_RESEARCH_USD`, `MYCELIUM_METER_QUERY_VALUE_USD`, `MYCELIUM_METER_QUERY_PROVENANCE_USD`.

## Tests

```bash
uv run pytest tests/test_entity_metering.py -q                    # 16 passed
uv run pytest tests/test_entity_growth.py tests/test_entity_research_gate.py -q  # regression OK
```

## Manual smoke (Paul, optional)

1. Local CRM network: set `metering.enabled: true` in `network.json`.
2. Query with `requested_attributes` → inspect `quote_required` + `quote.line_items`.
3. Retry with `quote_id` → research runs.
4. Second principal query → consumption-only quote (`cache_state: hit`).

## For Grok + Paul

- Mark **Entity metering Slice 10** done in `TODO.md` after review.
- Suggested commit message: `feat(metering): quote_required gate, entitlements, and builtin pricing (slice 10)`
- No split into 10a/10b — graph routing testable in one slice.

## Exit criteria

- [x] Layer 1 + 2 tests pass
- [x] Entity protocol regression (growth + research gate) unchanged with CRM default
- [x] `describe_network` documents quote loop + `quote_id`
- [x] Ruff clean; no `TODO.md` edit
