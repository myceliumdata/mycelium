# Review — baseball free-form derive on manifest miss (M4)

**Verdict:** **Approved + polish nits**  
**Reviewer:** Grok  
**Date:** 2026-06-19

## CI

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **579** smoke passed, ruff clean, admin-ui build ok |
| `./bin/smoke-baseball-e2e` | **13** scenarios (`ops_derive_mocked` ok) |
| M4 tests | `test_baseball_ops_derive.py` (2), `derive_on_miss_enabled` (3) |

## Delivery

`output.md` matches implementation. M4-scoped files complete; unrelated fuzzy dirty tree excluded from commit.

| File | Role |
|------|------|
| `warehouse_domains.json` | `derive_on_miss: true`; `derive_candidates` removed |
| `derive_resolve.py` | `derive_on_miss_enabled()` replaces `is_derive_candidate()` |
| `batting_specialist.py` | Manifest miss → derive when domain flag set |
| `categories.json` | `ops` → batting |
| `test_baseball_ops_derive.py`, fixtures, `test_derive_review.py` | M4 + unit gate |
| `bin/smoke-baseball-e2e` | `ops_derive_mocked` scenario |
| Hand-test doc | M4-1 row |

## Spec compliance

| Criterion | Result |
|-----------|--------|
| Remove `derive_candidates` whitelist | Pass |
| `derive_on_miss` domain gate | Pass |
| Reuse M3c pipeline unchanged | Pass |
| No new `EntityQuery` fields | Pass |
| Guinea pig `ops` mocked E2E | Pass |
| `career_avg` regression | Pass (existing tests) |
| Cache key = normalized label | Pass (unchanged) |

## Design critique

**Strong:** Minimal diff — one manifest flag and gate rename. Training wheels off without forking derive orchestration. `ops` is a good M4 guinea pig (multi-column rate, not in aliases).

**Nit:** `OPS_DERIVE_SOURCE` fixture returns constant `"0.900"` — fine for CI; does not exercise formula plausibility on fixture rows (unlike `career_avg` fixture math).

## Nits (non-blocking)

| # | Nit | Follow-up |
|---|-----|-----------|
| N1 | Live Aaron `ops` not CI-gated | Paul optional manual; expect career OPS ≈ **0.928** on full Lahman |
| N2 | Intent-hash / synonym labels (`batting_average` vs `career_avg`) | M4b per `output.md` |
| N3 | Pitching/bio `derive_on_miss` | Future domain flags when specialists ready |

## For Paul

- **Commit message:** `baseball: free-form derive on manifest miss (M4)`
- **Manual MCP test (`ops`):** clear batting storage; step 1 `requested_attributes: ["ops"]`, `provenance: true`; step 2 deliver — expect non-`N/A` with LLM `computation.inline` and `operator_audit` on first miss.