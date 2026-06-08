# CRM example network

Committed **reference network** for the Mycelium framework. Refresh it to a path you own, register it, and query.

This example ships **`seed.json`** and **`network.json`** only (plus this README and maintainer `prepare_seed.py`). Runtime artifacts — `categories.json`, `agent_registry.json`, `agents/`, `specialists/`, DB, checkpoints — are created under your `network_root` on first query.

The current `seed.json` is a small public-safe subset (15 people) including demo names used in docs and tests (`Nichanan Kesonpat`, `Andrea Kalmans`, ambiguous `Kevin Zhang` pairs).

## Quick start

From the framework repo root:

```bash
# Bootstrap or reset live CRM (default ~/mycelium-networks/crm; registers as default)
./bin/refresh-example-network crm

# Query via registered name or default
uv run mycelium query --network crm --entity-key "Nichanan Kesonpat"
uv run mycelium query --entity-key "Andrea Kalmans"
```

Custom live root:

```bash
./bin/refresh-example-network crm --root ~/mycelium-networks/crm --yes
```

Before demos, run refresh with `--yes` to wipe stale specialist research, then **restart MCP** and use fresh `thread_id` values per attribute.

Check network state before and after demo queries:

```bash
uv run mycelium network status --network crm
uv run mycelium network status --network crm --verbose   # debug layout
uv run mycelium network status --network crm --entity "Andrea Kalmans"
```

## Layout

```
<your-network_root>/
  network.json      # optional metadata (copied from this example)
  seed.json         # people array (name + employer only)
  categories.json   # runtime — created on first query (see docs/examples/sample-categories.json)
  agent_registry.json
  specialists/      # generated *_specialist.py
  agents/<category>/
  checkpoints.sqlite
  mycelium.db
```

## Categories taxonomy (documentation sample)

To see what `categories.json` typically contains before your first query, open **[`docs/examples/sample-categories.json`](../../../docs/examples/sample-categories.json)**.

## Full prototype CRM data

The larger prototype seed (`data/seed.json`, `seed_crm.json`, `raw_data.json`) was removed from the default framework clone in Phase 4. Retrieve from git tag **`prototype`** if you need the full historical dataset:

```bash
git show prototype:data/seed.json > /tmp/full-seed.json
```

`prepare_seed.py` in this directory documents the name+employer transform for maintainers extending the example.
