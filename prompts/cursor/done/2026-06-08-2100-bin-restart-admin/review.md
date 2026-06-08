# Review: `bin/restart-admin` (`2026-06-08-2100`)

**Reviewer:** Grok  
**Date:** 2026-06-08  
**Commit:** `df32d09`  
**Verdict:** **Approved**

---

## Scope check

| Requirement | Status |
|-------------|--------|
| `bin/restart-admin` executable | ✅ |
| Dev default: kill :8741 + :5173 | ✅ |
| Background `uv run mycelium-admin` | ✅ |
| Foreground `npm run dev` | ✅ |
| Default network `crm`; positional arg | ✅ |
| Caller `MYCELIUM_NETWORK` / `MYCELIUM_NETWORK_ROOT` wins | ✅ |
| Ctrl-C trap stops background daemon | ✅ |
| `/health` wait + actionable error | ✅ |
| `npm install` only if `node_modules` missing | ✅ |
| `--demo` optional | ✅ |
| `--dry-run` | ✅ |
| README + CRM README | ✅ |
| Governance: no `TODO.md` edit | ✅ |
| `output.md` + **For Grok + Paul** | ✅ |

---

## Verification (Grok re-run)

```bash
./bin/restart-admin --dry-run           → plan OK (crm)
./bin/restart-admin --dry-run fleet     → MYCELIUM_NETWORK=fleet
./bin/restart-admin --dry-run --demo    → build + foreground daemon plan
test -x bin/restart-admin               → executable
```

Paul hands-on: `./bin/restart-admin` → :5173 loads; Ctrl-C frees :8741.

---

## What looks good

- **`set -euo pipefail`** + portable `lsof` kill with SIGTERM then SIGKILL.
- **Network precedence** documented in header and implemented correctly (env wins).
- **`wait_for_admin`** polls `/health` with refresh hint on failure — good demo UX.
- **`--demo`** uses `exec` and clears trap — correct single-process semantics.
- **README** positions script as recommended path; keeps manual two-terminal fallback.

---

## Issues

### Nit — `MYCELIUM_ADMIN_UI_PORT` not wired to Vite

- **File:** `bin/restart-admin` documents `MYCELIUM_ADMIN_UI_PORT`; `admin-ui/vite.config.ts` hardcodes `port: 5173`.
- **Impact:** Custom port env kills the wrong listener or leaves Vite on 5173.
- **Suggestion:** Either read port in `vite.config.ts` from env, or drop the env from script help until wired. Low priority for demos (5173 default is fine).

### Nit — no `EXIT` trap

- If `npm run dev` exits without SIGINT (rare crash), background daemon may orphan on :8741.
- **Suggestion:** `trap cleanup EXIT` after daemon start, or document “if Vite dies, `lsof -i :8741`”. Non-blocking.

---

## Decision

**Approve.** Paul can use `./bin/restart-admin` as the default dev workflow.