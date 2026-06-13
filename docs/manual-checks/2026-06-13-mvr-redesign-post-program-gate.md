# Manual checks — MVR redesign post-program gate (M1–M10)

**Status:** ⏳ **PENDING** — run before `git push origin main`

**Context:** MVR redesign shipped locally (13 commits ahead of `origin`). Target two-step protocol on CLI, MCP, admin API, and admin UI. Automated coverage: `./bin/ci-local` (352 smoke).

**Prereqs:** From framework repo root; `uv sync` done; `.env` with keys if a check needs live research (noted below).

**Networks:** Use registered names (`crm`, `crm-metering`) if you have them, or `--network-dir examples/networks/<name>` for a self-contained run.

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
uv run mycelium query --network-dir examples/networks/crm \
  --lookup-json '{"name": "Nichanan Kesonpat", "employer": "1k(x)"}'

# Step 2 — paste delivery_id
uv run mycelium query --network-dir examples/networks/crm \
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
uv run mycelium query --network-dir examples/networks/crm \
  --lookup-json '{"employer": "645 Ventures"}'

# Step 2
uv run mycelium query --network-dir examples/networks/crm \
  --delivery-id <delivery_id-from-step-1>
```

**Pass criteria:**

- Step 1: `total_matches` = 3
- Step 2: `outcome` = `found`, `len(results)` = 3, distinct `id` values

---

## Check 3 — Metering arc: quote → deliver

Confirms metered step-1 quote + step-2 `assembled`. **Needs API keys** for email research on a cold network.

```bash
# Bootstrap metering example if needed
./bin/refresh-example-network crm-metering --yes

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
- Step 2: `outcome` = `assembled`, `results[0].email` populated (or sensible pending if keys missing — note in gate)

**Shortcut (mocked path):**

```bash
./bin/demo-metering-negotiation --network crm-metering
```

**Pass:** exits 0; final step `assembled`.

---

## Check 4 — Admin UI two-step

Confirms M10 admin-ui migration (P22).

```bash
./bin/restart-admin crm
# or: ./bin/restart-admin examples/networks/crm
```

Open **http://127.0.0.1:5173/** → **Run query**:

1. Name `Nichanan Kesonpat`, employer `1k(x)` → **Run** → expect `lookup_resolved`; `delivery_id` auto-fills
2. Clear name/employer (or leave them) → **Run** again with only `delivery_id` → expect `found`

**Pass criteria:**

- No request errors about `entity_key`
- Step 2 shows identity in results table

---

## Check 5 — Legacy CLI rejected (optional)

Confirms public gate.

```bash
uv run mycelium query --network-dir examples/networks/crm \
  --entity-key "Nichanan Kesonpat" 2>&1 || true
```

**Pass:** exits non-zero or prints migration error (legacy flags removed).

---

## Check 6 — MCP target protocol (optional)

If you use Claude Desktop / MCP for `crm`:

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

Fixture reference: `examples/networks/crm/queries/`.

---

## When done

1. Change **Status** at top to **✅ CLEAR** (with date), or tell Grok “MVR gate clear.”
2. Push when ready: `git push origin main` (Paul or Grok on request).
3. Proceed to Program 2 lock — [`next-chunk-prep.md`](../plans/next-chunk-prep.md).

---

*Created: 2026-06-13*