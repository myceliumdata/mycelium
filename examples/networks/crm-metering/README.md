# CRM metering demo network

Committed example with **`metering.enabled: true`** and **`payment.enabled: false`**. Same `seed.json` as `crm`; negotiation only (no settlement).

## Bootstrap

```bash
./bin/refresh-example-network crm-metering --yes
```

Default live root: `~/mycelium-networks/crm-metering` (registered as `crm-metering`).

## Paul Murphy arc (acceptance)

```bash
./bin/demo-metering-negotiation
```

Or manually (two-step):

```bash
# 1 — Resolve lookup (copy delivery_id from JSON)
uv run mycelium query --network crm-metering \
  --lookup-json '{"name":"Paul Murphy","employer":"Acme Corp"}'

# 2 — Quote (bind email into delivery scope)
uv run mycelium query --network crm-metering \
  --delivery-id d_xxxxxxxxxxxx --attributes email

# 3 — Accept (paste quote_id from step 2 JSON)
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
