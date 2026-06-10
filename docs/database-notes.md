# Local database notes

## Current schema (Phase 1)

`data/mycelium.db` holds a single core table:

| Column | Type | Notes |
|--------|------|-------|
| `id` | TEXT PRIMARY KEY | Person identifier |
| `name` | TEXT NOT NULL | Display name |
| `employer` | TEXT | Optional |

Queries resolve people from `<network_root>/entities.json` via the entity registry (not auto-loaded into SQLite on query). Optional `seed.json` is imported at bootstrap only (`refresh-example-network`, `network create`). The legacy `mycelium seed` CLI subcommand was removed in the seed-elimination phase.

LangGraph checkpoints live under `<network_root>/checkpoints.sqlite` (see `MYCELIUM_CHECKPOINT_PATH` / network path resolver in `.env.example`).

## Legacy `data/mycelium.db` files

If you created `data/mycelium.db` **before** the schema simplification (task `2025-06-01-1700-clean-derivative-references`), your file may still have:

- Extra columns on `people`: `email`, `phone`, `title`, `extra_json`
- Old tables such as `derivative_datasets`, `derivative_records`, or embedding stubs

The current code expects only `id`, `name`, and `employer`. With an old file you may see SQL errors, missing columns, or confusing query results.

### What to do

**Development (simplest)** — delete the old database and restart:

```bash
rm -f data/mycelium.db
uv run mycelium query --entity-key "Nichanan Kesonpat" --network crm
```

The app recreates the schema. Re-run `./bin/refresh-example-network crm` if you need bootstrap entities imported.

**Preserve data manually** — export any rows you care about, then delete `data/mycelium.db` and re-import into the new three-column shape (id, name, employer only). There is **no** built-in migration tool in Phase 1.

**Checkpoints** — `data/checkpoints.sqlite` is independent. You can delete it if graph state from an older run causes issues; it does not affect registry or bootstrap seed data.

We do not ship automatic migrations yet. If you need long-term upgrade paths, track that as a follow-up task rather than expecting silent schema upgrades.
