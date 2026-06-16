# Baseball network (Lahman)

Fan-facing **team** identities use **full canonical names** (e.g. `Brooklyn Dodgers`, `Los Angeles Dodgers` — different teams).

- **Not** franchise-level grouping by default (Brooklyn Dodgers ≠ Los Angeles Dodgers even if historians link franchises).
- **Nickname alone** (`Dodgers`) is ambiguous — require full name or return suggestions.
- **Player** identity uses display name + team name for bind disambiguation (any team the player appeared for may alias the same player).

Bootstrap discovers canonical team names from ingested background data per network policy — not hardcoded Lahman columns.