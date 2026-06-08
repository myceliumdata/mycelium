# Task: Demo slice 3 — `mycelium-admin` read-only HTTP daemon

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- `TODO.md` → Demo (phase) → Slice 3
- `src/network/introspection.py` — **single source of read logic** (do not duplicate)
- `src/mycelium_mcp/server.py` — long-lived per-network process pattern (`_bootstrap`, env binding)
- `src/main.py` — `mycelium network status` wiring (`_configure_network_paths`, `--json`, `--category`, `--entity`)
- `tests/test_network_status.py` — fixtures and expected JSON shape
- Demo slice 2 output: `prompts/cursor/done/2026-06-08-1100-demo-slice2-network-status/`

**Depends on:** Demo slices 1–2, 5, 1200 (introspection + CLI status complete).

**Blocks:** Demo slice 4 (minimal browser UI consumes this API).

---

## Workflow (mandatory)

1. **Claim:** move this file from `prompts/cursor/next/` to `prompts/cursor/in-progress/` before any edits.
2. **Deliver:** `prompts/cursor/done/2026-06-08-1700-demo-slice3-admin-daemon/` with `prompt.md`, `output.md`.
3. **Tests:** smoke by default (`uv run pytest -m smoke -q`); mark new HTTP tests `@pytest.mark.smoke`.
4. **Commit & push** when complete; update `TODO.md` slice 3 checkbox + prompt reference.

---

## Objective

Add a **long-lived localhost HTTP admin API** for operator demos — one process per network, mirroring MCP’s deployment model but serving **humans / a future UI**, not visiting agents.

```bash
# CRM example (env binding — same as MCP)
MYCELIUM_NETWORK=crm uv run mycelium-admin

# Or explicit root
MYCELIUM_NETWORK_ROOT=~/mycelium-networks/crm uv run mycelium-admin
```

**v0 is read-only.** Every response field must come from `src/network/introspection.py` — no parallel read logic in route handlers.

---

## Architecture (locked)

### Role split (do not blur)

| Surface | Audience | Transport |
|---------|----------|-----------|
| `mycelium-mcp` | Visiting AI agents | stdio MCP |
| `mycelium-admin` | Operator / demo UI | HTTP localhost |
| `mycelium network status` | CLI / scripting | one-shot subprocess |

All three share **`build_network_status()`** / **`status_to_dict()`** for snapshots.

### New package: `src/mycelium_admin/`

Mirror `mycelium_mcp` layout:

```
src/mycelium_admin/
  __init__.py
  server.py      # FastAPI app, bootstrap, run_server()
```

**Entry point** in `pyproject.toml`:

```toml
mycelium-admin = "mycelium_admin.server:run_server"
```

**Dependencies:** add explicit `fastapi` and `uvicorn` to `[project.dependencies]` (pin compatible with Python 3.12; run `uv lock` if lockfile changes).

### Network binding (env only — like MCP)

Daemon resolves network at **process start** via `resolve_network_root()` (no `--network-dir` CLI on v0):

| Env | Purpose |
|-----|---------|
| `MYCELIUM_NETWORK_ROOT` | Explicit path (highest env precedence) |
| `MYCELIUM_NETWORK` | Registered name in `networks.json` |
| (default) | Registry default network |

On startup: `load_dotenv()` → `apply_network_paths(NetworkPaths.from_root(root))` → `get_storage(...)` (seed path wiring; **no queries**, **no graph**).

Fail fast at startup with clear error if unconfigured (reuse `NO_NETWORK_CONFIGURED_MSG` tone from `network.paths`).

### Listen config

| Env | Default | Notes |
|-----|---------|-------|
| `MYCELIUM_ADMIN_HOST` | `127.0.0.1` | Localhost only v0 — no `0.0.0.0` |
| `MYCELIUM_ADMIN_PORT` | `8741` | One port per network process |

Log bound URL on startup (e.g. `http://127.0.0.1:8741`).

### Freshness after disk changes

Operators run `./bin/refresh-example-network` without restarting daemons. Before each **`GET /status`** (and **`GET /capabilities`** if implemented), call **`reset_seed_data()`** so cached seed matches disk. Ontology/registry/storage are already read from files in introspection — no full `refresh_runtime_from_disk()` (that is MCP query-path weight; admin has no graph).

Document in README: restart daemon after **code deploy** or if specialist modules on disk change and counts look wrong.

---

## HTTP API (v0 read-only)

Use FastAPI. JSON responses; `Content-Type: application/json`.

### `GET /health`

Liveness + network binding. **No graph ping** (unlike MCP `health_check` internal query).

Suggested shape:

```json
{
  "status": "ok",
  "network_name": "crm",
  "display_name": "CRM example",
  "network_root": "/Users/paul/mycelium-networks/crm"
}
```

On misconfiguration after startup (should not happen if bootstrap is correct): `503` with `status: "error"` and `message`.

### `GET /status`

**Canonical demo endpoint.** Returns **`status_to_dict(build_network_status(...))`** — identical JSON to:

```bash
uv run mycelium network status --json
```

Query parameters (mirror CLI flags):

| Param | Maps to |
|-------|---------|
| `category` | `category_filter` |
| `entity` | `entity_key` |

Examples:

```
GET /status
GET /status?category=contact
GET /status?entity=Andrea%20Kalmans
GET /status?category=contact&entity=Andrea%20Kalmans
```

Call `reset_seed_data()` immediately before `build_network_status()`.

### `GET /capabilities` (recommended)

Returns **`build_network_capabilities()`** JSON — same payload MCP `describe_network` uses (guide, ontology, policy). Enables slice 4 UI header without new read logic.

Call `reset_seed_data()` before build if capabilities ever reads seed (today it does not — still fine to share a small `_refresh_read_cache()` helper).

### CORS (slice 4 prep)

Enable permissive CORS for `http://127.0.0.1:*` and `http://localhost:*` only. No auth v0.

### Out of scope for v0 routes

- `POST` / `PUT` / `DELETE` (refresh, register, query) — slice 4+ / separate prompts
- WebSocket, SSE
- Serving static UI assets (slice 4)
- Auth, TLS, remote bind

---

## Tests

New file: `tests/test_admin_daemon.py`

| Test | Marker | Assert |
|------|--------|--------|
| `GET /health` returns 200 + network metadata | smoke | tmp_path network root via env |
| `GET /status` JSON matches `status_to_dict(build_network_status())` | smoke | seed-only fixture from `test_network_status.py` helpers |
| `GET /status?entity=…` drill-down | smoke | reuse `find_by_key` fixture name |
| `GET /capabilities` keys present (`ontology`, `policy`) | smoke | optional if route added |
| Unconfigured network → startup or health error | smoke | monkeypatch empty registry + no env |

Use FastAPI **`TestClient`** (from `starlette.testclient` or `fastapi.testclient`) — no live server subprocess in smoke tests.

Reuse `_seed_only_root`, `_configure_root` patterns from `tests/test_network_status.py` (import or extract shared helper if duplication is >10 lines — prefer minimal duplication).

---

## Docs

**README.md** — new subsection **Admin daemon** (after MCP or under CLI):

- One process per network; env binding examples parallel to MCP snippets
- `uv run mycelium-admin` + default port
- `GET /health`, `GET /status` (and `/capabilities` if added)
- Relationship to `mycelium network status --json`
- Restart guidance after refresh vs code deploy

**`examples/networks/crm/README.md`** — one line: start admin daemon for browser demo (slice 4).

**`TODO.md`** — mark Demo slice 3 done when complete; note prompt path.

No architecture.md rewrite.

---

## Verification

```bash
uv run ruff check src/mycelium_admin/ tests/test_admin_daemon.py
uv run pytest -m smoke -q tests/test_admin_daemon.py

# Manual (after refresh-example-network crm)
MYCELIUM_NETWORK=crm uv run mycelium-admin &
curl -s http://127.0.0.1:8741/health | jq .
curl -s http://127.0.0.1:8741/status | jq '.seed_people_count, .ontology_present'
curl -s "http://127.0.0.1:8741/status?entity=Andrea%20Kalmans" | jq '.entity_matches'
```

Compare daemon `/status` output to `uv run mycelium network status --network crm --json` — should match for same network.

---

## Scope boundaries (strict)

**May create/modify:**
- `src/mycelium_admin/` (new)
- `pyproject.toml` (scripts + fastapi/uvicorn deps; lockfile if needed)
- `tests/test_admin_daemon.py` (new)
- `README.md`, `examples/networks/crm/README.md`, `TODO.md`

**May touch lightly:**
- `src/network/__init__.py` — only if exporting a shared helper is cleaner than inline `reset_seed_data()` in admin (prefer admin-local helper)

**Out of scope (do not implement):**
- Changes to `build_network_status()` read logic or dataclasses (unless bug found — document, do not fix silently)
- Write endpoints (refresh, register, `query_entity`)
- Admin UI / static files
- Auth, ngrok, remote deployment
- Fuzzy matching, MCP tool changes
- Refactoring `main.py` network status into shared HTTP layer (CLI stays as-is)

If you believe shared bootstrap code between MCP and admin is necessary, **stop** and document a follow-up prompt — do not large-refactor `mycelium_mcp` in this slice.

---

## Deliverables

1. Working `mycelium-admin` entry point
2. Smoke tests green
3. `prompts/cursor/done/2026-06-08-1700-demo-slice3-admin-daemon/output.md` with:
   - Files changed
   - Sample `curl` output (health + status snippet)
   - Manual compare note vs CLI `--json`
   - Open questions for slice 4 (UI port, which endpoints to consume first)