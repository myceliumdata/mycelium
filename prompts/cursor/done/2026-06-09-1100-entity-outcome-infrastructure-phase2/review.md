# Review: Entity outcome infrastructure — Slice 2

**Reviewer:** Grok  
**Date:** 2026-06-09  
**Verdict:** **Approved**

---

## Spec coverage

| Item | Status |
|------|--------|
| All `response_*` builders set public `outcome` matching debug | Pass |
| `response_non_core` → `assembled` (locked rule) | Pass |
| Graph empty fallback → `error` | Pass |
| MCP internal error JSON includes `outcome` | Pass |
| `policy.outcome` in introspection | Pass |
| `tests/test_query_response_outcomes.py` (8 tests) | Pass |
| `test_supervisor_routing.py` outcome assertions | Pass |
| README paragraph | Pass |
| No new negotiation logic | Pass |

Slice 2 changes left **uncommitted** until this review — correct governance.

---

## Smoke suite — two recurring local failures

**Not caused by Slice 2.** See fix slice `1105` and explanation for Paul below.

| Test | Root cause | Product bug? |
|------|------------|--------------|
| `test_bootstrap_fails_when_unconfigured` | `bootstrap_admin()` calls `load_dotenv()` after monkeypatch clears env → `.env` restores `MYCELIUM_NETWORK=crm` | No — test isolation |
| `test_create_specialist_writes_files_and_registers` | `.env` API keys → sync research runs → `na` not `pending` | No — test isolation |

CI (no `.env`) likely passes; failures appear on dev machines with `examples/.env` or repo `.env`.

---

## Gate

**Slice 3 (`1200`)** unblocked. Recommend **`1105` test hygiene** before relying on local `pytest -m smoke` as green (non-blocking for protocol slices).