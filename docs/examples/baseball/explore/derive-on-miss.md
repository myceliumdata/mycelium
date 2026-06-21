# Derive on miss (LLM codegen)

## What this demonstrates

When a requested attribute is **not** in the warehouse manifest and the domain has `derive_on_miss: true`, `WarehousePlayerStatSpecialist` runs **sandboxed LLM codegen** (`query_warehouse()` only). Batting, pitching, and fielding domains are enabled on the committed example.

## Prerequisites

```bash
# .env
OPENAI_API_KEY=…
MYCELIUM_COMPUTATION_CODEGEN_MODEL=gpt-4o
MYCELIUM_INTENT_NORMALIZATION_MODEL=gpt-4o-mini   # synonym dedup (M4b)
```

Fresh derive path: use a refreshed root or `./bin/gate-live baseball` (auto-refresh clears derive cache).

## How to test — CLI

```bash
# Batting — career average (derive)
uv run mycelium query --network baseball \
  --lookup-json '{"player":"Hank Aaron"}' \
  --requested-attributes career_avg

# Batting — OPS (unaliased label)
uv run mycelium query --network baseball \
  --lookup-json '{"player":"Hank Aaron"}' \
  --requested-attributes ops

# Pitching — Nolan Ryan WHIP (after refresh; player lookup)
uv run mycelium query --network baseball \
  --lookup-json '{"player":"Nolan Ryan"}' \
  --requested-attributes career_whip
```

Step 2 with `delivery_id` after each step 1.

## How to test — MCP

```json
{
  "lookup": { "player": "Hank Aaron" },
  "requested_attributes": ["ops"]
}
```

## Expected output

| Attr | Player | Approximate value |
|------|--------|-------------------|
| `career_avg` | Hank Aaron | **0.305** |
| `ops` | Hank Aaron | **~0.928** (derived) |
| `career_whip` | Nolan Ryan | **~1.25** |

Step 2 `provenance.computation` shows inline codegen on first derive; repeat synonym (`batting_average`) may hit intent cache (M4b).

## Learn more

- [2026-06-19-baseball-m4-free-form-derive.md](../../../plans/conversations/2026-06-19-baseball-m4-free-form-derive.md)
- [2026-06-19-baseball-m4b-intent-normalization-gate.md](../../manual-checks/2026-06-19-baseball-m4b-intent-normalization-gate.md)
- Live gate: `bb-derive-01` … `bb-derive-08`