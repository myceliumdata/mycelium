# Output — registry + resolve polish nits (post 1900 / 2000 / 2100)

## Summary

Closed review nits from registry, closed-identity, and query-grain-router slices. Highest-impact fix: mocked email research in MCP batch roundtrip smoke (~30s → ~0.07s). Grain-aware partial fuzzy suggestions, cross-grain ambiguous messaging, router test gaps, baseball team-grain e2e, and doc/README polish.

**Recovery note:** Grok review Not Approved — P13 `apply_network_paths_monkeypatch` leaked baseball env via `apply_network_paths()` before `monkeypatch.setenv`. **Remedial:** removed `apply_network_paths(paths)`; helper now only sets env via monkeypatch (matches old private helper in `test_query_grain_router.py`). Re-run after **0800** is committed separately.

## Nits addressed

| ID | Status | Notes |
|----|--------|-------|
| P1 | Done | `test_registry_entity_to_match_omits_internal_registry_fields` |
| P2 | Done | `lahman_seed` sets `source_keys` on duplicate team bind |
| P3 | Done | Baseball README bind vs field alias wording |
| P4 | Dropped | Obsolete per prompt |
| P5 | Done | Provenance omission documented (`seed-bootstrap.md`, `add_field_alias` docstring) |
| P6 | Verified | `docs/seed-bootstrap.md` § Open vs closed identity present |
| P7 | Done | Grain-aware `_rank_bind_field_fuzzy_suggestions` / `_rank_name_suggestions`; router passes `grain=` |
| P8 | Done | `cross_grain_ambiguous` message in `responses.py` |
| P9 | Done | `seed-bootstrap.md` link valid |
| P10 | Done | Doc markdown fixed in `query-grain-router.md` |
| P11 | Done | Dodgers no-LLM, `chosen`, duplicate-id `not_found`, 0-hit alias retry |
| P12 | Done | `GrainDisambiguator \| None` on `resolve_target_step1` |
| P13 | Done (remedial) | `apply_network_paths_monkeypatch` — **no** `apply_network_paths()`; `runtime_env_field_names()` only |
| P14 | Done | `bin/smoke-baseball-e2e` team lookup + deliver (6 scenarios) |
| P15 | Done | `mock_email_research` + `register_contact_specialist`; batch MCP ~0.07s |

## Files changed (high level)

| Area | Change |
|------|--------|
| `entity_resolution.py` | Grain-aware fuzzy suggestion ranking |
| `query_grain_router.py` | Pass grain into partial fuzzy path |
| `responses.py` | `cross_grain_ambiguous` agent message |
| `target_resolve.py` | `GrainDisambiguator` type on step-1 |
| `entity_registry.py` | Provenance note on `add_field_alias` (P5 only — **not** 0800 `save_entity` changes) |
| `lahman_seed.py` | `set_source_keys` on duplicate team row |
| `network/paths.py` | `runtime_env_field_names()` |
| `tests/network_helpers.py` | `apply_network_paths_monkeypatch`, `mock_email_research`, `register_contact_specialist` |
| `tests/test_query_grain_router.py` | P11 tests + public path helper |
| `tests/test_mvr_target_public.py` | P15 fast batch MCP roundtrip |
| `tests/test_entity_store_evolution.py` | P1 public match guard |
| `bin/smoke-baseball-e2e` | Team-grain step-1 + step-2 scenarios |
| Docs / README | `query-grain-router.md`, `seed-bootstrap.md`, baseball README |

## Verification

| Check | Result |
|-------|--------|
| Env leak repro fix | `test_dodgers_…` + `test_shape_results_identity_summary` — **2 passed** |
| `./bin/ci-local` | **499** smoke passed, ruff green |
| P15 timing | `test_mcp_example_batch_fixture_roundtrip` ~0.07s |

## For Grok + Paul

- **Do not commit with 0800** — separate commits. Apply 0900 diff after 0800 lands on `main`.
- 0800 implementation is in git stash `0800-ready-for-grok-review` (or uncommitted 0800-only hunks).
- No commit (per workflow).

**Suggested commit message:**

```
chore(polish): registry/router nits and fast MCP batch smoke

Grain-aware partial fuzzy suggestions, cross-grain messages, router test
gaps, baseball team e2e, mock email research for batch MCP roundtrip.
```
