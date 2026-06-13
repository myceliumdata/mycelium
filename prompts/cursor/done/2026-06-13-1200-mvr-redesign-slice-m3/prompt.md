# MVR redesign — Slice M3 (EntityQuery + outcomes)

**Program:** [`docs/plans/mvr-redesign-program.md`](../../docs/plans/mvr-redesign-program.md)  
**Prerequisite:** M2 reviewed and approved  
**Depends on:** M2 `DeliveryStore` (types only; graph may import but not issue yet)

---

## Objective

Update **`EntityQuery`** and **`QueryResponse`** models for the target protocol: `id`, `lookup`, `delivery_id`, `quote_id`; add **`lookup_resolved`** outcome and **`total_matches`** / **`delivery`** response fields. **Deprecate but do not remove** `entity_key` / `binding` from models yet if tests require — prefer parallel fields with validation docs, or remove if all call sites updated in this slice (minimal: models + schema + tests only; **no graph behavior change** unless required for compile).

**Default for M3:** models, MCP JSON schema, validation rules, unit tests — **graph still runs legacy path** until M4 unless a single gate forces dual-path. Document `protocol_mode` or keep legacy fields until M4 in code comments.

---

## Read first

- [`docs/plans/mvr-redesign-entity-query-examples.md`](../../docs/plans/mvr-redesign-entity-query-examples.md)
- [`src/models/state.py`](../../src/models/state.py)
- [`src/mycelium_mcp/server.py`](../../src/mycelium_mcp/server.py) — schema export
- M2: [`src/network/delivery.py`](../../src/network/delivery.py)

---

## Tasks

1. **`EntityQuery`** — add `id: str | None`, `lookup: dict[str, str]`, `delivery_id: str | None`; validate step-1 vs step-2 (step 2: only `delivery_id` + optional `quote_id`; step 1: no `delivery_id`). Keep or remove `entity_key`/`binding` per least-disruptive path for smoke tests.

2. **`QueryResponse`** — add `total_matches: int | None`, `delivery: dict | None` (or typed `DeliveryPayload` with `delivery_id`, `expires_at`). Add outcome **`lookup_resolved`**.

3. **MCP / CLI schema** — update `_neutral_json_schema` and CLI help text for target fields; mark legacy fields deprecated in field descriptions.

4. **Tests** — `tests/test_mvr_entity_query_models.py` or extend existing: step-1/step-2 validation, `lookup_resolved` serializes in `QueryResponse`.

5. **Docs** — one paragraph in architecture if model shape differs from examples doc.

---

## Constraints

- **Do not edit `TODO.md`.**
- **Do not** wire resolve/deliver graph nodes (M4–M5).
- **Do not** change `entity_resolution` behavior yet (M4/M7).

---

## Verification

```bash
./bin/ci-local
```

---

## Output

`prompts/cursor/done/2026-06-13-1200-mvr-redesign-slice-m3/` — queue M4 in For Grok + Paul.

Do not commit until review.

---

## Exit criteria

- Target query/response shapes in models + MCP schema
- `lookup_resolved` in outcome enum/docs
- Smoke green; runtime query path unchanged or explicitly dual-gated off