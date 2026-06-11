# Local database notes

## Identity (canonical)

Queries resolve people from `<network_root>/entities.json` via the entity registry. Optional `seed.json` is imported at bootstrap only (`refresh-example-network`, `network create` with `--seed`). The legacy `mycelium seed` CLI subcommand was removed in the seed-elimination phase.

## LangGraph checkpoints

Checkpoints live under `<network_root>/checkpoints.sqlite` (see `MYCELIUM_CHECKPOINT_PATH` / network path resolver in `.env.example`). This file is independent of identity.

## `mycelium.db` (optional)

`<network_root>/mycelium.db` may exist as an empty SQLite file for bootstrap compatibility (`get_storage()` ensures the path). **No `people` table** is created (removed June 2026). Identity is not read from this file.

### Legacy `data/mycelium.db` files

If you have an old `mycelium.db` from before the schema simplification, it may still contain a `people` table and extra columns (`email`, `phone`, etc.). Current code ignores that schema.

**Development (simplest)** — delete the old file if it causes confusion:

```bash
rm -f data/mycelium.db
```

Re-run `./bin/refresh-example-network crm` if you need bootstrap entities imported into `entities.json`.

**Checkpoints** — `checkpoints.sqlite` is independent. Delete it if graph state from an older run causes issues; it does not affect registry or bootstrap seed data.

We do not ship automatic migrations. Historical ingest/SQLite people APIs are documented in [`legacy-ingest-and-storage-reference.md`](legacy-ingest-and-storage-reference.md).
