# MVR redesign — Slice M2 (DeliveryStore + TTL)

## Summary

Introduced `DeliveryScope` + `DeliveryStore` (JSON-backed, mirrors `QuoteStore`). Quote and delivery TTL default to **5 minutes** (300s). Not wired into graph yet.

## Changes

| Area | Change |
|------|--------|
| **`src/network/delivery.py`** | **New** — `DeliveryScope`, `issue_delivery()`, `delivery_is_expired()`, `DeliveryStore` (`put`/`get`/`is_expired`), `get_delivery_store()`, `reset_delivery_store()` |
| **`src/network/paths.py`** | `deliveries_path` → `<network_root>/deliveries.json`; env `MYCELIUM_DELIVERIES_PATH` |
| **`src/network/quotes.py`** | `quote_ttl_seconds()` via `MYCELIUM_QUOTE_TTL_SEC` (default **300**); `BuiltinQuoteProvider` uses 5m instead of 1h |
| **`tests/test_delivery_store.py`** | **New** — 5 smoke tests (roundtrip, expiry, unknown id, helper, quote TTL) |
| **`docs/plans/mvr-redesign-program.md`** | Store path note for deliveries + quotes |

**Untouched:** `EntityQuery`, graph, `entity_resolution`, `entity_key`.

## Breaking note

**Quote TTL** reduced from 1 hour to **5 minutes** (configurable). Clients holding quotes longer must re-quote. Delivery TTL matches (MVR redesign R12).

## Verification

```bash
./bin/ci-local
# uv sync OK · admin-ui build OK · ruff OK · 301 smoke passed, 26 deselected
```

## For Grok + Paul

- **M2 complete** — `DeliveryStore` + aligned 5m TTL for quotes and deliveries.
- **M3 unblocked** — `EntityQuery` / `QueryResponse` model changes (`mvr-redesign-slice-m3` prompt to queue).
- **TODO.md:** mark M2 done; queue M3.
- **Not committed** — awaiting review.

Suggested commit message:

```
feat: DeliveryStore and 5-minute quote/delivery TTL (MVR redesign M2)

Add delivery scope store under network_root/deliveries.json; reduce quote
expiry from 1h to MYCELIUM_QUOTE_TTL_SEC default 300s.
```
