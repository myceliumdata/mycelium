# Demo slice 3 — admin daemon

## Summary

Added **`mycelium-admin`**: a long-lived localhost HTTP read-only API (one process per network) for operator demos and the slice 4 browser UI.

## Files changed

| File | Change |
|------|--------|
| `src/mycelium_admin/__init__.py` | New package |
| `src/mycelium_admin/server.py` | FastAPI app, bootstrap, routes, `run_server()` |
| `pyproject.toml` | `fastapi`, `uvicorn` deps; `mycelium-admin` entry point |
| `uv.lock` | Lockfile updated |
| `tests/test_admin_daemon.py` | 8 smoke tests (TestClient) |
| `README.md` | Admin daemon section |
| `examples/networks/crm/README.md` | One-line daemon note for slice 4 |
| `TODO.md` | Demo slice 3 marked done |

## API (v0 read-only)

| Route | Source |
|-------|--------|
| `GET /health` | `network_metadata()` at bootstrap |
| `GET /status` | `status_to_dict(build_network_status(...))` — mirrors `mycelium network status --json` |
| `GET /capabilities` | `build_network_capabilities()` — same as MCP `describe_network` |

Query params on `/status`: `category`, `entity` (mirror CLI `--category`, `--entity`).

`reset_seed_data()` runs before `/status` and `/capabilities` so refresh-updated seed is visible without daemon restart.

## Sample curl (after `refresh-example-network crm`)

```bash
MYCELIUM_NETWORK=crm uv run mycelium-admin
# Listening on http://127.0.0.1:8741

curl -s http://127.0.0.1:8741/health | jq .
# { "status": "ok", "network_name": "crm", "display_name": "...", "network_root": "..." }

curl -s http://127.0.0.1:8741/status | jq '.seed_people_count, .ontology_present'
# 15, true/false depending on whether categories.json exists

curl -s "http://127.0.0.1:8741/status?entity=Andrea%20Kalmans" | jq '.entity_matches'
# 1
```

Compare to CLI:

```bash
uv run mycelium network status --network crm --json
```

JSON shape should match daemon `/status` for the same `network_root`.

## Verification

```bash
uv run pytest -m smoke -q tests/test_admin_daemon.py   # 8 passed
uv run ruff check src/mycelium_admin tests/test_admin_daemon.py
```

Full smoke: **152 passed** (with `LANGCHAIN_TRACING_V2=false`).

## Open questions for slice 4 (UI)

- Default UI dev server port vs admin `8741` — likely UI on separate port fetching `http://127.0.0.1:8741/status` and `/capabilities`.
- First screen: consume `/capabilities` for header (guide + ontology) and `/status` for seed/ontology/specialist summary.
- Entity drill-down: `GET /status?entity=…` (and optional `category=`).
- CORS already allows `http://127.0.0.1:*` and `http://localhost:*`.

## Next

Demo slice 4 — minimal browser UI against this API.
