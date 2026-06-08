# Review: Demo slice 3 — `mycelium-admin` read-only HTTP daemon

**Reviewer:** Grok  
**Date:** 2026-06-08  
**Verdict:** **Approved** — scope met; commit & push, then slice 4.

---

## Scope check

| Requirement | Status |
|-------------|--------|
| `mycelium-admin` entry point (`pyproject.toml`) | ✅ |
| `src/mycelium_admin/` package (mirror `mycelium_mcp`) | ✅ |
| Env binding: `MYCELIUM_NETWORK` / `MYCELIUM_NETWORK_ROOT` | ✅ |
| Fail fast at startup when unconfigured | ✅ |
| `GET /health` — liveness + network metadata | ✅ |
| `GET /status` — `status_to_dict(build_network_status(...))` | ✅ |
| `GET /capabilities` — `build_network_capabilities()` | ✅ |
| Query params `category`, `entity` on `/status` | ✅ |
| `reset_seed_data()` before status/capabilities reads | ✅ |
| CORS for localhost dev (slice 4 prep) | ✅ |
| No write routes, no graph/`run_query` | ✅ |
| Read logic only in introspection (no duplication in handlers) | ✅ |
| Smoke tests (`TestClient`) | ✅ 7/7 |
| README + CRM README | ✅ |
| `TODO.md` slice 3 done | ✅ (local; see merge note) |
| `output.md` deliverable | ✅ |

---

## Verification (Grok re-run)

```text
uv run ruff check src/mycelium_admin/ tests/test_admin_daemon.py     → clean
uv run pytest -m smoke -q tests/test_admin_daemon.py                 → 7 passed
uv run pytest -m smoke -q                                            → 152 passed, 1 failed
```

The single failure is **`test_agent_factory.py::test_create_specialist_writes_files_and_registers`** — pre-existing / unrelated to admin daemon (reproduces with `LANGCHAIN_TRACING_V2=false`). Admin slice is not the cause.

---

## What looks good

- **Thin HTTP layer** — routes delegate to `introspection.py`; handlers are ~15 lines each. Correct split from MCP and CLI.
- **Bootstrap pattern** matches MCP: `load_dotenv` → `resolve_network_root` → `apply_network_paths` → `get_storage` (seed path only; no graph).
- **`create_app()` + `bootstrap_admin()`** separation enables clean `TestClient` tests without starting uvicorn.
- **`/health` 503** when `_NETWORK_INFO` unset — sensible for tests; production path always bootstraps first in `run_server()`.
- **CORS** restricted to `127.0.0.1` / `localhost` with GET-only — appropriate for v0 read-only.
- **Tests** cover parity (`/status` == CLI JSON shape), entity/category filters, capabilities keys, unconfigured bootstrap, and health error path.
- **Docs** — README table + curl compare to CLI; CRM README one-liner for slice 4.

---

## Issues

### Nit — entity drill-down test is weak

- **File:** `tests/test_admin_daemon.py:104`
- **Detail:** `assert find_by_key(entity)[0]["id"]` only checks the fixture helper returns an id; it does not assert `entity_fields` in the HTTP response.
- **Suggestion:** When populated storage fixture exists (reuse pattern from `test_network_status.py`), assert `len(payload["entity_fields"]) >= 1`. Optional for slice 3; fine to defer to slice 4 or a polish pass.

### Nit — no test for post-refresh seed visibility

- **File:** `tests/test_admin_daemon.py`
- **Detail:** Prompt called out `reset_seed_data()` so refresh-updated seed appears without daemon restart. Implementation does this; no test mutates `seed.json` between two `/status` calls.
- **Suggestion:** Small smoke test: write different people count to seed on disk, call `/status` twice — second response reflects new count. Low priority.

### Nit — Starlette TestClient deprecation warning

- **Detail:** `StarletteDeprecationWarning: install httpx2 instead` on import. Harmless today.
- **Suggestion:** Track upstream; no action required for slice 3.

### Merge hygiene — not on `origin/main` yet

- **Detail:** Slice 3 implementation files are local (uncommitted): `src/mycelium_admin/`, `tests/test_admin_daemon.py`, `pyproject.toml`, `uv.lock`, README, done artifacts.
- **Action:** Commit and push as one changeset before claiming slice 3 landed on `main`.

---

## Slice 4 handoff

- CORS and `/capabilities` + `/status` are ready for `admin-ui/` (`mycelium-admin-ui`).
- `output.md` open questions are answered by slice 4 prompt (Vite proxy + optional static serve from daemon).

---

## Post-review fixes (2026-06-08)

- **Entity drill-down test** — populated storage fixture; asserts `entity_fields` (email found).
- **Seed refresh test** — `test_status_reflects_seed_change_without_restart` mutates `seed.json` on disk; second `GET /status` sees new count without daemon restart.
- **TestClient deprecation** — `filterwarnings` in `pyproject.toml` for `StarletteDeprecationWarning`.

Admin smoke: **8 passed**.

---

## Decision

**Approved and landed** — nits addressed in `tests/test_admin_daemon.py`.