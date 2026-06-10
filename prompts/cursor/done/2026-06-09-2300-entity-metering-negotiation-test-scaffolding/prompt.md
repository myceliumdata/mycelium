# Task: Metering negotiation — test scaffolding (Slice 12)

> **READY** — Slice 11 + fix shipped. Move to `in-progress/` to start.

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/entity-metering-negotiation-test-scaffolding.md`](../../docs/plans/entity-metering-negotiation-test-scaffolding.md) — **locked spec**
- Reference tests: `tests/test_entity_metering.py` (Paul Murphy arc, fixture helpers)

**Depends on:** Metering negotiation Slices 10–11 (+ fixes).

---

## Objective

Scaffold **easy hands-on testing** of `quote_required` negotiation on **CLI**, **MCP** (demo script + fixtures), and **admin UI**. **Not** real x402 / settlement protocol work.

---

## Deliverables (implement all)

### S1 — `examples/networks/crm-metering/`

- Copy or reuse `crm` seed; `network.json` with `metering.enabled: true`, `payment.enabled: false`
- `README.md` with bootstrap + Paul Murphy arc
- Optional `queries/*.json` MCP fixture files (bind, quote, accept)

### S2 — CLI flags (`src/main.py`)

Wire into `EntityQuery`:

- `--employer` → `binding.employer`
- `--binding-json` (optional JSON object)
- `--quote-id`
- `--provenance` (flag)

Document in `--help`. Full JSON response unchanged.

### S3 — Admin API (`src/mycelium_admin/server.py`)

Extend `AdminQueryRequest` + `/query` with `quote_id`, `provenance`, optional `principal`.

### S4 — Admin UI (`admin-ui/`)

- Add `quote` to `QueryResponse` type
- Outcome badges: `quote_required`, `payment_required`, `principal_required`
- When quote present: collapsible quote JSON, quote_id field, **Accept quote** button (re-run with same inputs + quote_id)
- `payment_required`: show message (MCP `pay_quote`); no pay button

Rebuild `admin-ui/dist` if your workflow expects built assets (or document `npm run build` in output.md).

### S5 — `bin/demo-metering-negotiation`

Executable script: bind → quote → accept for Paul Murphy @ Acme / email.

- Uses `MYCELIUM_NETWORK=crm-metering` by default
- Prints step labels + JSON
- `--network-dir`, `--json-only` flags
- Exit codes on failure

### S6 — Docs

- `README.md` — “Testing metering negotiation” section
- `docs/plans/entity-protocol-and-registry-program.md` — Slice 12 queued/shipped note

### S7 — Tests

- CLI subprocess test with temp metering network (binding + quote flow)
- Admin `/query` quote_id passthrough test

---

## Paul Murphy arc (acceptance)

```bash
./bin/refresh-example-network crm-metering --yes
./bin/demo-metering-negotiation
# OR manual CLI three-step from spec
```

Expect: `quote_required` with `quote.line_items`, then `assembled` after `--quote-id`.

---

## Governance

- **CRM `crm` example:** `metering.enabled: false` unchanged
- Match existing CLI/admin patterns
- **Do not edit `TODO.md`**
- No settlement / x402 / HTTP gateway code

---

## Tests

```bash
uv run pytest tests/test_entity_metering.py tests/test_cli_metering_query.py -q
# add admin test file as needed
uv run ruff check src/main.py src/mycelium_admin/server.py
```

---

## Deliverables folder

`prompts/cursor/done/2026-06-09-2300-entity-metering-negotiation-test-scaffolding/` with `prompt.md`, `output.md`.

---

## Exit criteria

- [ ] S1–S7 complete
- [ ] Demo script + CLI + admin accept loop work
- [ ] Metering regression green
- [ ] Ruff clean