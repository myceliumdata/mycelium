# Disable warm-cache intent inference — output

## Done

Removed unsafe `infer_slug_from_warm_cache` that bound unrelated labels (e.g. `ops`) to `career_batting_average` when only one mapped slug had warm storage.

| File | Change |
|------|--------|
| `batting_specialist.py` | Map miss → `resolve_intent_slug()` only; removed warm-cache block |
| `intent_map.py` | Deleted `infer_slug_from_warm_cache()` |
| `test_intent_map.py` | Removed warm-cache unit tests; kept round-trip + `labels_for_intent_slug` |
| `test_baseball_intent_dedup.py` | `intent_calls` 2 on synonym dedup; removed ambiguous warm-cache test; added `test_ops_after_career_avg_does_not_reuse_batting_slug` |

## Behavior change (accepted)

| Case | Before (M-polish P1) | After |
|------|----------------------|-------|
| `batting_average` after `career_avg` | `intent_calls == 1` (warm-cache skip) | `intent_calls == 2` (intent LLM on map miss) |
| `ops` after `career_avg` | Wrong slug → cached `0.305`/`0.500` | Distinct slug → correct ops value |
| Synonym codegen dedup | Unchanged — still 1 codegen via slug storage hit |

## Verification

```text
./bin/ci-local                                    # 600 smoke passed
uv run pytest tests/test_baseball_intent_dedup.py tests/test_intent_map.py -q  # 6 passed
./bin/refresh-example-network baseball --sync-only --yes --no-default
./bin/gate-live baseball --fresh-derive           # 15/15 passed
```

### Live gate (`bb-derive-02`)

- **ops** value matches anchor **≈ 0.928** (was **0.305** = career_avg bleed-through)
- Cleared poisoned cache: `agents/batting/storage.json`, `intent_map.json` via `--fresh-derive`

## For Grok + Paul

- Warm-cache P1 reverted; `intent_calls == 2` on synonym dedup is **accepted** per slice design.
- Paul: if live root still has `"ops": "career_batting_average"` in `intent_map.json` from a prior gate run, delete that mapping or re-run with `--fresh-derive`.
- Manual-check note: M4b gate caveat “Intent LLM on first synonym label” is accurate again (second synonym calls intent LLM; codegen still deduped).
- Next queued slice: `2026-06-20-2000-cli-delivery-id-network-hints.md`

## Suggested commit message

```
fix(baseball): remove warm-cache intent inference on map miss
```
