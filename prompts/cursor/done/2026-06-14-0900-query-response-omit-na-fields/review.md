# Review — QueryResponse omit N/A public JSON fields

**Verdict: Approved**

## CI

| Step | Result |
|------|--------|
| `./bin/ci-local` | Pass — ruff clean, admin-ui build ok, **392 smoke** passed, 26 deselected |

**Note:** First CI run failed on `test_example_crm_layout` — stray `examples/networks/crm/entities.json` in working tree (not introduced by slice code). Removed before re-run; green.

## Delivery

`output.md` matches diff. `public_dict()` outcome-aware omission in `src/models/state.py`; tests/docs/MCP description updated.

## Diff reviewed

| File | Read |
|------|------|
| `src/models/state.py` | Full `public_dict` + `_STEP1_PUBLIC_OUTCOMES` |
| `tests/test_mvr_entity_query_models.py` | Full new tests |
| `tests/test_mvr_target_deliver.py` | Step-2 `public_dict` assertions |
| `tests/test_mvr_target_public.py` | MCP/CLI quote omission |
| `tests/test_admin_daemon.py` | Admin wire JSON |
| `src/mycelium_mcp/server.py` | Schema description |
| `docs/architecture.md` | M9 paragraph |

## Spec compliance

| Exit criterion | Result |
|----------------|--------|
| `public_dict()` omits step-1 fields on `found` / `assembled` / `not_found` | Pass |
| Step-1 includes `total_matches` + `delivery` when set | Pass (spot-check: Road Runner repeat lookup) |
| Null `quote` / `provenance` omitted | Pass |
| Tests updated | Pass |
| `./bin/ci-local` green | Pass |
| `docs/architecture.md` updated | Pass |
| In-memory models unchanged | Pass |

## Design critique

**Strong**

- Single serialization point — matches `create_on_deliver` precedent.
- `_STEP1_PUBLIC_OUTCOMES` frozenset is clear and test-covered.
- `test_mvr_target_deliver` now uses `public_dict()` instead of `model_dump_json()` — tests the real wire shape.

**Minor (non-blocking)**

- Step-1 branch always `pop("provenance")` even if set; spec said omit when `None` only. No production path sets provenance on step 1 today.
- Minor breaking change for clients expecting explicit `null` — documented in `output.md`; acceptable.

## Nits

| # | Severity | Item |
|---|----------|------|
| 1 | Non-blocking | Optional gate-doc line: step-2 JSON no longer shows null `total_matches`/`delivery`. |
| 2 | Non-blocking | `examples/networks/crm/entities.json` keeps reappearing locally — watch `git status` before CI. |

## For Paul

- **Commit:** `fix: omit N/A QueryResponse fields in public JSON by outcome` (Grok committing now).
- **Manual gate:** Step-2 Road Runner JSON should no longer show `total_matches: null` — less confusing during Check 4/6.
- **Push:** Still local until you ask.