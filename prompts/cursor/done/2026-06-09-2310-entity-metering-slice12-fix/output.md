# Slice 12 fix — Negotiation scaffolding nits

## Summary

Closed four review items from Slice 12. Demo script now sets sync checkpointer internally; admin docs point operators at `./bin/restart-admin crm-metering` (Vite :5173) by default.

## Fixes

| # | Fix |
|---|-----|
| F1 | `MYCELIUM_USE_SYNC_CHECKPOINTER=1` in `bin/demo-metering-negotiation` `_bootstrap()` |
| F2 | Admin demo docs: default `./bin/restart-admin crm-metering`; `--demo` needs `npm run build`; added `admin-ui/dist/` to `.gitignore` |
| F3 | `test_demo_metering_negotiation_script` — subprocess `--json-only`, exit 0, `quote_required` + `assembled` |
| F4 | `queries/README.md` 3-step table; `03-accept-quote.json` placeholder `<quote_id-from-step-2>` |

## Tests

**29 passed** — `test_cli_metering_query.py` (2), `test_admin_daemon.py`, `test_example_network.py`

```bash
uv run pytest tests/test_cli_metering_query.py tests/test_admin_daemon.py tests/test_example_network.py -q
```

## For Grok + Paul

- Mark **Slice 12 fix (`2310`)** done in `TODO.md`
- Slice 12 parent already approved with fixes — this fix slice ready for review
- Review folder: `prompts/cursor/done/2026-06-09-2310-entity-metering-slice12-fix/`
- Suggested commit message (after review):

```
Fix metering negotiation scaffolding nits (Slice 12 fix).

Sync checkpointer in demo script; restart-admin as default admin path;
subprocess demo test; MCP queries README.
```

- **Did not edit `TODO.md`** (per governance)
