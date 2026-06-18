# Baseball network (Lahman)

Fan-facing **team** identities use **full canonical names** (e.g. `Brooklyn Dodgers`, `Los Angeles Dodgers` — different teams).

- **Not** franchise-level grouping by default (Brooklyn Dodgers ≠ Los Angeles Dodgers even if historians link franchises).
- **Bootstrap-only identity** — team and player record types never create new entities at query time. Unknown nicknames may resolve via **lazy field aliases** written on first 0-hit lookup.
- **Full official team names** must match Lahman labels exactly (`Boston Red Sox`); partial strings like `Red Sox` alone do not resolve unless a real nickname alias exists.
- Strings that are not recognized nicknames and do not match catalog values → `not_found` (expansion returns empty; mashups like `Washington Red Sox` must not pollute aliases).
- **Nickname alone** (`Dodgers`, `Bronx Bombers`, `The Miracle Mets`) may map to one or many existing teams after alias expansion; multi-match is valid.
- **Player** identity uses `player` (display name) + `debut_team` + `debut_year` for bind disambiguation (one primary bind per Lahman `playerID` at bootstrap).

**Lazy alias expansion (LLM)** — domain nickname patterns for first 0-hit lookup:

| Query | Canonical match | Notes |
|-------|-----------------|-------|
| `Dodgers` | `Brooklyn Dodgers`, `Los Angeles Dodgers` | Multi-match OK |
| `Bronx Bombers` | `New York Yankees` | |
| `The Miracle Mets` | `New York Mets` | |
| `Washington Red Sox` | *(empty)* | Mashup — not a real nickname |
| `The Say Hey Kid` | `Willie Mays` | Player field; when listed |
| `Hammerin' Hank` | `Hank Aaron` | Player field; when listed |

Same mashup rule for `debut_team` nicknames (e.g. `Braves` may match multiple franchise-era rows when listed).

**Query keys:** `{player, debut_team, debut_year}` routes to player record type; `{player}` alone resolves when the name hits the registry (unique or homonym multi-match); unknown names return `not_found` on bootstrap-only player type. `{team}` routes to team record type. No `record_type` override on step 1.

Bootstrap discovers canonical team names and player debut binds from ingested background data per network policy — not hardcoded Lahman columns.
