# `bin/restart-admin`

## Summary

Added **`./bin/restart-admin`** — one command to restart the admin dev stack (kill `:8741` + `:5173`, background `mycelium-admin`, foreground Vite). Optional `--demo` for single-process built SPA on `:8741`.

## Files changed

| File | Change |
|------|--------|
| `bin/restart-admin` | New executable bash script |
| `README.md` | Recommended dev workflow + `--demo` shortcut |
| `examples/networks/crm/README.md` | One-line `./bin/restart-admin` mention |

## Behavior

**Dev mode (default):**
1. `lsof -ti:PORT` kill on admin port (`MYCELIUM_ADMIN_PORT` or 8741) and Vite 5173
2. `npm install` in `admin-ui/` only if `node_modules` missing
3. Background `uv run mycelium-admin` with network binding
4. Wait for `/health` (or port listen); exit non-zero with refresh hint on failure
5. Foreground `npm run dev`; Ctrl-C trap stops background daemon

**Network precedence:** `MYCELIUM_NETWORK_ROOT` → `MYCELIUM_NETWORK` (caller env) → positional/`--network` → default `crm`

**Flags:** `--demo` (build + foreground daemon only), `--dry-run`

## Manual verification

```bash
./bin/restart-admin --dry-run
./bin/restart-admin
# → open http://127.0.0.1:5173/, confirm overview loads

# second terminal after query:
uv run mycelium query --network crm --entity-key "Andrea Kalmans" --attributes email
# UI poll should show specialist within ~3s

# Ctrl-C restart-admin → confirm ports free:
lsof -i :8741 -i :5173
```

## For Grok + Paul

- Mark **`bin/restart-admin`** done in `TODO.md` (Cursor did not edit per governance).
- Optional: add `MYCELIUM_ADMIN_UI_PORT` to README if Vite port customization is documented elsewhere.
- Paul may want `bin/restart-admin` mentioned in demo runbook slice if a consolidated operator cheatsheet is planned.
