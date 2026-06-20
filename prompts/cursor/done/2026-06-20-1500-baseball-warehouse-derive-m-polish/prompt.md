# Baseball warehouse derive M-track polish

> **READY** — Claim per `prompts/cursor/WORKFLOW.md`.

**Objective:** Close non-blocking nits from M3–M4b reviews. No new features; behavior preserved except where noted.

**Do not edit `TODO.md`.**

---

## Scope (must implement)

| # | Nit | Source |
|---|-----|--------|
| **P1** | Skip intent LLM on 2nd synonym when derive cache already under shared slug | M4b review P3 |
| **P2** | Intent-map-aware legacy storage read (pre-M4b per-label rows) | M4b gate caveat |
| **P3** | `intent_dedup_mocked` scenario in `bin/smoke-baseball-e2e` | M4b review P2 |
| **P4** | Confirm `test_birth_date_missing_birth_month_na` asserts `N/A` only; tighten if still loose | M1c polish review |

**Out of scope:** M5 `question` field, pitching `derive_on_miss`, semantic-review env toggle (defer), live Aaron `ops` manual gate.

---

## P1 — Intent LLM skip when slug cache + map already warm

**Today:** `career_avg` derive → map + storage under `career_batting_average`. `batting_average` still calls intent LLM (`intent_calls == 2` in `test_baseball_intent_dedup.py`).

**Target:** Second synonym deliver uses **storage-informed map warmup** without intent LLM when safe.

### Suggested approach (`batting_specialist.py` derive branch)

Before `resolve_intent_slug()` when `lookup_intent_slug(requested_key, intent_map)` is **None**:

1. Collect slugs `S` where:
   - `record.get(S)` has a computed value (`field_has_value`), and
   - `S` appears as a value in `intent_map` (at least one label already maps to `S`).
2. If **exactly one** such slug `S`, treat as intent slug:
   - `save_intent_mapping(paths, requested_key, S)`
   - update in-memory `intent_map`
   - skip intent LLM
3. If zero or multiple candidates → call `resolve_intent_slug()` as today.

**Safety:** Multiple distinct derive slugs with storage + map entries → still use LLM (do not guess).

### Tests

Update `tests/test_baseball_intent_dedup.py`:

- After `career_avg` then `batting_average`, assert `intent_calls == 1` (was 2).
- Add unit test for multi-slug case: two derive slugs cached → second new label still invokes intent LLM (mock counter).

Optional helper in `src/network/intent_normalization.py` or `intent_map.py` (e.g. `infer_slug_from_warm_cache(...)`) — keep framework-owned if extracted.

---

## P2 — Legacy read across intent aliases

**Today:** Legacy fallback only checks `record.get(requested_key)` when `intent_slug != requested_key`. Pre-M4b row under `career_avg` is missed when client asks for `batting_average`.

**Target:** After resolving `intent_slug`, before derive, check **all labels** that map to that slug in `intent_map` plus `requested_key` and `intent_slug` itself.

```python
# Pseudocode — implement in batting_specialist derive branch
def _legacy_entries_for_intent(record, requested_key, intent_slug, intent_map):
    keys = {requested_key, intent_slug}
    keys.update(label for label, slug in intent_map.items() if slug == intent_slug)
    for k in keys:
        entry = record.get(k)
        if field_has_value(entry) or field_is_na(entry):
            yield k, entry
```

Use first hit for deliver under `requested_key`. Do **not** migrate legacy rows to slug in v1 (read-only).

### Tests

New test in `test_baseball_intent_dedup.py` or `test_intent_normalization.py`:

- Seed storage with value under `career_avg` only (no slug row).
- Deliver `batting_average` with mocked intent mapping to `career_batting_average`.
- Assert cache hit, no codegen, correct value under `batting_average` in results.

---

## P3 — Smoke: `intent_dedup_mocked`

Mirror `career_avg_derive_mocked` / `ops_derive_mocked` in `bin/smoke-baseball-e2e`:

1. `_patch_intent_dedup_mock(root)` — mock intent LLM + derive codegen (reuse `baseball_derive_fixtures.CAREER_AVG_DERIVE_SOURCE` + `IntentProposal`).
2. Scenario: deliver `career_avg` then `batting_average` on same fixture player.
3. Assert both `0.500`, shared value, `intent_slug` in provenance on second, **no second codegen** (track call count on mock).

Expect **14** scenarios (was 13).

---

## P4 — Bio missing-month test

Read `tests/test_baseball_bio_specialist.py::test_birth_date_missing_birth_month_na`. If assertion is already strict `N/A` only, note in `output.md` — no change. If it still accepts `pending` or other states, tighten to `N/A` only.

---

## Docs

- `docs/manual-checks/2026-06-19-baseball-m4b-intent-normalization-gate.md` — note P1/P2 code fixes reduce manual cache-clear requirement (still recommend clear on upgrade).
- `prompts/cursor/done/2026-06-20-1200-baseball-intent-normalization-m4b/review.md` — optional one-line note in `output.md` that P2/P3 addressed by this slice (do not edit review.md unless Grok asks).

---

## Verification

```bash
./bin/ci-local
./bin/smoke-baseball-e2e
uv run pytest tests/test_baseball_intent_dedup.py tests/test_intent_normalization.py tests/test_intent_map.py tests/test_baseball_bio_specialist.py -q
```

---

## For Grok + Paul (`output.md`)

- Scenario count after smoke change
- `intent_calls` before/after on dedup test
- Suggested commit: `polish(baseball): M-track derive intent cache + legacy alias reads`