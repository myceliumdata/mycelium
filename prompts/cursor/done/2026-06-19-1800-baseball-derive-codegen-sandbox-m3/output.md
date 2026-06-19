# M3 output — LLM derive codegen sandbox

## Done

- **`src/network/derive_sandbox.py`** — AST validation + restricted `run_derive_function` (`compute(player_id, warehouse)` only; `query_warehouse` + `Path` injected).
- **`examples/networks/baseball/specialists/derive_resolve.py`** — prompt builder, LLM codegen (`MYCELIUM_DERIVE_MODEL`, default `gpt-4o-mini`), sandbox run.
- **`warehouse_domains.json`** — `derive_candidates: ["career_avg"]` on batting domain.
- **`batting_specialist.py`** — after M2 alias miss, derive path for listed candidates; cache via `write_computed_field`.
- **Tests:** `test_derive_sandbox.py`, `test_baseball_career_avg_derive.py` (mocked LLM; cache hit on second deliver).

## Locked formats

| Context | Expected `career_avg` |
|---------|----------------------|
| Minimal fixture (H=4, AB=8) | **`0.500`** (three decimal places) |
| Full Lahman Aaron (manual) | ≈ **`0.305** |

## Approach

`derive_candidates` in manifest — only listed attrs invoke LLM on cache miss. M2 aliased attrs unchanged.

## Verification

```text
./bin/ci-local                    # 574 smoke passed
uv run pytest tests/test_derive_sandbox.py tests/test_baseball_career_avg_derive.py tests/test_baseball_batting_specialist.py -q
./bin/smoke-baseball-e2e          # 11 scenarios (career_avg pytest-only with mock)
```

## Manual (Paul)

Clear `agents/batting/storage.json` if stale `N/A` for `career_avg`, then deliver with `provenance: true` on live Lahman (requires `OPENAI_API_KEY`).

## Suggested commit message

```
baseball: LLM derive sandbox for career_avg (M3)
```
