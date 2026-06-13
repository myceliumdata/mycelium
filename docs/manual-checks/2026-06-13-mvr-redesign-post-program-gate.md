# Manual checks — MVR redesign post-program gate (M1–M10)

**Status:** ⏳ **PENDING** — run before `git push origin main`

**Context:** MVR redesign shipped locally (14 commits ahead of `origin`). Target two-step protocol on CLI, MCP, admin API, and admin UI. Automated coverage: `./bin/ci-local` (352 smoke).

**Prereqs:** From framework repo root; `uv sync` done; `.env` with keys if a check needs live research (noted below).

**Networks:** Use **clean deployed** live roots under `~/mycelium-networks/` (or your configured paths) — **not** `--network-dir examples/networks/…`. The committed example tree is source material only; queries need a full deployed root (seed imported, `entities.json`, DB, categories).

---

## 0 — Clean deploy (required before checks 1–6)

Wipe runtime state and recopy from `examples/networks/`:

```bash
./bin/refresh-example-network crm --yes
./bin/refresh-example-network crm-metering --yes
```

Confirm registration:

```bash
uv run mycelium network list
# expect: crm (default), crm-metering
```

**After refresh:**

- **Admin (check 4):** `./bin/restart-admin crm` — daemon must bind the refreshed root.
- **MCP (check 6):** restart the MCP server for `crm` so it picks up the clean network.

---

## Quick smoke (optional first)

```bash
./bin/ci-local
```

**Pass:** all steps green (352 smoke passed at last review).

---

## Check 1 — Free CRM: two-step identity deliver

Confirms step-1 `lookup_resolved` + step-2 `found`.

```bash
# Step 1 — copy delivery_id from JSON
uv run mycelium query --network crm \
  --lookup-json '{"name": "Nichanan Kesonpat", "employer": "1k(x)"}'

# Step 2 — paste delivery_id
uv run mycelium query --network crm \
  --delivery-id <delivery_id-from-step-1>
```

**Pass criteria:**

- Step 1: `outcome` = `lookup_resolved`, `total_matches` = 1, `results` = `[]`, `delivery.delivery_id` present
- Step 2: `outcome` = `found`, `results[0].name` = `Nichanan Kesonpat`

---

## Check 2 — Batch resolve + deliver (3 matches)

Confirms R9 batch deliver without attrs.

```bash
# Step 1
uv run mycelium query --network crm \
  --lookup-json '{"employer": "645 Ventures"}'

# Step 2
uv run mycelium query --network crm \
  --delivery-id <delivery_id-from-step-1>
```

**Pass criteria:**

- Step 1: `total_matches` = 3
- Step 2: `outcome` = `found`, `len(results)` = 3, distinct `id` values

---

## Check 3 — Metering arc: quote → deliver

Confirms metered step-1 quote + step-2 `assembled` on the **refreshed** `crm-metering` network. **Needs API keys** for email research.

```bash
# Step 1 — quote (attrs on step 1 only)
uv run mycelium query --network crm-metering \
  --lookup-json '{"name": "Paul Murphy", "employer": "Acme Corp"}' \
  --attributes email

# Step 2 — deliver with quote_id + delivery_id from step 1 JSON
uv run mycelium query --network crm-metering \
  --delivery-id <delivery_id> --quote-id <quote_id>
```

**Pass criteria:**

- Step 1: `outcome` = `quote_required`, `quote.quote_id` and `delivery.delivery_id` present
- Step 2: `outcome` = `assembled`, `results[0].email` populated (or note if keys missing)

**Shortcut (uses deployed crm-metering via default network in script):**

```bash
./bin/demo-metering-negotiation --network crm-metering
```

**Pass:** exits 0; final step `assembled`.

---

## Check 4 — Admin UI two-step

Confirms M10 admin-ui migration (P22) against the **deployed** CRM network.

```bash
./bin/restart-admin crm
```

Open **http://127.0.0.1:5173/** → **Run query**:

1. Name `Nichanan Kesonpat`, employer `1k(x)` → **Run** → expect `lookup_resolved`; `delivery_id` auto-fills
2. Clear name/employer (or leave them) → **Run** again with only `delivery_id` → expect `found`

**Pass criteria:**

- No request errors about `entity_key`
- Step 2 shows identity in results table

---

## Check 5 — Legacy CLI rejected (optional)

Confirms public gate on deployed CRM.

```bash
uv run mycelium query --network crm \
  --entity-key "Nichanan Kesonpat" 2>&1 || true
```

**Pass:** exits non-zero or prints migration error (legacy flags removed).

---

## Check 6 — MCP target protocol (optional)

Restart MCP for **crm** after section 0 refresh. Then:

**Step 1** `query_entity`:

```json
{
  "lookup": {"name": "Andrea Kalmans", "employer": "Lontra Ventures"}
}
```

**Step 2** (paste `delivery_id` from step 1):

```json
{
  "delivery_id": "d_…"
}
```

**Pass:** step 1 `lookup_resolved`; step 2 `found` with Andrea in `results`.

Fixture reference (payload shape only): `examples/networks/crm/queries/`.

---

## When done

1. Change **Status** at top to **✅ CLEAR** (with date), or tell Grok “MVR gate clear.”
2. Push when ready: `git push origin main` (Paul or Grok on request).
3. Proceed to Program 2 lock — [`next-chunk-prep.md`](../plans/next-chunk-prep.md).

---

*Created: 2026-06-13 · Updated: use clean deployed networks (refresh-example-network)*