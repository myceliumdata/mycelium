# Review — baseball derive retry on execution error (M3b)

**Verdict:** **Approved + polish nits**  
**Reviewer:** Grok  
**Date:** 2026-06-19

## CI

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **576** smoke passed, ruff clean, admin-ui build ok |
| `./bin/smoke-baseball-e2e` | **12** scenarios passed (`career_avg_derive_mocked` ok) |
| M3b tests | `test_career_avg_derive_retries_after_sqlite_error`, `test_career_avg_derive_exhausts_attempts_to_na` |

## Delivery

`output.md` matches working-tree implementation (uncommitted at review time). All prompt deliverables present.

| File | Role |
|------|------|
| `derive_resolve.py` | Retry loop, `build_fix_prompt`, `DeriveRunResult`, `invoke_llm_for_prompt` |
| `batting_specialist.py` | Merges `derive_result.audit_log` into graph `audit_log` |
| `baseball_derive_fixtures.py` | `CAREER_AVG_DERIVE_BAD_SOURCE` (`%s` → `OperationalError`) |
| `test_baseball_career_avg_derive.py` | Retry + exhaust tests |
| `bin/smoke-baseball-e2e` | Patches `invoke_llm_for_prompt` |
| Hand-test doc | M3b-1 row |

## Diff reviewed

Full read of M3b-scoped files (~+200 lines in `derive_resolve.py`, batting wiring, tests, smoke, doc). Unrelated dirty tree (fuzzy, `entity_resolution`) excluded from commit.

## Spec compliance

| Criterion | Result |
|-----------|--------|
| No initial-prompt dialect bloat | Pass — `build_derive_prompt` unchanged |
| Retry on execution/sandbox errors (max 5, env override) | Pass |
| Fix prompt includes error + failed source | Pass |
| `sqlite3.Error` caught — no MCP `outcome: error` | Pass |
| End user sees value or `N/A` only | Pass |
| Provenance: winning source only | Pass |
| Operator `audit_log` lines on derive | Pass (graph state) |
| Tests: bad→good retry, 5× exhaust → `N/A` | Pass |

## Design critique

**Strong:** Matches Paul’s direction — self-correction over finicky prompts. `invoke_llm_for_prompt` extraction makes mocking clean. `DeriveRunResult` keeps batting specialist thin. Bad-source fixture exactly reproduces live `%` failure class.

**Nit:** Derive `audit_log` lines accumulate in LangGraph `state.audit_log` but are **not** appended to `QueryResponse.debug` today — MCP `query_entity` clients may not see retry lines unless LangSmith/admin adds audit surfacing. Hand-test says “check `audit_log` / debug”; debug string today has routing/contrib counts, not full audit tail.

## Nits (non-blocking)

| # | Nit | Follow-up |
|---|-----|-----------|
| N1 | Operator visibility — retry lines not in MCP `debug` | Future: append derive audit tail to `debug_extra` in `assemble_response` or admin audit panel |
| N2 | Retry test doesn’t assert `audit_log` content in graph | Optional test via debug/contrib hook |

## For Paul

- **Commit message:** `baseball: derive retry loop on execution error (M3b)`
- **Manual:** Re-run Hank Aaron `career_avg` — expect `≈0.305` without `outcome: error`; if first codegen fails, retries are silent (up to 5 LLM calls).
- **Clear batting storage** if stale `N/A` from pre-M3b error run.