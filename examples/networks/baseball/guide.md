# Baseball network (Lahman)

Fan-facing **team** identities use **full canonical names** (e.g. `Brooklyn Dodgers`, `Los Angeles Dodgers` — different teams).

- **Not** franchise-level grouping by default (Brooklyn Dodgers ≠ Los Angeles Dodgers even if historians link franchises).
- **Closed identity** — team and player grains never create new entities at query time. Unknown nicknames may resolve via **lazy field aliases** written on first 0-hit lookup.
- **Nickname alone** (`Dodgers`, `Bronx Bombers`) may map to one or many existing teams after alias expansion; multi-match is valid.
- **Player** identity uses display name + team name for bind disambiguation (any team the player appeared for may alias the same player via bind aliases at bootstrap).

Bootstrap discovers canonical team names from ingested background data per network policy — not hardcoded Lahman columns.
