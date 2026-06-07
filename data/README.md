# Runtime network data (`data/`)

This directory is the **legacy prototype shim**: when no network is selected via CLI flags, env, or user config, Mycelium resolves `network_root` to `<framework>/data/`.

A fresh framework clone ships **without** committed seed or runtime files here. A bare `mycelium query` with no flags, env, or registry default will resolve to this directory and **fail** until `seed.json` exists (typically after bootstrap).

Bootstrap a network from the CRM example:

```bash
./bin/copy-example-network crm --root ./data --register --default
```

Or copy to a path outside the repo (recommended for real use):

```bash
./bin/copy-example-network crm --root ~/mycelium-networks/crm --register --default
```

## Gitignored at runtime

Created locally on first query (see `.gitignore`):

- `mycelium.db`, `checkpoints.sqlite`
- `categories.json` (runtime only — see [`docs/examples/sample-categories.json`](../docs/examples/sample-categories.json) for shape)
- `agent_registry.json`, `agents/` specialist storage

To rebuild runtime artifacts, use `mycelium network create --force` on the same root or bootstrap a new `network_root` (see README). To wipe local state, delete files under this directory manually.

## Historical CRM seed

Committed CRM seed files (`seed.json`, `seed_crm.json`, `raw_data.json`) were moved to **`examples/networks/crm/`** in Networks Phase 4. Full prototype data: `git show prototype:data/seed.json`.
