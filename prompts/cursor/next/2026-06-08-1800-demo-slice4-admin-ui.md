# Task: Demo slice 4 — `mycelium-admin-ui` minimal browser UI

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- `TODO.md` → Demo (phase) → Slice 4
- `src/mycelium_admin/server.py` — live API (`GET /health`, `/status`, `/capabilities`)
- `src/network/introspection.py` — response shapes (`NetworkStatusSummary`, `status_to_dict`)
- `tests/test_admin_daemon.py` — API contract tests
- Demo slice 3 output (if present): `prompts/cursor/done/2026-06-08-1700-demo-slice3-admin-daemon/`
- Demo slice 1200 output: scannable status UX (`format_status_demo`) — **mirror this in the browser**

**Depends on:** Demo slice 3 (`mycelium-admin` read-only HTTP) complete.

---

## Workflow (mandatory)

1. **Claim:** move this file from `prompts/cursor/next/` to `prompts/cursor/in-progress/` before edits.
2. **Deliver:** `prompts/cursor/done/2026-06-08-1800-demo-slice4-admin-ui/` with `prompt.md`, `output.md`.
3. **Verification:** `npm run build` must succeed; Python smoke unchanged (`uv run pytest -m smoke -q`).
4. **Commit & push** when complete; update `TODO.md` slice 4 checkbox.

---

## Objective

Add a **minimal browser UI** for operator demos — a thin client over `mycelium-admin` only. No direct file reads, no MCP, no LangGraph.

**Two run modes:**

| Mode | Commands | Use |
|------|----------|-----|
| **Development** | Terminal A: `MYCELIUM_NETWORK=crm uv run mycelium-admin` · Terminal B: `cd admin-ui && npm run dev` | Local iteration (Vite HMR) |
| **Demo (single process)** | `cd admin-ui && npm run build` then `MYCELIUM_NETWORK=crm uv run mycelium-admin` | Screen recordings; one URL |

Demo mode serves the built SPA from the admin daemon at `http://127.0.0.1:8741/` (API routes unchanged).

---

## Architecture (locked)

### Package layout

New top-level directory (not under `src/`):

```
admin-ui/
  package.json          # "name": "mycelium-admin-ui"
  vite.config.ts
  tsconfig.json
  index.html
  src/
    main.tsx
    App.tsx
    api.ts              # fetch wrappers for /health, /status, /capabilities
    components/         # minimal presentational components
  public/               # optional favicon
```

**Stack:** Vite + React + TypeScript. No component library required (plain CSS or CSS modules). Keep dependencies lean — this is a demo shell, not a design system.

### API client rules

- Base URL from `import.meta.env.VITE_ADMIN_API_URL` defaulting to `http://127.0.0.1:8741`.
- **Dev:** Vite `server.proxy` maps `/health`, `/status`, `/capabilities` → admin daemon (so fetches can use relative paths like `/status` during `npm run dev`).
- **Production (served by daemon):** use relative paths (`/status`, etc.) — same origin.
- **Never** import Python modules or read `seed.json` / `categories.json` from disk in the frontend.

### Backend addition (small)

Extend `src/mycelium_admin/server.py` to mount static files **after** API routes:

- If `framework_root() / "admin-ui" / "dist"` exists and contains `index.html`, mount `StaticFiles` at `/` with `html=True` (SPA fallback).
- If `dist/` absent, daemon behaves as today (API only) — log a one-line hint: `admin UI: cd admin-ui && npm run build`.
- Do **not** add a new Python entry point for the frontend.

Use `network.paths.framework_root()` for the dist path.

---

## UI requirements (v0)

Single-page app with scannable sections — visually aligned with CLI `format_status_demo` (slice 1200), not the verbose debug layout.

### 1. Header (from `GET /health`)

- Network label: `network_name` + `display_name` when they differ.
- Connection status badge (`ok` vs error).
- Show bound `network_root` in a subdued/secondary style (operators need it; keep off the hero line).

### 2. Overview (from `GET /status`)

Mirror demo CLI semantics:

| CLI | UI |
|-----|-----|
| `Seed: ✅ (N)` | Seed card with count |
| `Current ontology: ✅` + category lines | Category list with `format_category_examples`-style copy (name + e.g. examples) |
| `Current ontology: ❌` | Empty ontology state |
| `Existing specialists: contact (1)` | Specialists with `record_count > 0` only — show **category + count**, not `*_specialist` agent names |
| `Existing specialists: ❌` | Empty specialists state |

Load `/status` on mount; show loading and error states.

### 3. Ontology detail (from `GET /capabilities` or `/status.categories`)

- Expandable or secondary panel with category **descriptions** from `capabilities.ontology.categories` when present.
- If `guide_present`, show `guide.md` content in a collapsible panel (raw markdown render is fine — `<pre>` or minimal markdown lib; avoid heavy deps).

### 4. Entity drill-down

- Search input (name or id).
- On submit: `GET /status?entity={encodeURIComponent(key)}`.
- Display:
  - `entity_matches` count
  - `0` → “No seed match”
  - `>1` → “Multiple seed matches — narrow the key”
  - `1` → table of `entity_fields`: field, category, status, value (when present)
- Optional: `?category=` filter dropdown populated from ontology categories; pass through to status fetch.

### 5. Specialist drill-down (lightweight)

- Clicking a specialist row (category + count) sets category filter and refetches `/status?category=…`.
- Show filtered `specialists` and `categories` for that slice — no new API needed.

### Out of scope for v0 UI

- Write actions (refresh, register, query)
- Auth, login, multi-network switcher in one UI (one daemon = one network)
- LangSmith traces, MCP tools
- Fancy charts, real-time polling (manual refresh button is enough)
- Mobile polish beyond readable layout

---

## Repo hygiene

### `.gitignore`

Add:

```
admin-ui/node_modules/
```

(`dist/` is already gitignored globally — built assets are not committed.)

### `README.md`

New subsection **Admin UI** under Admin daemon:

- `cd admin-ui && npm install && npm run dev`
- Demo single-process flow (`npm run build` + `mycelium-admin`)
- `VITE_ADMIN_API_URL` override
- Explicit note: UI is API-only; restart daemon after code deploy

### `examples/networks/crm/README.md`

Short demo steps: refresh CRM → start admin → open browser.

### `TODO.md`

Mark Demo slice 4 done when complete.

### CI (optional but preferred)

Add a non-blocking step to `.github/workflows/ci.yml`:

```yaml
- uses: actions/setup-node@v4
  with:
    node-version: "22"
- run: cd admin-ui && npm ci && npm run build
```

If `package-lock.json` is omitted, use `npm install` and document why. Prefer **committed lockfile** for reproducible builds.

---

## Tests & verification

### Frontend

```bash
cd admin-ui && npm install && npm run build
```

Build success is the minimum bar. Optional: one Vitest smoke for `api.ts` URL builder — only if trivial.

### Python (smoke)

Add one test in `tests/test_admin_daemon.py` (or sibling):

- Create minimal fake `admin-ui/dist/index.html` under `tmp_path` is awkward — instead **monkeypatch `framework_root()`** to point at a tmp dir containing `admin-ui/dist/index.html`.
- Assert `GET /` returns 200 and HTML when dist exists.
- Assert `GET /status` still works when static mount is enabled.

Mark `@pytest.mark.smoke`.

### Manual demo script (document in `output.md`)

```bash
./bin/refresh-example-network crm --yes
MYCELIUM_NETWORK=crm uv run mycelium-admin   # terminal 1 — or build+single process
cd admin-ui && npm run dev                   # terminal 2 (dev mode)

# After queries populate storage:
# - Overview shows specialists with counts
# - Entity search "Andrea Kalmans" shows fields when storage exists
```

---

## Scope boundaries (strict)

**May create/modify:**
- `admin-ui/**` (new)
- `src/mycelium_admin/server.py` (static mount only)
- `tests/test_admin_daemon.py` (static mount smoke)
- `.gitignore`, `README.md`, `examples/networks/crm/README.md`, `TODO.md`
- `.github/workflows/ci.yml` (optional frontend build step)

**Out of scope:**
- Changes to `build_network_status()` or API response shapes
- Write endpoints on admin daemon
- Embedding admin UI in MCP
- Extracting frontend to separate repo
- Heavy UI frameworks (MUI, Chakra, etc.)
- E2E Playwright suite (follow-up if needed)

If API gaps block UX, **document in `output.md`** and propose a tiny slice 3.1 — do not expand introspection in this slice.

---

## Deliverables

1. Working `admin-ui` with `npm run dev` and `npm run build`
2. Static serve from `mycelium-admin` when `admin-ui/dist` exists
3. `output.md` with screenshots description, dev vs demo commands, and any slice-5 polish nits
4. `TODO.md` slice 4 marked complete