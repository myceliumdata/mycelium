# M-track polish output — derive intent cache + legacy alias reads

## Done

| Item | Change |
|------|--------|
| **P1** | `infer_slug_from_warm_cache()` in `intent_map.py`; batting derive skips intent LLM on 2nd synonym when exactly one mapped slug has storage |
| **P2** | `_legacy_derive_entry()` scans all labels mapping to `intent_slug` plus requested key and slug (pre-M4b per-label rows readable) |
| **P3** | `_patch_intent_dedup_mock()` + `intent_dedup_mocked` smoke scenario (career_avg → batting_average, one codegen) |
| **P4** | `test_birth_date_missing_birth_month_na` already asserts `== "N/A"` only — no code change |
| **Docs** | M4b gate doc updated: P1/P2 reduce routine cache-clear; still recommend clear on upgrade |

## Key metrics

| Metric | Before | After |
|--------|--------|-------|
| `intent_calls` on dedup test (`career_avg` → `batting_average`) | 2 | **1** |
| Smoke scenarios | 13 | **14** |

## Verification

```text
./bin/ci-local                    # 582 passed
./bin/smoke-baseball-e2e          # 14 scenarios (intent_dedup_mocked ok)
uv run pytest tests/test_baseball_intent_dedup.py tests/test_intent_normalization.py tests/test_intent_map.py tests/test_baseball_bio_specialist.py -q  # 15 passed
```

## For Grok + Paul

- M4b review nits P1–P4 closed; no new features.
- M4b `review.md` P2/P3 (smoke dedup + intent_calls) addressed by this slice.
- Paul: routine synonym delivers no longer need cache clear; clear batting storage + `intent_map.json` only when validating a fresh upgrade from pre-M4b roots.

## Suggested commit message

```
polish(baseball): M-track derive intent cache + legacy alias reads
```
