# Baseball program polish capstone — output

## Summary

Closed accumulated non-blocking nits from M5–M14 reviews: live gate alignment (bio + rate drift), test coverage gaps, roster scope cache, provenance scope rules, M14 doc/hygiene, and program doc sync. **648 smoke tests pass** via `./bin/ci-local`.

## Live gate

| Item | Result |
|------|--------|
| Scenario count | **27** (added `bb-bio-02`: `final_game` + `death_date`) |
| Rate drift helper | `rate_value_drift()` + `RATE_DRIFT_ATTRS` in `gate_runner.py` |
| Phases | `fielding`, `roster`, `franchise` in unit minimums |

Paul: run `./bin/gate-live baseball` on live root after `--sync-only` to confirm **27/27** on real Lahman.

## Nits addressed vs deferred

| Nit | Status | Notes |
|-----|--------|-------|
| M7 N1/N5 — bio gate `final_game` + `death_date` | ✅ | `bb-bio-02` in catalog |
| M8 N4 — shared rate drift helper | ✅ | `gate_runner.py` |
| M5 P1 — smoke `--with-pytest` note | ✅ | `examples/networks/baseball/README.md` |
| M7 N2–N4 — bio tests + fixture consolidation | ✅ | `test_baseball_bio_specialist.py` |
| M8 N1–N3 — ERA provenance + zero IPouts | ✅ | pitching smoke tests |
| M9 N1–N2 — scope in provenance only when scoped | ✅ | `warehouse_resolve.py` |
| M9 N4 — deliveries.json roundtrip assert | ✅ | `test_delivery_store.py` |
| M11 N1/N2 — roster scope cache keys | ✅ | `roster::1957` storage + cache isolation test |
| M10/M12 — live gate phase minimums | ✅ | unit test updated |
| M13 N1/N2 — LAHMAN_CSV_TABLE_COUNT + docs | ✅ | test + `seed-bootstrap.md` |
| M14 N1–N4 — hierarchy doc, derive_on_miss doc, deprecation, pending cleanup | ✅ | see code/docs |
| Framework — scoped provenance read | ✅ | `query_provenance.py` reads `attr::yearID` when delivery scope set |
| M5 P2 — `attendance` alias | ⏸ deferred | Not in manifest; skip per prompt |
| M11 N3 — `roster_count_1957_bro` anchor | ⏸ deferred | Optional; roster names gate sufficient |
| M12 N1 — TeamsFranchises label enrichment | ⏸ deferred | Optional polish |
| M13 N3 — bootstrap CLI ingest counts | ⏸ deferred | Optional |
| M14 N5 — mocked `resolve_derive_on_miss` test | ⏸ deferred | Optional |

## Key code changes

| Area | Change |
|------|--------|
| Live gate | `bb-bio-02`, `rate_value_drift`, pitcher drift uses shared helper |
| Roster | Scope-aware storage keys (`roster::1957`); provenance `scope_in_provenance` |
| Provenance | `yearID` only when resolve uses scope; framework reads scoped storage keys on deliver |
| Tests | Bio death_date, ERA zero IPouts, roster cache isolation, career_hr scope provenance |
| M14 polish | `pack_common` deprecation warning; `derive_resolve` docstring; hierarchy doc refresh |

## Verification

```text
./bin/ci-local    # 648 passed, 143 deselected
```

## For Grok + Paul

- Mark **baseball example program capstone** done; M1–M14 + polish complete.
- Update `TODO.md`: baseball program ready for **manual gate sign-off** (not demo-ready until bootstrap timing gate passes).
- Run `./bin/gate-live baseball` on live root — expect **27/27**.
- Optional: cold bootstrap timing (Test 10 / identity pass) if not recorded since `2280`.
- Suggested commit message:

```
polish(baseball): program capstone — gate alignment, test gaps, smoke parity
```
