# Baseball franchise product specialist (M12) — output

## Summary

Shipped **`franchise_specialist`**: franchise-era team labels from `Teams` grouped by `franchID`, attr **`franchise_teams`** as compact JSON array. Uses same `product_common.run_product_team_specialist` shell as roster.

## Design (v1 — locked)

| Decision | Choice |
|----------|--------|
| Pattern | Product specialist via `franchise_team_labels()` |
| Data | `Teams.franchID` join — no `TeamsFranchises` table required for v1 |
| Attr | `franchise_teams` — sorted distinct team `name` values |
| Category | `franchise` (opt-in; registry team rows unchanged) |
| Provenance | `lahman.teamID`, `lahman.franchID`, `warehouse`, `computation.inline` |

## Files

| Area | Files |
|------|--------|
| Pack | `franchise_specialist.py`, `product_common.py`, `categories.json` |
| Tests | `tests/test_baseball_franchise_specialist.py` |
| Live gate | `bb-franchise-01` (phase `franchise`), anchor `franchise_team_labels_json` |

## Verification

```text
./bin/ci-local                              # 637 smoke passed
uv run pytest tests/test_baseball_franchise_specialist.py -m smoke -q
```

Live discovery (Brooklyn Dodgers): 8 franchise-era labels ending with Los Angeles Dodgers.

## For Grok + Paul

- Mark M12 franchise specialist shipped.
- Live gate: `./bin/gate-live baseball --phase franchise`.
- M10–M12 batch complete; next queued: M13 full warehouse ingest / program polish capstone.

## Suggested commit message

```
baseball: franchise team labels product specialist (M12)
```
