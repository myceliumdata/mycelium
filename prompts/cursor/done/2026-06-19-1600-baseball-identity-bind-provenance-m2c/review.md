# Review — baseball identity bind + warehouse parameters (M2c)

**Verdict:** **Approved + polish nits**  
**Reviewer:** Grok  
**Date:** 2026-06-19

## CI

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **569** smoke passed, ruff clean, admin-ui build ok |
| `uv run pytest tests/test_baseball_batting_specialist.py tests/test_baseball_bio_specialist.py tests/test_baseball_player_identity_specialist.py -q` | **12** passed |
| `./bin/smoke-baseball-e2e` | **10** scenarios passed |

## Delivery

`output.md` matches files on disk. Option **A** (pack `player_identity_specialist.py`) documented. Uncommitted.

## Spec compliance

| Criterion | Result |
|-----------|--------|
| `debut_team` / `debut_year` from registry bind, not research | Pass |
| Provenance actor `registry` or `seed_bootstrap` — not `research` | Pass |
| Rewrites cached `research` versions on deliver | Pass |
| Warehouse `parameters.warehouse` on batting/bio | Pass (M2b; unchanged) |
| No web research for bind fields | Pass |
| `TODO.md` untouched | Pass |

## Legacy / dual-path

Warehouse specialists unchanged. Factory stub replaced by pack specialist via `_install_pack_specialists` copy — correct for baseball roots.

## Tests

Bind deliver + provenance shape covered. Gap: no single-query multi-attr test (`debut_team` + `career_hr` + `birth_date`) — Paul hand-test doc calls this out; add in polish or manual gate only.

## Design critique

**Strong:** Minimal Option A; reads bind from graph context then registry fallback; research-contamination rewrite is pragmatic for roots that had factory storage; `actor_kind="registry"` on `write_fields` / `write_na_field` aligns with bind semantics; smoke asserts provenance with `provenance=true`.

**Sub-optimal (non-blocking):** Structural duplication with batting/bio specialists; `_write_registry_version` parallels `write_fields`; `player` bind not explicitly tested (only debut fields).

## Polish nits (non-blocking)

| # | Nit | Note |
|---|-----|------|
| C1 | No integration test for multi-attr deliver (`debut_team`, `career_hr`, `birth_date` + `provenance: true`) | One pytest or smoke row for hand-test gate automation. |
| C2 | `player` bind field not covered in identity tests | Trivial assert alongside debut fields. |
| C3 | Research rewrite only when cache has value + `actor.kind==research` | Document operator “clear agents/player_identity storage” if stale research persists without value match. |

**Queue:** Add C1–C2 to `2026-06-19-1700-baseball-warehouse-manifest-m2a-polish.md` (M2 polish after M2c). C3 doc note in hand-test optional.

## Diff reviewed

- `examples/networks/baseball/specialists/player_identity_specialist.py` (new)
- `tests/test_baseball_player_identity_specialist.py` (new)
- `bin/smoke-baseball-e2e`
- `prompts/cursor/done/2026-06-19-1600-baseball-identity-bind-provenance-m2c/` (`prompt.md`, `output.md`)

## For Paul

- **Commit message:** `baseball: registry bind attrs on deliver + full warehouse parameters (M2c)`
- **Commit scope:** M2c files above only.
- **Manual:** Full hand-test gate now — multi-attr query with `provenance: true`; confirm bind attrs not research, warehouse attrs have `parameters.warehouse`.
- **Next:** M2 polish slice (`1700`), then optional push when you’re satisfied with hand-test.
- **TODO.md:** Mark M2c done after commit (Grok/Paul).