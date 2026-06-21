# Empty-seed CRM example

**Operator guides:** [`docs/examples/crm-empty/`](../../../docs/examples/crm-empty/getting-started.md)

Committed **reference network** with CRM MVR/bind rules but **no `seed.json`**. Contrast with [`../crm-seeded/`](../crm-seeded/), which ships a 15-person bootstrap fixture imported into `entities.json` on refresh.

`network.json` still declares the framework bootstrap handler (`DefaultSeedHandler` via `network.bootstrap.handlers.default_seed`). On refresh the handler runs but commits **0** entities when `seed.json` is absent.

## Quick start

```bash
./bin/refresh-example-network crm-empty --root ~/mycelium-networks/crm-empty --yes

# Step 1 — resolve lookup (issues delivery_id; create_on_deliver when 0 matches)
uv run mycelium query --network-dir ~/mycelium-networks/crm-empty \
  --lookup-json '{"name":"Paul Murphy","employer":"Acme Corp"}'

# Step 2 — deliver (paste delivery_id from step 1; creates the first registry row)
uv run mycelium query --network-dir ~/mycelium-networks/crm-empty \
  --delivery-id d_…
```

After refresh, `entities.json` is absent or empty — no bootstrap import runs. The first registry row is created on **step 2 deliver**, not step 1. Step 2 ensures MVR `name`/`employer` mappings exist in `categories.json` automatically before writing bind versions to specialist storage.

**Live regression:** `./bin/gate-live crm-empty` auto-refreshes to an empty root before scenarios (`--no-refresh` to skip) — see [`docs/manual-checks/2026-06-20-live-gate-program.md`](../../../docs/manual-checks/2026-06-20-live-gate-program.md).

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
