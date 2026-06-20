# Baseball fielding domain (M10) — output

## Summary

Shipped **fielding** warehouse domain: thin `fielding_specialist.py` wrapper on `pack_common.run_warehouse_player_graph`, `Fielding` in bootstrap tables, manifest aliases `career_games` / `career_putouts` (`career_sum` on `G` / `PO`), smoke tests, live gate **`bb-field-01`**, and drift checks.

## Design (v1 — locked)

| Decision | Choice |
|----------|--------|
| Specialist | Thin wrapper (same pattern as `pitching_specialist.py`) |
| Attributes | `career_games`, `career_putouts` via `career_sum` on Fielding |
| Scope | Career sums ignore `yearID` scope (same as batting/pitching) |
| Category | `fielding` in committed ontology |

## Files

| Area | Files |
|------|--------|
| Pack | `fielding_specialist.py`, `warehouse_domains.json`, `categories.json`, `lahman_common.py` |
| Fixture | `tests/baseball_minimal_fixture.py`, `bin/smoke-baseball-e2e` Fielding.csv |
| Tests | `tests/test_baseball_fielding_specialist.py` |
| Live gate | `bb-field-01` (phase `fielding`), anchors `fielder_*`, `gate_runner.py` drift |

## Verification

```text
./bin/ci-local                              # 637 smoke passed
uv run pytest tests/test_baseball_fielding_specialist.py -m smoke -q
```

Baseball catalog: **26** scenarios (was 23 after M9).

## For Grok + Paul

- Mark M10 fielding domain shipped in program slice map.
- Operator: refresh Lahman when Fielding table missing on live root — `./bin/refresh-example-network baseball --sync-only` (or `--yes` for full bootstrap).
- Live gate: `./bin/gate-live baseball --phase fielding` after refresh.
- Anchors: Hank Aaron `fielder_career_games=3298`, `fielder_career_putouts=21773` (discover via `./bin/gate-live baseball --discover` if drift).

## Suggested commit message

```
baseball: fielding warehouse domain and career G/PO attrs (M10)
```
