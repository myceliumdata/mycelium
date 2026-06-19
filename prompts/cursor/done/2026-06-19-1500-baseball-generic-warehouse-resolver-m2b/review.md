# Review — baseball generic warehouse resolver (M2b)

**Verdict:** **Approved + polish nits**  
**Reviewer:** Grok  
**Date:** 2026-06-19

## CI

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **567** smoke passed, ruff clean, admin-ui build ok |
| `uv run pytest tests/test_baseball_batting_specialist.py tests/test_baseball_bio_specialist.py -q` | **10** passed (6 batting + 4 bio) |
| `./bin/smoke-baseball-e2e` | **9** scenarios passed |

## Delivery

`output.md` matches files on disk. Implementation complete; uncommitted (exclude unrelated fuzzy drift at commit).

## Spec compliance

| Criterion | Result |
|-----------|--------|
| Generic resolver via manifest aliases (no per-attr `career_hr` branch) | Pass |
| `career_hr` / `career_rbi` / `career_hits` → `career_sum` on Batting | Pass |
| `birth_date` compose + raw People (`debut`, `bats`, `throws`, `birth_city`) aliases | Pass (wired; raw cols not fixture-tested) |
| `parameters`: `lahman.playerID` + `warehouse` | Pass |
| `career_hr==3`, `career_rbi==3`, `career_hits==4` on minimal fixture | Pass |
| `birth_date==1934-02-05` regression | Pass |
| Unknown / rate stats → `N/A` | Pass (via `resolve_domain_attribute` → None) |
| No web research | Pass |
| M2c / bind-field provenance | N/A — correctly deferred |
| `TODO.md` untouched | Pass |

## Legacy / dual-path

M1b/M1c provenance envelope preserved. `career_hr` provenance now uses shared `career_sum` inline (convention-level, not per-attr function) — acceptable per locked design.

## Tests

New batting tests for `career_rbi`/`career_hits` + provenance `warehouse` param. Smoke adds `career_rbi_routes_batting_specialist`. Gap: no bio raw-column deliver test (`bats`/`debut`) — optional per prompt, worth one fixture row in polish.

## Design critique

**Strong:** Clean layer-3 step — aliases in `warehouse_domains.json` flow into live manifest; `warehouse_resolve.py` is pack-only with three convention functions + `inspect.getsource`; specialists share one resolve loop; dynamic import keeps sibling `warehouse_resolve.py` working after `_install_pack_specialists` copy.

**Sub-optimal (non-blocking):** Identical `_load_warehouse_resolve()` duplicated in both specialists; provenance `parameters` omit resolved `attribute`/`column` (inline is generic `career_sum`); hand-test doc still lists `bats`/`height` as post-M2b N/A.

## Polish nits (non-blocking)

| # | Nit | Note |
|---|-----|------|
| P1 | Duplicate `_load_warehouse_resolve` in `batting_specialist.py` and `bio_specialist.py` | Move to `warehouse_resolve.py` or tiny `specialist_loader.py` in pack. |
| P2 | No test for bio raw-column alias path (`bats`, `debut`, `birth_city`) | Add People columns to minimal fixture + one deliver test. |
| P3 | Provenance `parameters` lack `attribute` (and column for career_sum) | Align with full-parameters policy; fold into M2c or polish. |
| P4 | Update hand-test doc “Should NOT work” — `bats`/`debut`/`birth_city` work when manifest + column present | Doc-only after M2b commit. |

**Queued:** `prompts/cursor/next/2026-06-19-1700-baseball-warehouse-manifest-m2a-polish.md` (M2a A1–A3 + M2b B1–B4, after M2c).

## Diff reviewed

- `examples/networks/baseball/specialists/warehouse_resolve.py` (new)
- `examples/networks/baseball/specialists/batting_specialist.py`
- `examples/networks/baseball/specialists/bio_specialist.py`
- `examples/networks/baseball/warehouse_domains.json`
- `tests/test_baseball_batting_specialist.py`
- `tests/test_baseball_bio_specialist.py` (provenance `warehouse` assert only)
- `bin/smoke-baseball-e2e`
- `prompts/cursor/done/2026-06-19-1500-baseball-generic-warehouse-resolver-m2b/` (`prompt.md`, `output.md`)

## For Paul

- **Commit message:** `baseball: manifest-driven warehouse resolver for career stats (M2b)`
- **Commit scope:** M2b files above only.
- **Manual after M2b:** `career_rbi`, `career_hits` on full Lahman; optional `bats` if People row populated.
- **Next:** **M2c** (`2026-06-19-1600-baseball-identity-bind-provenance-m2c.md`) — then full hand-test gate.
- **TODO.md:** Mark M2b done after commit (Grok/Paul).