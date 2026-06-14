# Empty-seed CRM example

Committed **reference network** with CRM MVR/bind rules but **no `seed.json`**. Contrast with [`../crm/`](../crm/), which ships a 15-person bootstrap fixture imported into `entities.json` on refresh.

## Quick start

```bash
./bin/refresh-example-network empty-crm --root ~/mycelium-networks/empty-crm --yes

# Step 1 — resolve lookup (issues delivery_id; create_on_deliver when 0 matches)
uv run mycelium query --network-dir ~/mycelium-networks/empty-crm \
  --lookup-json '{"name":"Paul Murphy","employer":"Acme Corp"}'

# Step 2 — deliver (paste delivery_id from step 1; creates the first registry row)
uv run mycelium query --network-dir ~/mycelium-networks/empty-crm \
  --delivery-id d_…
```

After refresh, `entities.json` is absent or empty — no bootstrap import runs. The first registry row is created on **step 2 deliver**, not step 1. Step 2 ensures MVR `name`/`employer` mappings exist in `categories.json` automatically before writing bind versions to specialist storage.

## Layout

```
<your-network_root>/
  network.json      # metadata (copied from this example)
  guide.md          # operator prose for visiting agents
  entities.json     # runtime — created on first bind/import
  categories.json   # runtime — created on first query
  ...
```

See `queries/` for copy-paste step-1 and step-2 `EntityQuery` payloads.
