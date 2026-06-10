# Metering negotiation — test scaffolding (Slice 12)

**Status:** Shipped (Slice 12 — review pending)  
**Depends on:** Slice 10 + fix, Slice 11 + fix (negotiation + optional settlement seam)  
**Program:** [`entity-protocol-and-registry-program.md`](entity-protocol-and-registry-program.md)  
**Paul (June 2026):** Settlement protocol (real x402, wallets, HTTP gateway) is a **separate track** on `TODO.md` — not this slice.

---

## Objective

Make **priced-commit negotiation** (`quote_required` → `quote_id` → work) easy to exercise on all three operator surfaces:

| Surface | Today | After slice |
|---------|-------|-------------|
| **CLI** | No `binding`, `quote_id`, `provenance` | Full `EntityQuery` flags |
| **MCP** | Works; no guided demo | `bin/demo-metering-negotiation` + example queries |
| **Admin UI** | Bind employer only; no quote display/retry | Quote panel + accept + metering outcomes |

**Non-goals:** Real x402, payment UI beyond showing `payment_required` + message, rebate/pool, HTTP gateway.

---

## Locked deliverables

| # | Deliverable |
|---|-------------|
| S1 | **`examples/networks/crm-metering/`** — CRM clone with `metering.enabled: true`, `payment.enabled: false`; README with Paul Murphy arc |
| S2 | **CLI** — `mycelium query` flags: `--employer`, `--quote-id`, `--provenance`, optional `--binding-json` |
| S3 | **Admin API** — `AdminQueryRequest` + `/query` pass `quote_id`, `provenance`, optional `principal` |
| S4 | **Admin UI** — quote JSON panel, sticky `quote_id`, **Accept quote** button, outcome badges for `quote_required` / `payment_required` / `principal_required` |
| S5 | **`bin/demo-metering-negotiation`** — scripted Paul Murphy arc (bind → quote → accept); prints JSON each step; works against `crm-metering` |
| S6 | **Docs** — `README.md` “Testing negotiation” section; `examples/networks/crm-metering/README.md` |
| S7 | **Tests** — CLI binding+quote_id smoke; admin `/query` quote_id passthrough |

---

## Example network: `crm-metering`

```
examples/networks/crm-metering/
  seed.json          # same as crm (symlink or copy)
  network.json       # metering.enabled: true; payment.enabled: false
  guide.md           # note: metering demo network
  README.md          # hands-on runbook
  queries/           # optional JSON fixtures for MCP copy-paste
    01-bind.json
    02-quote-email.json
    03-accept-quote.json
```

Bootstrap:

```bash
./bin/refresh-example-network crm-metering
uv run mycelium network register crm-metering --root ~/mycelium-networks/crm-metering
```

CRM example (`crm`) keeps `metering.enabled: false` — demos unchanged.

---

## CLI (`src/main.py`)

Extend `mycelium query`:

```bash
# Bind
uv run mycelium query --network crm-metering \
  --entity-key "Paul Murphy" --employer "Acme Corp"

# Quote
uv run mycelium query --network crm-metering \
  --entity-key "Paul Murphy" --employer "Acme Corp" --attributes email

# Accept (paste quote_id from prior JSON)
uv run mycelium query --network crm-metering \
  --entity-key "Paul Murphy" --employer "Acme Corp" --attributes email \
  --quote-id q_abc123
```

Flags:

| Flag | Maps to |
|------|---------|
| `--employer` | `binding.employer` |
| `--binding-json` | full `binding` dict (overrides `--employer` if both) |
| `--quote-id` | `quote_id` |
| `--provenance` | `provenance=true` |

Output: unchanged — full `QueryResponse` JSON to stdout (includes `outcome`, `quote`, `message`).

---

## Admin

### API (`src/mycelium_admin/server.py`)

Extend `AdminQueryRequest`:

```python
quote_id: str | None = None
provenance: bool = False
principal: BillingPrincipal | None = None  # optional; sponsor demos later
```

Pass through to `EntityQuery`.

### UI (`admin-ui/`)

When `outcome` is `quote_required` or `payment_required`:

- Show collapsible **Quote** `<pre>` with `quote` object (line items, `total_usd`, `cache_state`)
- Show **quote_id** in a read-only field + editable retry field
- **Accept quote** button — re-submit same entity_key / binding / attributes with `quote_id`
- Outcome badge styles for metering outcomes (distinct from `assembled` / `error`)

When `payment_required`: show message pointing at MCP `pay_quote` (no pay button in this slice).

Optional read-only line in Overview when capabilities expose `metering.enabled` from policy.

---

## MCP

No tool changes required. Add:

- **`bin/demo-metering-negotiation`** — Python script invoking `run_query` or `query_entity` with `MYCELIUM_NETWORK=crm-metering`; three steps; rich or plain JSON
- **`queries/*.json`** fixtures documented in README for Claude Desktop manual runs

---

## Demo script behavior

`bin/demo-metering-negotiation`:

1. Assert `crm-metering` registered or `--network-dir` passed
2. Step 1: bind Paul Murphy @ Acme
3. Step 2: request `email` → expect `quote_required`, print quote
4. Step 3: retry with `quote_id` → expect `assembled` (mock research OK without API keys if test env mocks; script documents need for keys OR use env `MYCELIUM_AUTO_ACCEPT_QUOTES` only for step 3 debugging — **default: no bypass**)
5. Exit 0 on success; non-zero with clear stderr on mismatch

Flags: `--network`, `--network-dir`, `--json-only` (no prose).

---

## Tests

| Test | Assert |
|------|--------|
| `test_cli_query_binding_and_quote_id` | subprocess `mycelium query` with metering fixture network |
| `test_admin_query_passes_quote_id` | `POST /query` with `quote_id` reaches graph (mock graph or temp network) |

Extend or mirror patterns from `tests/test_entity_metering.py` fixture helpers.

---

## Doc updates

- **`README.md`** — “Testing metering negotiation” subsection (crm-metering, CLI flags, demo script, admin, MCP fixtures)
- **Program doc** — Slice 12 row (this slice); settlement → separate track
- **Do not edit `TODO.md`** (Cursor governance — Grok updates after review)

---

## Exit criteria

- [x] `crm-metering` example refreshable; CRM default unchanged
- [x] CLI supports bind + quote + accept loop
- [x] Admin UI shows quote and accept retry
- [x] `bin/demo-metering-negotiation` runs Paul Murphy arc
- [x] New tests pass; entity metering regression green
- [x] Ruff clean