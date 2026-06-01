# Output: Legacy database guidance

## Where guidance was added

| Location | Role |
|----------|------|
| `docs/database-notes.md` | **Primary** — full legacy schema explanation and options |
| `README.md` | One-line link under Quick start pointing to database notes |
| `src/storage/core.py` | Module docstring pointer to `docs/database-notes.md` |

## Locations considered

- **README only** — Rejected as too long for quick start; link + dedicated doc is easier to maintain.
- **`.env.example`** — Out of scope; DB path is already documented there.
- **Migration code** — Explicitly out of scope per prompt.

## Guidance summary (see `docs/database-notes.md` for full text)

- Current schema: `people(id, name, employer)` only.
- Legacy files may have extra columns and `derivative_*` tables.
- **Dev fix:** `rm -f data/mycelium.db` then rerun a query to recreate + reseed.
- **Preserve data:** manual export/re-import; no built-in migration.
- Checkpoints file is separate and optional to delete.

## TODO.md

Marked complete: legacy `data/mycelium.db` documentation (`2025-06-01-1740-local-database-legacy-schema-note`).

## In-progress cleanup

Removed only `prompts/in-progress/2025-06-01-1740-local-database-legacy-schema-note.md` after claim.
