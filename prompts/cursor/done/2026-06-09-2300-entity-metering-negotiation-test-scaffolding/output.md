# Slice 12 — Metering negotiation test scaffolding

## Summary

Scaffolded hands-on testing of `quote_required` negotiation on CLI, MCP fixtures, admin UI, and a demo script. **`crm`** example unchanged (`metering.enabled: false`). New **`crm-metering`** example has metering on, payment off.

## Deliverables

| # | Item |
|---|------|
| S1 | `examples/networks/crm-metering/` — seed, `network.json`, guide, README, `queries/*.json` |
| S2 | CLI flags: `--employer`, `--binding-json`, `--quote-id`, `--provenance` |
| S3 | Admin API: `AdminQueryRequest` + `/query` pass `quote_id`, `provenance`, `principal` |
| S4 | Admin UI: quote panel, quote_id field, **Accept quote**, metering outcome badges |
| S5 | `bin/demo-metering-negotiation` — Paul Murphy bind → quote → accept |
| S6 | `README.md` “Testing metering negotiation”; program doc Slice 12 |
| S7 | `tests/test_cli_metering_query.py`, `test_admin_query_passes_quote_id` |

## Quick start

```bash
./bin/refresh-example-network crm-metering --yes
./bin/demo-metering-negotiation
```

Manual CLI:

```bash
uv run mycelium query --network crm-metering --entity-key "Paul Murphy" --employer "Acme Corp"
uv run mycelium query --network crm-metering --entity-key "Paul Murphy" --employer "Acme Corp" --attributes email
uv run mycelium query --network crm-metering ... --quote-id q_xxx
```

Admin: `cd admin-ui && npm run build` then `MYCELIUM_NETWORK=crm-metering uv run mycelium-admin`.

## Tests

**47 passed** (representative run):

- `tests/test_cli_metering_query.py` — 1
- `tests/test_entity_metering.py` — 20
- `tests/test_admin_daemon.py` — 14 (incl. new quote_id test)
- `tests/test_example_network.py` — `test_example_crm_metering_layout`

```bash
uv run pytest tests/test_cli_metering_query.py tests/test_entity_metering.py tests/test_admin_daemon.py -q
```

## For Grok + Paul

- Mark **Slice 12 — Negotiation test scaffolding** done in `TODO.md`
- Register `crm-metering` in docs/onboarding if not already listed
- Review folder: `prompts/cursor/done/2026-06-09-2300-entity-metering-negotiation-test-scaffolding/`
- Suggested commit message (after review):

```
Add metering negotiation test scaffolding (Slice 12).

crm-metering example, CLI bind/quote flags, admin quote accept UI,
bin/demo-metering-negotiation, and CLI/admin tests.
```

- **Did not edit `TODO.md`** (per governance)
