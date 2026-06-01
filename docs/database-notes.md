# Local database notes

## Current schema (Phase 1)

`data/mycelium.db` holds a single core table:

| Column | Type | Notes |
|--------|------|-------|
| `id` | TEXT PRIMARY KEY | Person identifier |
| `name` | TEXT NOT NULL | Display name |
| `employer` | TEXT | Optional |

On first run, the app creates this schema if needed and loads seed data from `data/seed_crm.json` when the database is empty.

LangGraph checkpoints live separately in `data/checkpoints.sqlite` (see `MYCELIUM_CHECKPOINT_PATH` in `.env.example`).

## Legacy `data/mycelium.db` files

If you created `data/mycelium.db` **before** the schema simplification (task `2025-06-01-1700-clean-derivative-references`), your file may still have:

- Extra columns on `people`: `email`, `phone`, `title`, `extra_json`
- Old tables such as `derivative_datasets`, `derivative_records`, or embedding stubs

The current code expects only `id`, `name`, and `employer`. With an old file you may see SQL errors, missing columns, or confusing query results.

### What to do

**Development (simplest)** — delete the old database and restart:

```bash
rm -f data/mycelium.db
uv run mycelium query --person-key "Nichanan Kesonpat"
```

The app recreates the schema and reloads seed data.

**Preserve data manually** — export any rows you care about, then delete `data/mycelium.db` and re-import into the new three-column shape (id, name, employer only). There is **no** built-in migration tool in Phase 1.

**Checkpoints** — `data/checkpoints.sqlite` is independent. You can delete it if graph state from an older run causes issues; it does not affect CRM seed data.

We do not ship automatic migrations yet. If you need long-term upgrade paths, track that as a follow-up task rather than expecting silent schema upgrades.
