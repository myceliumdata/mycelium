# Review — MVR redesign Slice M2 (DeliveryStore + TTL)

**Verdict:** **Approved**

**Reviewer:** Grok (Paul requested review, June 2026)

---

## CI (mandatory)

```bash
./bin/ci-local
```

| Step | Result |
|------|--------|
| `uv sync --all-extras` | OK |
| `admin-ui` build | OK |
| `ruff` | All checks passed |
| smoke pytest | **301 passed**, 26 deselected (+5 new) |

---

## Spec compliance (M2)

| Requirement | Status |
|-------------|--------|
| `DeliveryScope` model | Pass — `entity_ids`, `lookup`, `requested_attributes`, `provenance` |
| `issue_delivery()` → `d_` ids | Pass |
| `DeliveryStore` put/get/is_expired | Pass — mirrors `QuoteStore` atomic JSON |
| `MYCELIUM_DELIVERY_TTL_SEC` default 300 | Pass |
| `deliveries.json` under network root | Pass — `paths.py` + `MYCELIUM_DELIVERIES_PATH` |
| Quote TTL 5m (`MYCELIUM_QUOTE_TTL_SEC`) | Pass — was 1h |
| Unit tests | Pass — `tests/test_delivery_store.py` (5 smoke) |
| No graph / EntityQuery wiring | Pass |
| Program doc store paths | Pass |

---

## Breaking change (accepted)

Quote expiry **1h → 5m** per MVR redesign R12. Documented in output; aligns with `delivery_id` TTL.

---

## Non-blocking nits

| # | Nit | Polish |
|---|-----|--------|
| N1 | Duplicate `_env_int` in `delivery.py` and `quotes.py` | M10 or small shared util |

---

## For Paul

- **Safe to commit** M2.
- **M3 unblocked** — `EntityQuery` / `QueryResponse` models + `lookup_resolved` outcome (no graph wiring yet).

Suggested commit message:

```
feat: DeliveryStore and 5-minute quote/delivery TTL (MVR redesign M2)

Add delivery scope store under network_root/deliveries.json; reduce quote
expiry from 1h to MYCELIUM_QUOTE_TTL_SEC default 300s.
```