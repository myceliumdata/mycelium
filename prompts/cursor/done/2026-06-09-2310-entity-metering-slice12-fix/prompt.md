# Task: Entity metering Slice 12 — fix slice

> **READY** — Slice 12 reviewed (approve with fixes). Move to `in-progress/` to start.

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/entity-metering-slice12-fix.md`](../../docs/plans/entity-metering-slice12-fix.md) — **locked fix spec**
- Slice 12 review: `prompts/cursor/done/2026-06-09-2300-entity-metering-negotiation-test-scaffolding/review.md`

**Depends on:** Slice 12 negotiation test scaffolding.

---

## Objective

Fix four review items from Slice 12: demo script checkpointer bug, admin demo docs, subprocess test, MCP fixture clarity.

---

## Fixes (implement all)

### F1 — `bin/demo-metering-negotiation` sync checkpointer

Set `os.environ.setdefault("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")` in bootstrap before `run_query` (same as `src/main.py`).

Verify: fresh `crm-metering` refresh + script exits 0 without caller env.

### F2 — Admin UI demo documentation

- `examples/networks/crm-metering/README.md` — **default:** `./bin/restart-admin crm-metering` (Vite :5173, no build). **Alternate:** `--demo` needs `npm run build`.
- `README.md` “Testing metering negotiation” — same guidance.

Do **not** commit `admin-ui/dist/`.

### F3 — Subprocess test for demo script

Add `test_demo_metering_negotiation_script` in `tests/test_cli_metering_query.py` (or new file):

- Temp metering network with contact specialist + seed (reuse fixture helpers)
- `subprocess.run` on `bin/demo-metering-negotiation --network-dir … --json-only`
- Assert exit code 0; output contains `quote_required` and `assembled`

### F4 — MCP fixtures README

- Create `examples/networks/crm-metering/queries/README.md` (3-step table)
- Change `03-accept-quote.json` placeholder to `"<quote_id-from-step-2>"`
- Link from `crm-metering/README.md`

---

## Governance

- No settlement / x402 scope
- **Do not edit `TODO.md`**
- Match existing test/style patterns

---

## Tests

```bash
uv run pytest tests/test_cli_metering_query.py tests/test_admin_daemon.py tests/test_example_network.py -q
uv run ruff check bin/demo-metering-negotiation tests/test_cli_metering_query.py
```

---

## Deliverables

`prompts/cursor/done/2026-06-09-2310-entity-metering-slice12-fix/` with `prompt.md`, `output.md`.

---

## Exit criteria

- [ ] F1–F4 complete
- [ ] Demo script smoke passes without extra env
- [ ] All Slice 12 regression tests green
- [ ] Ruff clean