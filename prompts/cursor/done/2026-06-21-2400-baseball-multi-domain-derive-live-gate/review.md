# Review — baseball multi-domain derive + live gate (2400)

**Verdict:** **Approved + polish nits**  
**Reviewer:** Grok  
**Date:** 2026-06-21

## Context

Post-reload slice: `derive_on_miss` on pitching + fielding, framework `domain=self.domain` fix, five derive live-gate scenarios with SQL-discovered anchors. Implemented in parallel with `2410` — shared catalog/anchor edits reviewed in both reviews.

## CI

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **655** smoke passed, ruff clean, admin-ui build ok |

## Delivery

`output.md` matches files on disk. Manifest flags, framework domain pass-through, derive audit hygiene, drift checks, pitching/fielding smoke tests, and gate scenarios `bb-derive-04` … `08` all present.

## Diff reviewed

| File | Read |
|------|------|
| `src/agents/specialists/warehouse_stat.py` | `domain=self.domain` in `resolve_derive_on_miss` |
| `examples/networks/baseball/specialists/derive_resolve.py` | `_derive_specialist_name`, audit lines |
| `examples/networks/baseball/warehouse_domains.json` | pitching + fielding `derive_on_miss` |
| `examples/networks/baseball/categories.json` | guinea-pig ontology routing |
| `examples/networks/baseball/README.md` | derive paragraph |
| `tests/test_baseball_pitching_derive.py` | Full |
| `tests/test_baseball_fielding_derive.py` | Full |
| `tests/test_warehouse_stat_specialist.py` | `test_resolve_derive_on_miss_passes_domain` |
| `tests/live/catalogs/baseball.yaml` | `bb-derive-04` … `08` |
| `tests/live/anchors/baseball_aaron_lahman_v2025.json` | Ryan/Aaron derive anchors |
| `tests/live/gate_runner.py` | `RATE_DRIFT_ATTRS` + drift discovery |
| `tests/test_live_gate_runner_unit.py` | Minimum 34 scenarios |
| `docs/manual-checks/2026-06-20-live-gate-program.md` | Count 34 |

## Spec compliance

| Criterion | Result |
|-----------|--------|
| Blocking fix: `domain=self.domain` | Pass |
| Framework unit test for domain arg | Pass |
| `derive_on_miss: true` pitching + fielding only | Pass |
| No manifest aliases for guinea-pig attrs | Pass |
| No bio / team derive | Pass |
| `bb-derive-04` … `08` with anchors + tolerances | Pass |
| `bb-derive-08` synonym / intent pattern | Pass |
| `bb-pitch-03` / `career_era` manifest regression | Pass — `test_career_era_still_manifest_when_derive_on_miss_enabled` |
| Discovery SQL documented in `output.md` | Pass |
| Drift checks for new attrs | Pass |
| Audit lines not hardcoded `batting_specialist` | Pass |
| Live gate count **34** (27 + 5 derive + 2 bio) | Pass |
| `./bin/ci-local` green | Pass |

## Legacy / dual-path

- Batting `derive_on_miss` unchanged.
- `career_era` still `career_era_weighted` manifest — derive flag on pitching does not steal manifest aliases.
- CRM unchanged.

## Tests

**Strong:** Mocked WHIP derive (pitching domain), fielding % derive, manifest `career_era` regression, framework domain capture test.

**Gaps (non-blocking):** No unit test for `bb-derive-08` intent_map behavior (live gate only). `rate_value_drift` helper still untested at unit level (program nit from 2350).

## Design critique

**Strong:** The `domain=self.domain` fix was blocking — without it pitching/fielding derive would have received batting warehouse context in prompts. Guinea-pig stats are baseball-meaningful and deliberately unaliased. `_derive_specialist_name` from manifest metadata is the right pack hygiene move.

**Sub-optimal (non-blocking):** Prompt §7 asked for `docs/manual-checks/2026-06-19-baseball-specialist-hand-test.md` derive rows — not updated (hand-test drift).

## Polish nits (non-blocking)

| Item | Note |
|------|------|
| Hand-test doc | Add pitching/fielding derive rows under derive section |
| `bb-derive-05` / `06` | No `provenance: true` on step1 (inconsistent with `04` / `08` — optional) |
| `bb-derive-08` first live run | May need `intent_map` entry `whip` → `career_whip` — re-run if synonym timestamp fails once |

## For Paul

- **Commit:** Combined with `2410` in one working tree.
- **Manual gate:** `./bin/gate-live baseball` with `OPENAI_API_KEY` + codegen model — derive phase; target **34/34**.
- **Note:** `fresh_derive_before_gate: true` clears derive cache; `bb-derive-08` depends on `bb-derive-04` provenance timestamp.
- **Push:** Local only until you request program push.