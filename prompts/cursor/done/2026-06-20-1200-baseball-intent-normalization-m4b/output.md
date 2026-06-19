# M4b output — intent normalization for derive cache dedup

## Done

- **`src/network/intent_map.py`** — `{network_root}/intent_map.json` load/save/lookup (atomic merge).
- **`src/network/intent_normalization.py`** — LLM intent slug resolution (`MYCELIUM_INTENT_NORMALIZATION_MODEL`), confidence 0.7, slug validation + retry, map persistence.
- **`src/network/warehouse_context.py`** — extracted shared `format_warehouse_context` (from pack derive).
- **`src/utils/llm_models.py`** — `intent_normalization_model()`.
- **`batting_specialist.py`** — derive-on-miss: resolve intent slug, cache read/write under slug, `values[requested_label]` on deliver; legacy read under requested key.
- **`derive_resolve.py`** — `provenance_parameters(..., intent_slug=)`.
- **`query_provenance.py`** — provenance read falls back to intent slug storage; rewrites `parameters.attribute` to requested label.
- **Tests** — `test_intent_map.py`, `test_intent_normalization.py`, `test_baseball_intent_dedup.py`.

## Locked behavior

| Topic | Behavior |
|-------|----------|
| Storage key | Intent slug only (e.g. `career_batting_average`) |
| Results key | Requested label (`career_avg`, `batting_average`) |
| Provenance | `parameters.attribute` = requested; `parameters.intent_slug` = slug |
| Dedup | Second synonym label hits slug cache — no second computation codegen |
| Intent LLM | Cheap model; separate from `MYCELIUM_COMPUTATION_CODEGEN_MODEL` |

## Verification

```text
uv run pytest tests/test_intent_map.py tests/test_intent_normalization.py tests/test_baseball_intent_dedup.py tests/test_llm_models.py -q  # 22 passed (subset)
./bin/ci-local                    # 580 smoke passed
./bin/smoke-baseball-e2e          # 13 scenarios
```

## Manual (Paul)

Clear batting `storage.json`, set `MYCELIUM_INTENT_NORMALIZATION_MODEL=gpt-4o-mini` and `MYCELIUM_COMPUTATION_CODEGEN_MODEL=gpt-4o` in `.env`. Deliver Aaron `career_avg` then `batting_average` — same value, no second codegen; check `intent_map.json` at network root.

## For Grok + Paul

- M4b v1 complete; mark slice done on roadmap.
- Paul: ensure both env vars set; clear batting cache before manual gate.

## Suggested commit message

```
baseball: intent normalization for derive cache dedup (M4b)
```
