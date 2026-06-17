# Review — 2026-06-18-0900-registry-source-keys-polish-nits

**Verdict: Approved**

---

## CI

| Step | Result |
|------|--------|
| `./bin/ci-local` (Grok, post-stash + remedial) | **Pass** |
| smoke pytest | **500 passed**, 100 deselected |
| ruff | clean |
| `bin/smoke-baseball-e2e` | **6/6** pass |

Env-leak repro (P13 remedial):

```bash
uv run pytest tests/test_query_grain_router.py::test_dodgers_two_hits_one_grain_no_llm_via_resolve_target_step1 \
  tests/test_result_shape.py::test_shape_results_identity_summary -m smoke -q
# 2 passed
```

Prior **Not Approved** (env leak) resolved — `apply_network_paths_monkeypatch` uses **monkeypatch only** (no `apply_network_paths()`).

---

## Delivery vs prompt

| ID | Status |
|----|--------|
| P1 | ✅ Public match guard test |
| P2 | ✅ Team duplicate `set_source_keys` |
| P3 | ✅ Baseball README |
| P4 | ✅ Dropped |
| P5 | ✅ Provenance doc + `add_field_alias` docstring |
| P6 | ✅ `identity_mode` in seed-bootstrap |
| P7 | ✅ Grain-aware fuzzy partial lookup |
| P8 | ✅ `cross_grain_ambiguous` message |
| P9 | ✅ Link valid |
| P10 | ✅ Doc markdown |
| P11 | ✅ Router test gaps (4 tests) |
| P12 | ✅ `GrainDisambiguator` type |
| P13 | ✅ Public path helper (env leak fixed) |
| P14 | ✅ Baseball team-grain e2e |
| P15 | ✅ Mock email research (~0.07s batch MCP) |

**16 files** changed; stacks cleanly on **0800** (`ff52422`) — `entity_registry.py` diff is P5 docstring only (0800 perf hunks preserved).

---

## Diff notes (non-blocking)

- `test_mock_disambiguation_chosen_single_entity` exercises disambiguator `chosen` contract with mock returning `team-brooklyn` — fine.
- `crm_public_env` registers contact specialist + mock research path — scoped to fixture; no global pollution after P13 fix.

---

## Next steps

- Grok commits (separate from 0800).
- Paul **Test 8c** timing gate still open on 0800 commit.
- Restore/drop obsolete stashes (`0800-ready-for-grok-review`, `polish-review`) when convenient.