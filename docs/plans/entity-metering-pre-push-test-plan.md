# Pre-push test plan — Entity metering (Slices 11–12)

**Paul (June 2026)** — Run before `git push origin main`.  
**Local state:** `main` is ahead of `origin` by Slice 11 commit + uncommitted Slice 12 + fix (commit those first).

---

## What you are validating

| Layer | Shipped locally | Default CRM behavior |
|-------|-----------------|----------------------|
| **Negotiation** (Slice 10–12) | `quote_required` → `quote_id` → work | `crm`: metering **off** |
| **Settlement seam** (Slice 11) | `pay_quote`, `payment_required` when payment on | `crm-metering`: payment **off** |
| **Test scaffolding** (Slice 12) | `crm-metering`, CLI flags, admin quote UI, demo script | `crm` unchanged |

**Not in scope for this push:** real x402, wallets, HTTP gateway (Settlement protocol — TODO).

---

## 0 — One-time setup

```bash
cd /path/to/mycelium
uv sync --all-extras
cp -n .env.example .env   # if needed; add OPENAI_API_KEY + TAVILY_API_KEY for live research
```

Refresh **both** networks (isolates metering demo from CRM demos):

```bash
./bin/refresh-example-network crm-seeded --yes
./bin/refresh-example-network crm-metering --yes
```

Confirm registry:

```bash
uv run mycelium network list
# expect: crm (default), crm-metering
```

---

## 1 — Automated gate (5 min)

Run first; must be green before manual testing.

```bash
uv run pytest tests/test_cli_metering_query.py \
  tests/test_entity_metering.py \
  tests/test_entity_payment.py \
  tests/test_admin_daemon.py \
  tests/test_example_network.py \
  tests/test_entity_research_gate.py \
  tests/test_entity_growth.py -q
```

**Pass:** ~60+ tests, 0 failures.

```bash
uv run ruff check src/main.py src/mycelium_admin/server.py bin/demo-metering-negotiation
```

---

## 2 — CRM regression (metering off)

Proves default demos are unchanged.

```bash
uv run mycelium query --network crm-seeded --entity-key "Nichanan Kesonpat"
```

| Check | Expected |
|-------|----------|
| `outcome` | `found` (or `assembled` if attrs requested) |
| `quote` | `null` |
| No `quote_required` | ✓ |

```bash
uv run mycelium query --network crm-seeded --entity-key "Andrea Kalmans" --attributes email
```

| Check | Expected |
|-------|----------|
| `outcome` | `assembled` (no quote gate) |
| Research may run | OK if API keys set |

---

## 3 — Negotiation: demo script (2 min) ★ start here

**Primary smoke** for Slice 12. Prints **Input** and **Output** per step (copy-paste friendly for MCP/CLI).

```bash
unset MYCELIUM_USE_SYNC_CHECKPOINTER
./bin/demo-metering-negotiation
```

| Check | Expected |
|-------|----------|
| Exit code | `0` |
| Each step | **Input:** `EntityQuery` JSON, then **Output:** `QueryResponse` JSON |
| Step 1 output `outcome` | `entity_validated` or `found` |
| Step 2 output `outcome` | `quote_required` + `quote` with `line_items`, `total_usd` |
| Step 3 **input** | includes `quote_id` from step 2 output |
| Step 3 output `outcome` | `assembled` |
| Final line | `Metering negotiation demo completed successfully.` |

**`--json-only`:** each step is one object: `{"step", "input", "output"}` (for scripting).

---

## 4 — Negotiation: CLI manual (5 min)

Three-step Paul Murphy arc; **you** read `quote_id` from step 2 JSON.

```bash
# 1 — Bind
uv run mycelium query --network crm-metering \
  --entity-key "Paul Murphy" --employer "Acme Corp"

# 2 — Quote
uv run mycelium query --network crm-metering \
  --entity-key "Paul Murphy" --employer "Acme Corp" --attributes email

# 3 — Accept (replace q_… with quote_id from step 2)
uv run mycelium query --network crm-metering \
  --entity-key "Paul Murphy" --employer "Acme Corp" --attributes email \
  --quote-id q_XXXXXXXXXXXX
```

| Step | Expected `outcome` |
|------|-------------------|
| 1 | `entity_validated` |
| 2 | `quote_required` |
| 3 | `assembled` |

**Optional:** `--provenance` on step 2 — quote should include `query_provenance` line item (higher `total_usd`).

---

## 5 — Negotiation: Admin UI (10 min)

**Default path** (Vite dev — no build):

```bash
./bin/restart-admin crm-metering
```

Open **http://127.0.0.1:5173/**

| Step | Action | Expected |
|------|--------|----------|
| 1 | Run query: Paul Murphy, employer Acme Corp, no attributes | Outcome badge: validated/found |
| 2 | Same + attribute `email` | Badge: **`quote_required`**; quote panel shows JSON, `quote_id`, line items |
| 3 | Click **Accept quote** | Badge: **`assembled`**; results appear |

**Check:** Overview or policy hints that metering is enabled (if shown).

Stop admin: Ctrl+C in restart-admin terminal (or kill :5173 / :8741).

---

## 6 — Negotiation: MCP (10 min, optional)

Restart MCP after refresh. Claude Desktop or terminal:

**Env** (example):

```json
"env": {
  "MYCELIUM_NETWORK": "crm-metering",
  "OPENAI_API_KEY": "...",
  "TAVILY_API_KEY": "..."
}
```

| Step | Tool | Payload |
|------|------|---------|
| 0 | `describe_network` | — |
| 1 | `query_entity` | `examples/networks/crm-metering/queries/01-bind.json` |
| 2 | `query_entity` | `02-quote-email.json` → copy `quote.quote_id` |
| 3 | `query_entity` | `03-accept-quote.json` with `<quote_id-from-step-2>` replaced |

| Check | Expected |
|-------|----------|
| Step 2 `outcome` | `quote_required` |
| Step 3 `outcome` | `assembled` |

---

## 7 — Settlement seam (optional, 5 min)

Only if you want to verify Slice 11 payment path. **Not** required for `crm-metering` push (payment off there).

Temporarily enable payment on a **throwaway copy** or use Python:

```bash
# Quick test via settle_quote in pytest already covers this; manual optional:
uv run pytest tests/test_entity_payment.py -v -k "mock_settle or payment_required"
```

For full MCP settlement loop: enable `metering.payment.enabled: true` on a test `network.json`, then `pay_quote` → `query_entity` + `quote_id`. Skip unless you are validating payment before push.

---

## 8 — Commit checklist (after tests pass)

```bash
# Commit Slice 12 + fix (if not already committed)
git add -A   # review diff first
git commit -m "Add metering negotiation test scaffolding (Slice 12).

crm-metering example, CLI bind/quote flags, admin quote accept UI,
bin/demo-metering-negotiation, and CLI/admin tests."

git commit -m "Fix metering negotiation scaffolding nits (Slice 12 fix).

Sync checkpointer in demo script; restart-admin as default admin path;
subprocess demo test; MCP queries README; demo script prints input/output."
# Or squash Slice 12 + fix into one commit if you prefer
```

Verify ahead of push:

```bash
git log origin/main..HEAD --oneline
git status
```

---

## 9 — Push gate

```bash
git push origin main
```

Only after sections **1–5** pass (6–7 optional).

---

## Quick reference — outcomes

| `outcome` | Meaning |
|-----------|---------|
| `quote_required` | Negotiation: accept quote (retry with `quote_id`) |
| `payment_required` | Settlement: call `pay_quote` first (payment.enabled) |
| `principal_required` | Missing billing principal for funding model |
| `assembled` | Work ran / attributes merged |

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Demo script fails step 2 with event-loop error | Pull Slice 12 fix; script must set `MYCELIUM_USE_SYNC_CHECKPOINTER` |
| No `quote_required` on crm-metering | `metering.enabled` false in live `network.json` — re-run refresh |
| Admin quote panel missing | Use `:5173` Vite dev, not stale `:8741` dist without rebuild |
| Step 3 hangs / slow | API keys for live research; or expect `researching` in message |
| MCP stale data | Restart MCP after `refresh-example-network` |