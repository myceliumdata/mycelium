# Empty-seed CRM example

Committed **reference network** with CRM MVR/bind rules but **no `seed.json`**. Contrast with [`../crm/`](../crm/), which ships a 15-person bootstrap fixture imported into `entities.json` on refresh.

## Quick start

```bash
./bin/refresh-example-network empty-crm --root ~/mycelium-networks/empty-crm --yes

# Bind Paul Murphy (creates the first registry row)
uv run mycelium query --network-dir ~/mycelium-networks/empty-crm \
  --entity-key "Paul Murphy" --employer "Acme Corp"
```

After refresh, `entities.json` is absent or empty — no bootstrap import runs. The first successful bind creates registry rows at query time.

## Layout

```
<your-network_root>/
  network.json      # metadata (copied from this example)
  guide.md          # operator prose for visiting agents
  entities.json     # runtime — created on first bind/import
  categories.json   # runtime — created on first query
  ...
```

See `queries/01-bind-paul-murphy.json` for a copy-paste `EntityQuery` payload.
