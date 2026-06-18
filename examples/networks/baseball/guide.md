# Baseball network (Lahman)

Fan-facing **team** identities use **full canonical names** (e.g. `Brooklyn Dodgers`, `Los Angeles Dodgers` — different teams).

- **Not** franchise-level grouping by default (Brooklyn Dodgers ≠ Los Angeles Dodgers even if historians link franchises).
- **Bootstrap-only identity** — team and player record types never create new entities at query time. Unknown nicknames may resolve via **lazy field aliases** written on first 0-hit lookup.
- **Nickname alone** (`Dodgers`, `Bronx Bombers`) may map to one or many existing teams after alias expansion; multi-match is valid.
- **Player** identity uses `player` (display name) + `debut_team` + `debut_year` for bind disambiguation (one primary bind per Lahman `playerID` at bootstrap).

**Query keys:** `{player, debut_team, debut_year}` routes to player record type; `{player}` alone resolves when the name hits the registry (unique or homonym multi-match); unknown names return `not_found` on bootstrap-only player type. `{team}` routes to team record type. No `record_type` override on step 1.

Bootstrap discovers canonical team names and player debut binds from ingested background data per network policy — not hardcoded Lahman columns.
