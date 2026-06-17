# Review — strict lookup-key grain routing

**Verdict: Approved + polish nits**

## CI

| Step | Result |
|------|--------|
| `./bin/ci-local` | Pass — **500** smoke, 98 deselected; ruff clean; admin-ui build ok |
| `LANGCHAIN_TRACING_V2=false uv run pytest -m full -q` | **18 passed**, 580 deselected |
| `./bin/smoke-crm-e2e` | **7/7** scenarios |
| `./bin/smoke-baseball-e2e` | **6/6** scenarios (includes new team-grain paths) |

## Delivery

`output.md` matches diff: fan-out deleted (~960 lines), `infer_grain_from_lookup`, baseball `player`/`team` bind keys, 10 strict-routing smokes, ship gate + `bin/baseball-query` updated.

## Diff reviewed

| File | Notes |
|------|-------|
| `src/network/mvr.py` | `infer_grain_from_lookup` — exact key-set match; subset → `lookup_incomplete` |
| `src/agents/target_resolve.py` | Multi-grain → inference + single-grain; `resolve_id_all_grains` retained |
| **Deleted** | `query_grain_router.py`, `grain_disambiguation.py`, `test_query_grain_router.py` |
| `src/models/state.py` | `EntityQuery.grain` removed |
| `examples/networks/baseball/*` | Manifest, handler, guide, README |
| `tests/test_strict_grain_routing.py` | 10 scenarios, no `grain=` on queries |
| `bin/baseball-query`, `bin/smoke-baseball-e2e` | New keys + team scenarios |
| `docs/query-grain-router.md` | Rewritten — readable without fan-out context |

## Spec compliance

| Criterion | Result |
|-----------|--------|
| Strict routing table (`{player,team}` / `{team}` / `{player}` incomplete) | Pass |
| Remove fan-out + disambiguation LLM + `EntityQuery.grain` | Pass |
| Baseball bind rename `team` / `player`+`team` | Pass |
| Lahman handler + fixtures | Pass |
| Tests without `grain` arg on queries | Pass |
| CRM unchanged | Pass |
| Closed lazy field aliases preserved | Pass |
| bind_index fallback (1000) still works | Pass — Milwaukee test in strict routing |
| Ship gate doc | Pass |
| `docs/plans/baseball-example-program.md` update | **Miss** — see nits |

## Legacy / dual-path

CRM single-grain `create_pending` smoke passes. `DeliveryScope.grain` still set on delivery.

## Design critique

**Strong:** Deletes ~400 lines of confusing machinery; `infer_grain_from_lookup` is self-documenting. Disjoint keys (`team` vs `player`+`team`) make the baseball contract obvious. Stacks cleanly on slice 1000 bind_index fallback.

**Sub-optimal (non-blocking):** `infer_grain_from_lookup` uses exact key-set equality only — no fuzzy keys (intentional). Unknown extra keys → `not_found` rather than helpful error (acceptable).

## Nits

| ID | Item |
|----|------|
| P1 | `prompts/cursor/HOLD.md` still describes fan-out / `EntityQuery.grain` / team `name` key — update when clearing HOLD |
| P2 | `_resolve_single_grain_step1` docstring still says "explicit grain override" |
| P3 | `docs/plans/baseball-example-program.md` not updated for `player`/`team` bind vocabulary (prompt listed it) |
| P4 | `LookupSuggestion` docstring still mentions `cross_grain_ambiguous` |

## For Paul

- **Breaking:** Re-bootstrap required before ship gate (`refresh-example-network baseball --root /tmp/mycelium-baseball-benchmark --yes --no-default`).
- **Commit message:** `refactor(routing): strict lookup-key grain inference; remove fan-out and EntityQuery.grain`
- **Next:** Manual ship gate Checks 4–7 on fresh benchmark root.
- **Push:** local only until gate clear.