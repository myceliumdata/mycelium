# CRM example network

Committed **reference network** for the Mycelium framework. Refresh it to a path you own, register it, and query.

This example ships **`seed.json`** (bootstrap fixture only — imported into `entities.json` on refresh), **`network.json`**, **`guide.md`**, and an optional reference **`specialists/contact_specialist.py`** (plus this README and maintainer `prepare_seed.py`). Runtime artifacts — `entities.json`, `categories.json`, `agent_registry.json`, `agents/`, additional `specialists/*.py`, DB, checkpoints — are created under your `network_root` on refresh or first query. `refresh-example-network` copies seed, network metadata, and guide; it does not copy `specialists/` (the committed reference is for inspection only).

For a **no-seed** growth demo, see [`../empty-crm/`](../empty-crm/).

Edit **`guide.md`** at your network root to tell visiting agents what this network is for (MCP `describe_network` returns it verbatim).

The current `seed.json` is a small public-safe subset (15 people) including demo names used in docs and tests (`Nichanan Kesonpat`, `Andrea Kalmans`, ambiguous `Kevin Zhang` pairs).

## Quick start

From the framework repo root:

```bash
# Bootstrap or reset live CRM (default ~/mycelium-networks/crm; registers as default)
./bin/refresh-example-network crm

# Step 1 — resolve by lookup (copy delivery_id from JSON output)
uv run mycelium query --network crm --lookup-json '{"name":"Nichanan Kesonpat"}'
uv run mycelium query --lookup-json '{"name":"Andrea Kalmans"}'

# Step 2 — deliver (paste delivery_id from step 1)
uv run mycelium query --network crm --delivery-id d_…
```

Custom live root:

```bash
./bin/refresh-example-network crm --root ~/mycelium-networks/crm --yes
```

Before demos, run refresh with `--yes` to wipe stale specialist research, then **restart MCP** and use fresh `thread_id` values per attribute.

### Browser admin UI

```bash
./bin/refresh-example-network crm --yes

# Single-process demo (built SPA at http://127.0.0.1:8741/)
cd admin-ui && npm install && npm run build
MYCELIUM_NETWORK=crm uv run mycelium-admin

# Dev mode (recommended): `./bin/restart-admin` from repo root
```

After demo queries populate storage, search **Andrea Kalmans** in the UI to see entity fields; overview cards mirror `mycelium network status` demo layout.

Check network state before and after demo queries:

```bash
uv run mycelium network status --network crm
uv run mycelium network status --network crm --verbose   # debug layout
uv run mycelium network status --network crm --entity "Andrea Kalmans"
```

## Network growth from queries

`seed.json` is imported into **`entities.json` at bootstrap only** (refresh/create). Queries read the registry. When a visiting agent binds a new person via step-1 `lookup` (for example `{"name":"Paul Murphy","employer":"Acme Corp"}`), Mycelium:

1. Creates a provisional row in `entities.json` (registry)
2. Runs core validation and promotes the row to `validated`
3. Step 2 with `delivery_id` invokes specialists for requested attributes (research gate: validated registry row)
4. Writes extended attributes under `agents/<category>/storage.json` keyed by `entity_id`
5. Records **data attribution** on the registry row: `attr_sources` (which category owns each attr) and `last_researched_at` (when research last succeeded)

Re-query the same `lookup` (or `id`) for step 1, then `delivery_id` for step 2. Specialist storage remains the source of truth for attribute values; registry metadata tracks provenance for operators and the admin UI.

Example MCP fixtures: [`queries/`](queries/) (batch deliver walkthrough).

## Layout

```
<your-network_root>/
  network.json      # optional metadata (copied from this example)
  guide.md          # author prose for visiting agents (edit freely)
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
