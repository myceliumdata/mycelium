# Review — bind-index fallback for step-1 full MVR lookup

**Verdict: Approved**

## CI

| Step | Result |
|------|--------|
| `uv sync --all-extras` | Pass |
| `admin-ui` build | Pass |
| `ruff` | Pass |
| smoke tests | **502 passed**, 100 deselected |

## Delivery

`output.md` claims match the diff: registry fallback, three new smoke tests, `seed-bootstrap.md` + ship gate Check 4 note. No missing implementation.

## Diff reviewed

| File | Notes |
|------|-------|
| `src/agents/entity_registry.py` | `lookup_by_target_lookup` — field index first, `bind_index` fallback on full MVR 0-hit |
| `tests/test_entity_store_evolution.py` | Primary + alias + partial (no fallback) |
| `tests/test_lahman_seed_handler.py` | Multi-team bootstrap → `lookup_by_target_lookup` both tuples |
| `tests/test_mvr_target_resolve.py` | Graph step-1 `lookup_resolved` on alias bind |
| `docs/seed-bootstrap.md` | Bind alias table note |
| `docs/manual-checks/2026-06-17-baseball-identity-ship-gate.md` | Check 4 Milwaukee optional pass |

## Spec compliance

| Criterion | Result |
|-----------|--------|
| Full MVR 0-hit → `bind_index` via `lookup_by_bind_values` | Pass |
| Partial lookup — no bind_index fallback | Pass |
| Field index hit unchanged | Pass |
| CRM regression (single grain) | Pass — fallback only on 0-hit full MVR |
| No fan-out / suggestion behavior change | Pass |
| Tests: registry + Lahman + graph | Pass |
| Docs | Pass |

## Legacy / dual-path

CRM and single-grain paths unchanged. Fan-out still benefits via shared `lookup_by_target_lookup` (problem 2 deferred to slice 1100).

## Tests

Coverage matches prompt: alias bind resolves at registry and graph layers; partial `team`-only does not use bind_index.

## Design critique

**Strong:** Minimal change at the correct layer — one registry method composes field index + bind_index. Fixes Milwaukee / multi-team without bootstrap or router edits.

**Sub-optimal (non-blocking):** Graph test still uses `EntityQuery.grain="player"`; slice 1100 will remove that. Ship gate Check 4 addendum still documents `grain` — update when 1100 lands.

## Nits

None blocking.

## For Paul

- **Commit message:** `fix(registry): step-1 full MVR lookup falls back to bind_index for alias binds`
- **Next:** Cursor slice `2026-06-18-1100-strict-grain-routing` (re-bootstrap required after merge)
- **Manual:** Milwaukee with `{name, team}` + `grain: player` on existing benchmark root (no reload for this slice alone)
- **Push:** local only until ship gate clear