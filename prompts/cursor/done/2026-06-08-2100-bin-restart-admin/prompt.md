# Task: `bin/restart-admin` — one-command dev stack restart

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md` (Governance — do not edit `TODO.md`)
- `bin/run-studio`, `bin/refresh-example-network` — repo conventions
- `README.md` — Admin daemon + Admin UI sections
- `src/mycelium_admin/server.py` — default host/port (`127.0.0.1:8741`)
- `admin-ui/vite.config.ts` — dev port `5173`, proxy targets

**Depends on:** Demo slices 3–4 (`mycelium-admin` + `admin-ui`) on `main`.

**May run in parallel with:** `2026-06-08-2000-demo-admin-ui-polish` (no file overlap except README).

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- `output.md` must include **"For Grok + Paul"** (README cross-links, any follow-up flags).

---

## Workflow (mandatory)

1. Claim: move to `prompts/cursor/in-progress/` before edits.
2. Deliver: `prompts/cursor/done/2026-06-08-2100-bin-restart-admin/`
3. Commit & push (not `TODO.md`).

---

## Objective

Paul needs **one command** to restart the **whole admin dev stack** after code changes or a stuck process — instead of manually killing ports and opening two terminals.

```bash
./bin/restart-admin          # default: network crm
./bin/restart-admin fleet    # MYCELIUM_NETWORK=fleet
```

---

## Behavior (locked — Paul confirmed)

### Default: **dev mode**

1. **Stop** anything listening on:
   - `127.0.0.1:8741` (or `MYCELIUM_ADMIN_PORT` if set)
   - `127.0.0.1:5173` (Vite dev server)
   - Use portable kill (e.g. `lsof -ti:PORT` on macOS/Linux); ignore exit if nothing bound.
2. **Start** `mycelium-admin` in **background** with network binding.
3. **Start** `admin-ui` Vite dev server in **foreground** (script blocks; Ctrl-C stops Vite; trap should also stop background daemon).

### Network binding

| Input | Env |
|-------|-----|
| No arg | `MYCELIUM_NETWORK=crm` |
| Positional `<name>` | `MYCELIUM_NETWORK=<name>` |
| `--network NAME` | same (optional explicit flag) |

Do **not** override if caller already exported `MYCELIUM_NETWORK` / `MYCELIUM_NETWORK_ROOT` — env wins over defaults (document precedence in script header).

### Repo / toolchain

- Run from **framework repo root** (resolve via script location like other `bin/` tools).
- Use **`uv run mycelium-admin`** for the daemon (not bare python).
- For UI: `cd admin-ui && npm run dev` — run `npm install` only if `node_modules` missing (or document “run npm install once”; prefer check for `admin-ui/node_modules`).
- Re-exec via `.venv` python if present (match `refresh-example-network` pattern) **or** pure bash invoking `uv` — either is fine if consistent with repo.

### UX output

Print clearly after start:

```
Admin API:  http://127.0.0.1:8741/health
Admin UI:   http://127.0.0.1:5173/
Network:    crm
```

On daemon start failure (port still busy, unconfigured network), exit non-zero with actionable message (`refresh-example-network crm`, check `MYCELIUM_NETWORK`).

### Signal handling

- Foreground Vite: Ctrl-C exits script.
- On exit (INT/TERM), kill background `mycelium-admin` child (avoid orphan on :8741).
- Optional: write PIDs to `tmp/restart-admin.pids` (gitignored `tmp/` exists) for debugging — not required if trap is reliable.

---

## Optional flags (implement if straightforward)

| Flag | Behavior |
|------|----------|
| `--demo` | **Not default.** Kill :8741 only; `npm run build` in `admin-ui/`; foreground `mycelium-admin` only (single URL :8741). Skip :5173. |
| `--dry-run` | Print kill/start plan without executing |

If `--demo` is omitted, dev mode above is the only required path.

---

## Docs

- **`README.md`** — Admin UI section: add `./bin/restart-admin` as the recommended dev workflow.
- **`examples/networks/crm/README.md`** — one-line mention for browser demos.

---

## Tests

No pytest required. Manual verification in `output.md`:

```bash
./bin/restart-admin
# open :5173, confirm /health via proxy

# second terminal: run a query, confirm UI poll sees specialists (if polish landed)

Ctrl-C → confirm :8741 and :5173 are free (lsof)
```

---

## Scope boundaries

**May create/modify:**
- `bin/restart-admin` (new, executable `chmod +x`)
- `README.md`, `examples/networks/crm/README.md`

**Out of scope:**
- `TODO.md`
- Changes to `mycelium_admin` Python code
- systemd/launchd installers
- Killing MCP processes

---

## Deliverables

1. Working `./bin/restart-admin`
2. `output.md` with manual verify notes + **For Grok + Paul**
3. Commit & push