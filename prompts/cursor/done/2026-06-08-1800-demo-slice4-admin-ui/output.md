# Demo slice 4 — admin UI

## Summary

Added **`mycelium-admin-ui`** (`admin-ui/`): a minimal Vite + React + TypeScript SPA that talks only to `mycelium-admin` HTTP routes. Demo mode serves the built bundle from the daemon at `http://127.0.0.1:8741/` when `admin-ui/dist/index.html` exists.

## Files changed

| File | Change |
|------|--------|
| `admin-ui/**` | New SPA: header, overview, ontology/guide panels, entity search, category filter |
| `admin-ui/package-lock.json` | Committed for reproducible CI builds |
| `src/mycelium_admin/server.py` | Mount `StaticFiles` at `/` when `dist/` present; hint when absent |
| `tests/test_admin_daemon.py` | +1 smoke test (`GET /` HTML + `GET /status` with static mount) |
| `.gitignore` | `admin-ui/node_modules/` |
| `README.md` | Admin UI subsection (dev vs single-process) |
| `examples/networks/crm/README.md` | Browser demo steps |
| `.github/workflows/ci.yml` | Node 22 + `npm ci && npm run build` |
| `TODO.md` | Demo slice 4 marked done |

## Run modes

### Development (HMR)

```bash
# Terminal A
MYCELIUM_NETWORK=crm uv run mycelium-admin

# Terminal B
cd admin-ui && npm install && npm run dev
# → http://127.0.0.1:5173 (proxies /health, /status, /capabilities)
```

### Demo (single process)

```bash
./bin/refresh-example-network crm --yes
cd admin-ui && npm install && npm run build
MYCELIUM_NETWORK=crm uv run mycelium-admin
# → http://127.0.0.1:8741/
```

Optional API override: `VITE_ADMIN_API_URL=http://127.0.0.1:8741 npm run dev`

## UI sections (v0)

1. **Header** — `GET /health`: network name/display, ok/error badge, subdued `network_root`.
2. **Overview** — `GET /status`: seed count, ontology categories (`format_category_examples` copy), specialists as `category (count)` only.
3. **Ontology detail** — `GET /capabilities`: category descriptions; collapsible `guide.md` in `<pre>` when present.
4. **Entity drill-down** — search → `GET /status?entity=…`; table of fields when one match.
5. **Specialist drill-down** — click category row → category filter refetch.

Manual refresh button; no polling, no write actions.

## Verification

```bash
cd admin-ui && npm ci && npm run build          # ✓
uv run pytest -m smoke -q tests/test_admin_daemon.py   # 9 passed
uv run pytest -m smoke -q                       # 155 passed (see flake note)
```

**Known flake:** `test_create_specialist_writes_files_and_registers` may fail in full parallel runs (LLM research path); passes in isolation.

## Slice 5 polish nits (optional follow-up)

- Add favicon under `admin-ui/public/`
- Light markdown rendering for `guide.md` (tiny dep or hand-rolled)
- Manual refresh could re-fetch `/capabilities` only when guide panel is open
- Playwright smoke for entity search after storage populated
