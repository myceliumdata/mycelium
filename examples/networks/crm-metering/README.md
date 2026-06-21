# CRM metering demo network

**Operator guides:** [`docs/examples/crm-metering/`](../../../docs/examples/crm-metering/getting-started.md)

Committed example with **`metering.enabled: true`** and **`payment.enabled: false`**. Same `seed.json` and bootstrap handler as `crm-seeded` (`network.json` → `bootstrap`: `DefaultSeedHandler`); negotiation only (no settlement).

## Bootstrap

```bash
./bin/refresh-example-network crm-metering --yes
```

Refresh copies `network.json`, `seed.json`, and `guide.md`, then runs `DefaultSeedHandler` to import 15 seed people into `entities.json`.

Default live root: `~/mycelium-networks/crm-metering` (registered as `crm-metering`).

**Live regression:** `./bin/gate-live crm-metering` auto-refreshes the live root before scenarios (`--no-refresh` to skip) — see [`docs/manual-checks/2026-06-20-live-gate-program.md`](../../../docs/manual-checks/2026-06-20-live-gate-program.md).

## Paul Murphy arc (acceptance)

```bash
./bin/demo-metering-negotiation
```

Or manually (two-step):

```bash
# 1 — Resolve lookup (copy delivery_id from JSON)
uv run mycelium query --network crm-metering \
  --lookup-json '{"name":"Paul Murphy","employer":"Acme Corp"}'

# 2 — Quote (lookup + attributes → quote_required)
uv run mycelium query --network crm-metering \
  --lookup-json '{"name":"Paul Murphy","employer":"Acme Corp"}' --attributes email

# 3 — Accept (paste delivery_id and quote_id from step 2 JSON)
uv run mycelium query --network crm-metering \
  --delivery-id d_xxxxxxxxxxxx --quote-id q_xxxxxxxxxxxx
```

Step 3 needs `OPENAI_API_KEY` and `TAVILY_API_KEY` in `.env` for live email research (or use mocked research in tests).

## MCP fixtures

See **[`queries/README.md`](queries/README.md)** for the 3-step table and placeholder instructions.

## Admin UI

**Default (dev stack — no build):**

```bash
./bin/refresh-example-network crm-metering --yes
./bin/restart-admin crm-metering
```

Open **http://127.0.0.1:5173/** (Vite proxies to the admin API). Use **Run query** → lookup (name + employer) → request attributes → **Accept quote** when `quote_required` appears.

**Alternate (single-process demo):** requires a built SPA first:

```bash
cd admin-ui && npm run build
./bin/restart-admin crm-metering --demo
```

Then open **http://127.0.0.1:8741/**. Do not commit `admin-ui/dist/` — the dev stack above is the operator default.
