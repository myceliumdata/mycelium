# Task: Entity metering implementation — Slice 10

> **READY** — Slice 9 design locked. Move to `in-progress/` to start.

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/entity-metering-design-phase9.md`](../../docs/plans/entity-metering-design-phase9.md) — **locked design (D1–D22)**
- [`docs/plans/entity-metering-implementation.md`](../../docs/plans/entity-metering-implementation.md) — **implementation spec**

**Depends on:** Entity protocol Slices 1–8 shipped.

---

## Objective

Implement v1 metering hooks in **one slice**: `quote_required`, multi-line-item quotes, `entitlements.json`, commit + consumption gates, CRM-default `metering.enabled: false`. No payment provider.

Paul: prefer one slice; split only if graph routing cannot be tested cleanly (document in `output.md` if you split).

---

## Locked behaviors (do not reinterpret)

| Decision | Implementation |
|----------|----------------|
| Q9a-A | Multi-line-item per job |
| Q9g-A | Meters: production, query_value, query_provenance |
| Q9m-B default | `meter_first_delivery: true`; override in `network.json` |
| Q9c-A | Classify before quote (supervisor already classifies; gate runs after validate) |
| Q9f-B | Sync quotes only |
| Q9l-A | `quote_id` on `EntityQuery` retry |
| Q9h-A | `entitlements.json` under network_root |
| Q9i-A | Principal optional marginal; required for sponsor_public/pool commits |
| Q9j-B | No pool_id / rebate schema |
| Q9k-A | `full_duplicate` opt-in in policy |
| Q9b-A | Validation stays free (gate must not block validate_entity) |

---

## Deliverables

### Code

1. **`src/network/metering_policy.py`** — load `metering` block from `network.json`; CRM-safe defaults when absent (`enabled: false`).
2. **`src/network/entitlements.py`** — atomic JSON store; lookup by `scope_hash`.
3. **`src/network/quotes.py`** — `Quote`, `WorkloadSpec`, `BuiltinQuoteProvider`, `QuoteStore` (`quotes.json`).
4. **`src/agents/metering_gate.py`** — `metering_gate_node`; helpers for scope hash, cache state, entitlement write after research.
5. **Graph** — insert `metering_gate` after `validate_entity` per implementation spec diagram; conditional route to `assemble_response` on `quote_required`.
6. **`src/models/state.py`** — `BillingPrincipal`, `quote_id`, `principal` on `EntityQuery`; `quote` on `QueryResponse`; `quote_required` outcome docs.
7. **`src/agents/responses.py`** — `response_quote_required()`.
8. **`src/network/paths.py`** — `entitlements_path`, `quotes_path` + env vars.
9. **`src/network/introspection.py`** — MCP policy strings for quote loop.
10. **`examples/networks/crm/network.json`** — add disabled `metering` block (documented; `enabled: false`).

### Tests — `tests/test_entity_metering.py`

Cover table in implementation spec. Metering off must not regress existing entity tests.

### Bypass

- `MYCELIUM_AUTO_ACCEPT_QUOTES=1` skips gate when metering enabled (tests + demos).

---

## Non-goals (do not implement)

- HTTP 402, wallet, payment settlement, rebate ledger
- Async quote jobs
- Dynamic `quote_provider` class import (Protocol stub OK)
- Blockchain SLA / freshness meters in tests
- Admin UI
- **Do not edit `TODO.md`**

---

## Gate logic (guidance)

**Production** line when `cache_state` is `miss` or `partial` (delta production).

**Consumption** line when delivering `requested_attributes` and `meter_first_delivery` policy says so (default: always, including first assembly).

**Marginal** on cache hit: consumption only; expose `avoidable_cost` on quote when production would have applied under full_duplicate.

On accepted production quote + successful specialist research: write entitlement with `scope_hash`, optional `sponsor_id` from principal.

---

## Governance

- Match patterns in `src/network/mvr.py`, `src/agents/entity_registry.py` (atomic JSON save).
- Keep specialist/Tavily behavior unchanged when metering disabled.
- Report **For Grok + Paul** section in `output.md` with any spec ambiguities.

---

## Exit criteria

- [ ] `uv run pytest tests/test_entity_metering.py` passes
- [ ] Entity protocol smoke tests still pass with default CRM `network.json`
- [ ] `describe_network` mentions `quote_required` + `quote_id` retry
- [ ] Deliverables under `prompts/cursor/done/2026-06-09-2100-entity-metering-implementation/`