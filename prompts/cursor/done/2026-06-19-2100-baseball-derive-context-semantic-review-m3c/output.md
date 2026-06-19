# M3c output — derive warehouse context + semantic review

## Done

- **`derive_resolve.py`** — `format_warehouse_context()` (grain, tables/row_count, conventions, alias patterns, execution environment). Shared across derive, fix, and review prompts. Removed hardcoded batting-average formatting rule.
- **Semantic review** — after successful `run_derive_function`, `invoke_llm_for_review()` + `parse_review_verdict()`; `DeriveReviewRejected` on REJECT or unparseable response → semantic fix prompt on next attempt (same attempt budget as M3b).
- **`warehouse_domains.json`** — generic batting conventions: `rate_from_aggregates`, `sqlite_integer_aggregates`.
- **Tests** — `CAREER_AVG_DERIVE_SQL_INT_DIV_SOURCE` fixture; `test_derive_review.py`; `test_career_avg_derive_retries_after_sql_integer_division` (reject `0.000` → accept `0.500`).
- **Smoke** — review auto-accept mock alongside codegen mock.

## Locked behavior

| Step | Behavior |
|------|----------|
| Codegen + run + review ACCEPT | Cache winning source (M3/M3b unchanged) |
| Run success + review REJECT | Counts as failed attempt; semantic fix prompt with full context |
| Execution error | Fix prompt with full manifest context (not error-only) |
| Unparseable review | Treated as reject → retry |
| End user | Final value or `N/A` only |
| Operator | `audit_log` / `operator_audit`: `attempt N review rejected: …` |

## Verification

```text
./bin/ci-local                    # 577 smoke passed
./bin/smoke-baseball-e2e          # 12 scenarios
```

## Manual (Paul)

Clear batting `storage.json`, refresh, re-run Aaron `career_avg` — expect ≈**0.305**. `operator_audit` may show execution failure, review rejection, then success. **Not run in CI** (requires live `OPENAI_API_KEY`).

## For Grok + Paul

- M3c complete; mark slice done on roadmap.
- Aaron manual gate pass/fail pending Paul.
- Review adds one extra LLM call per attempt that reaches successful execution (latency note for live derive).

## Suggested commit message

```
baseball: derive warehouse context + semantic review retry (M3c)
```
