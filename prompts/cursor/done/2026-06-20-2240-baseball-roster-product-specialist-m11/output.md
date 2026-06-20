# Baseball roster product specialist (M11) — output

## Summary

Shipped **`roster_specialist`** product specialist: scoped team roster from `Appearances` ⋈ `People`, delivered as JSON string array on attr **`roster`**. Shared helper `product_common.run_product_team_specialist` + `team_roster_names`. Requires `scope.yearID`; without scope returns N/A.

## Design (v1 — locked)

| Decision | Choice |
|----------|--------|
| Pattern | Product specialist (not warehouse manifest wrapper) |
| Attr | `roster` — compact JSON array of sorted display names |
| Scope | Required `yearID` for roster computation |
| Category | `team_roster` |
| Provenance | `lahman.teamID`, `yearID`, `warehouse`, `computation.inline` |

## Files

| Area | Files |
|------|--------|
| Pack | `roster_specialist.py`, `product_common.py`, `categories.json` |
| Tests | `tests/test_baseball_roster_specialist.py` |
| Live gate | `bb-roster-01` (phase `roster`), `contains` assertion on roster JSON |
| Assertions | `tests/live/assertions.py` — new `contains` path operator |

## Verification

```text
./bin/ci-local                              # 637 smoke passed
uv run pytest tests/test_baseball_roster_specialist.py -m smoke -q
```

## For Grok + Paul

- Mark M11 roster product specialist shipped.
- Live gate: `./bin/gate-live baseball --phase roster` (1957 BRO includes Hank Aaron).
- Anchor `roster_count_1957_bro: 35` retained for drift documentation; gate uses `contains` on player name.

## Suggested commit message

```
baseball: team roster product specialist with yearID scope (M11)
```
