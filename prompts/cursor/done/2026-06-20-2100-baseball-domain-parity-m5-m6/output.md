# Output — baseball domain parity M5–M6 (Grok ad-hoc)

## Summary

Shipped three pack specialists and manifest/resolver extensions so pitching and team-season attrs use the warehouse path (not factory research stubs). Multi-domain deliver (`career_hr` + `career_wins`) verified in smoke.

## Files

| Area | Files |
|------|--------|
| Specialists | `pitching_specialist.py`, `team_identity_specialist.py`, `team_season_specialist.py` |
| Resolver | `warehouse_resolve.py` — `_domain_table`, `team_latest_column`, `resolve_team_domain_attribute`, `team_provenance_parameters` |
| Manifest | `warehouse_domains.json` pitching + team_season aliases |
| Tests | `tests/baseball_minimal_fixture.py`, 3 new smoke test modules |
| Docs | `baseball-example-program.md` slice map, `TODO.md`, hand-test, README |
| Queue | M7–M13 prompts in `prompts/cursor/next/` |

## Verification

- `./bin/ci-local` — **621** smoke passed
- `./bin/smoke-baseball-e2e` — existing inline scenarios still pass; new domains covered via `--with-pytest`

## Operator

```bash
./bin/refresh-example-network baseball --sync-only
# restart MCP if running
```

## For Grok + Paul

- M5–M6 marked shipped in `TODO.md` (already updated).
- Cursor: pick up `2026-06-20-2200-baseball-bio-manifest-aliases-m7.md` next.
- Live gate pitching/team anchors — shipped 2026-06-20; manual gate doc sync folded into M8 prompt.

## Suggested commit

`feat(baseball): M5-M6 pitching, team_identity, team_season specialists` — **committed** as `b6db456`.