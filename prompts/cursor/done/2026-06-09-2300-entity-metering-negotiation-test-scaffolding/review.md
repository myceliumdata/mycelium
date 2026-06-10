# Review — Entity metering Slice 12 (negotiation test scaffolding)

**Reviewer:** Grok (June 2026)  
**Verdict:** **Approve with one fix** — S1–S7 delivered; tests green; demo script needs sync checkpointer default.

---

## Summary

Substantial but appropriate scaffolding slice. All three operator surfaces now support the Paul Murphy negotiation arc without touching settlement. `crm` default unchanged; `crm-metering` is a clean demo network. Scope matches spec — no x402 creep.

---

## Checklist

| # | Deliverable | Verdict | Notes |
|---|-------------|---------|-------|
| S1 | `crm-metering` example | Pass | seed, network.json, guide, README, `queries/*.json` |
| S2 | CLI flags | Pass | `--employer`, `--binding-json`, `--quote-id`, `--provenance` |
| S3 | Admin API | Pass | `quote_id`, `provenance`, `principal` on `/query` |
| S4 | Admin UI | Pass | Quote panel, sticky quote_id, Accept quote, metering badges |
| S5 | `bin/demo-metering-negotiation` | **Fix** | Fails on step 2 without `MYCELIUM_USE_SYNC_CHECKPOINTER=1` (see below) |
| S6 | Docs | Pass | README “Testing metering negotiation”; crm-metering README |
| S7 | Tests | Pass | `test_cli_metering_query.py` + `test_admin_query_passes_quote_id` + layout test |

---

## Tests

```
uv run pytest tests/test_cli_metering_query.py tests/test_entity_metering.py \
  tests/test_entity_payment.py tests/test_admin_daemon.py tests/test_example_network.py -q
→ 60 passed
```

Ruff clean on touched Python files.

---

## Issue (fix before or immediately after commit)

### Issue 1 — Severity: bug

- **File:** `bin/demo-metering-negotiation` (bootstrap / `_configure_network`)
- **Description:** `./bin/demo-metering-negotiation` calls `run_query` three times in one process. Without `MYCELIUM_USE_SYNC_CHECKPOINTER=1`, step 2 raises `RuntimeError: ... bound to a different event loop`. CLI sets this in `src/main.py`; demo script does not.
- **Suggestion:** Set `os.environ["MYCELIUM_USE_SYNC_CHECKPOINTER"] = "1"` in `_bootstrap()` or `_configure_network()` (same pattern as CLI).
- **Status:** open

Verified: fails on fresh `crm-metering` refresh without env var; succeeds with `MYCELIUM_USE_SYNC_CHECKPOINTER=1`.

---

## Non-blocking nits

1. **Admin `dist/` not rebuilt in diff** — source updated; operators must `cd admin-ui && npm run build` (documented in crm-metering README). Acceptable for this slice.
2. **No automated test for `bin/demo-metering-negotiation` subprocess** — CLI in-process test covers same arc; optional follow-up.
3. **MCP fixtures** — `03-accept-quote.json` uses placeholder `QUOTE_ID`; documented.

---

## Recommendation

Fix sync checkpointer in demo script (one line), then commit:

```
Add metering negotiation test scaffolding (Slice 12).

crm-metering example, CLI bind/quote flags, admin quote accept UI,
bin/demo-metering-negotiation, and CLI/admin tests.
```

Mark Slice 12 done in `TODO.md` after commit.