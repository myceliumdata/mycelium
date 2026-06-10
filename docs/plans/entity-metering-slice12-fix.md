# Metering Slice 12 — fix slice

**Status:** Shipped (fix slice 2310 — review pending)  
**Depends on:** Slice 12 shipped (`prompts/cursor/done/2026-06-09-2300-entity-metering-negotiation-test-scaffolding/`)  
**Program:** [`entity-protocol-and-registry-program.md`](entity-protocol-and-registry-program.md)

---

## Objective

Close blocking and non-blocking review nits from Slice 12 negotiation test scaffolding. No settlement / x402 work.

---

## Fixes (locked)

| # | Gap | Fix |
|---|-----|-----|
| F1 | Demo script asyncio crash on step 2 | Set `MYCELIUM_USE_SYNC_CHECKPOINTER=1` in `bin/demo-metering-negotiation` bootstrap (match `src/main.py`) |
| F2 | Admin quote UI requires manual `npm run build` for `--demo` | Document **dev path** as default: `./bin/restart-admin crm-metering` (Vite :5173, no dist). Clarify `--demo` needs build in crm-metering README + root README |
| F3 | No subprocess test for demo script | Add `test_demo_metering_negotiation_script` — temp `crm-metering` root, subprocess `bin/demo-metering-negotiation --network-dir …`, exit 0; mock research if needed (same pattern as CLI test) |
| F4 | MCP `03-accept-quote.json` placeholder opaque | Add `queries/README.md` with 3-step flow; use placeholder `"<quote_id-from-step-2>"`; cross-link from crm-metering README |

---

## Non-goals

- Settlement protocol / x402
- Commit `admin-ui/dist/` (not tracked; dev stack is canonical for operators)
- New negotiation features
- **Do not edit `TODO.md`**

---

## F1 — Sync checkpointer in demo script

In `bin/demo-metering-negotiation`, before any `run_query` call:

```python
os.environ.setdefault("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")
```

Place in `_bootstrap()` or start of `_configure_network()`.

**Acceptance:** `./bin/demo-metering-negotiation --network-dir <fresh crm-metering>` exits 0 without caller setting env.

---

## F2 — Admin UI demo path docs

Update:

- `examples/networks/crm-metering/README.md` — **Primary:** `./bin/restart-admin crm-metering` → `http://127.0.0.1:5173` (live source, quote panel works). **Alternate:** `--demo` single-process requires `npm run build` first.
- `README.md` “Testing metering negotiation” table — same distinction.

No requirement to add `admin-ui/dist` to git.

---

## F3 — Demo script subprocess test

Extend `tests/test_cli_metering_query.py` (or sibling file):

1. Build temp metering network (reuse `metering_cli_env` fixture pattern).
2. `subprocess.run([repo/bin/demo-metering-negotiation, "--network-dir", root, "--json-only"], …)`
3. Assert `returncode == 0`
4. Parse stdout JSON chunks or combined output for `quote_required` then `assembled`

Mock research in parent via monkeypatch does **not** apply to subprocess — either:
- Accept step 3 `assembled` with research pending (no API keys), or
- Inject env / use network already warmed with specialist data from fixture setup before subprocess

Prefer: fixture seeds storage + categories before subprocess; script runs against that root.

---

## F4 — MCP query fixtures README

`examples/networks/crm-metering/queries/README.md`:

| Step | File | Expected outcome |
|------|------|------------------|
| 1 | `01-bind.json` | `entity_validated` |
| 2 | `02-quote-email.json` | `quote_required` + `quote.quote_id` |
| 3 | `03-accept-quote.json` | Replace `<quote_id-from-step-2>` → `assembled` |

Note: MCP server must use `crm-metering` network; restart after refresh.

Update `03-accept-quote.json`:

```json
"quote_id": "<quote_id-from-step-2>"
```

---

## Tests

```bash
uv run pytest tests/test_cli_metering_query.py tests/test_entity_metering.py -q
./bin/demo-metering-negotiation --network-dir <tmp>   # manual smoke after F1
```

Regression: prior Slice 12 tests unchanged and green.

---

## Exit criteria

- [x] F1–F4 implemented
- [x] Demo script works without caller env on fresh network
- [x] Subprocess test green
- [x] Ruff clean