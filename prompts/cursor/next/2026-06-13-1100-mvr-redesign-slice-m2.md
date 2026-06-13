# MVR redesign — Slice M2 (DeliveryStore + TTL)

**Program:** [`docs/plans/mvr-redesign-program.md`](../../docs/plans/mvr-redesign-program.md)  
**Prerequisite:** M1 reviewed and approved  
**Depends on:** M1 docs only — no runtime query path changes in M2

---

## Objective

Introduce **`DeliveryStore`** and **`DeliveryScope`** model (mirror `QuoteStore` pattern). Set **5-minute TTL** for delivery tokens and quotes (default 300s, env-configurable). Unit tests only — **do not wire into graph yet** (M4–M5).

---

## Read first

- [`docs/plans/mvr-redesign-program.md`](../../docs/plans/mvr-redesign-program.md) — R6, R12, Implementation stores
- [`src/network/quotes.py`](../../src/network/quotes.py) — `QuoteStore`, expiry pattern
- M1 review: `prompts/cursor/done/2026-06-13-1000-mvr-redesign-slice-m1/review.md`

---

## Tasks

1. **`DeliveryScope` model** (Pydantic or dataclass in `src/network/delivery.py` or `src/models/delivery.py`):
   - `delivery_id`, `expires_at`, `entity_ids: list[str]`, `lookup` snapshot (dict), `requested_attributes`, `provenance: bool`
   - Factory: `issue_delivery(...)` → new `d_` id

2. **`DeliveryStore`** — file-backed or in-memory like quotes (match existing quote store pattern under network root or runtime path):
   - `put(scope)`, `get(delivery_id)`, `is_expired`
   - TTL from `MYCELIUM_DELIVERY_TTL_SEC` (default **300**)

3. **Quote TTL** — change `BuiltinQuoteProvider` / quote issuance from **1 hour** to **5 minutes**; env `MYCELIUM_QUOTE_TTL_SEC` (default **300**). Update tests that assume 1h if any.

4. **Tests** — `tests/test_delivery_store.py`:
   - issue + get roundtrip
   - expiry after TTL
   - invalid/expired id returns None

5. **Docs** — one-line note in `mvr-redesign-program.md` or architecture if store path differs from program spec.

---

## Constraints

- **Do not edit `TODO.md`.**
- **Do not** change `EntityQuery`, graph nodes, or `entity_resolution` (M3–M4).
- **Do not** remove `entity_key` yet.
- Match `QuoteStore` persistence style (same network root / sqlite / json file pattern as quotes today).

---

## Verification

```bash
./bin/ci-local
```

---

## Output

`prompts/cursor/done/2026-06-13-1100-mvr-redesign-slice-m2/` with `output.md` (For Grok + Paul: queue M3).

Do not commit until review.

---

## Exit criteria

- DeliveryStore + 5m TTL shipped with tests
- Quote TTL 5m (breaking for long-lived quotes — document in output)
- Ready for M3 (`EntityQuery` models)