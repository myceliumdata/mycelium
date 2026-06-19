# M4 output — free-form derive on manifest miss

## Done

- **`warehouse_domains.json`** — batting `derive_on_miss: true`; removed `derive_candidates` whitelist.
- **`derive_resolve.py`** — `derive_on_miss_enabled(manifest, domain)` replaces `is_derive_candidate()`.
- **`batting_specialist.py`** — any manifest miss on batting domain invokes M3c `generate_and_run_derive()`.
- **`categories.json`** — `ops` → batting in `attribute_map` and category examples.
- **Tests** — `OPS_DERIVE_SOURCE` fixture; `test_baseball_ops_derive.py`; `derive_on_miss_enabled` unit tests.
- **Smoke** — `ops_derive_mocked` scenario (13 scenarios total).

## Locked behavior

| Case | Behavior |
|------|----------|
| Manifest alias hit (`career_hr`, etc.) | M2 resolve path — no LLM |
| Manifest miss + `derive_on_miss` | Full M3c derive pipeline for any owned batting label |
| Cache key | Normalized requested label (e.g. `ops`, `career_avg`) |
| Guinea pig | `ops` → mocked **0.900** on fixture |

## Verification

```text
uv run pytest tests/test_baseball_career_avg_derive.py tests/test_baseball_ops_derive.py tests/test_derive_review.py -q  # 15 passed
./bin/ci-local                    # 579 smoke passed
./bin/smoke-baseball-e2e          # 13 scenarios
```

## Manual (Paul)

Optional live `ops` on Hank Aaron (requires `OPENAI_API_KEY`, clear batting cache first). **Not run in CI.**

## For Grok + Paul

- M4 v1 complete; mark slice done on roadmap.
- Recommend **M4b**: intent-hash / label normalization (`career_avg` vs `batting_average` synonym dedup).

## Suggested commit message

```
baseball: free-form derive on manifest miss (M4)
```
