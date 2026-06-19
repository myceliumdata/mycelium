# Review — baseball derive warehouse context + semantic review (M3c)

**Verdict:** **Approved + polish nits**  
**Reviewer:** Grok  
**Date:** 2026-06-19

## CI

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **577** smoke passed, ruff clean, admin-ui build ok |
| `./bin/smoke-baseball-e2e` | **12** scenarios passed (`career_avg_derive_mocked` ok) |
| M3c tests | `test_derive_review.py` (5), `test_career_avg_derive_retries_after_sql_integer_division` |

## Delivery

`output.md` matches implementation. M3c-scoped files complete; unrelated dirty tree (fuzzy / `entity_resolution`) excluded from commit.

| File | Role |
|------|------|
| `derive_resolve.py` | `format_warehouse_context`, unified fix prompt, review loop, `DeriveReviewRejected` |
| `warehouse_domains.json` | `rate_from_aggregates`, `sqlite_integer_aggregates` conventions |
| `baseball_derive_fixtures.py` | `CAREER_AVG_DERIVE_SQL_INT_DIV_SOURCE` |
| `test_derive_review.py` | Context formatter + verdict parsing + int-div fixture |
| `test_baseball_career_avg_derive.py` | E2E int-div → review reject → good source; review mock on all derive tests |
| `bin/smoke-baseball-e2e` | `fake_review` auto-accept (reject `VALUE: 0.000`) |
| Hand-test doc | M3c-1 row |

## Diff reviewed

Full read of M3c files (~+180 lines in `derive_resolve.py`, manifest, fixtures, tests, smoke, hand-test). Confirmed no framework output validators, no per-attribute specs, no H/AB re-query.

## Spec compliance

| Criterion | Result |
|-----------|--------|
| No per-attribute output specs / rule-engine validation | Pass |
| No hardcoded `career_avg` / batting-average prompt line | Pass — removed; “infer from column semantics” |
| Generic manifest conventions (environmental facts) | Pass |
| Full manifest context on derive, fix, and review prompts | Pass |
| Post-execution LLM semantic review before cache | Pass |
| Review REJECT → retry within same attempt budget | Pass |
| End user: value or `N/A` only | Pass |
| Operator: `audit_log` / `operator_audit` for review rejections | Pass (`attempt N review rejected`) |
| `derive_candidates` list unchanged (M3 gate) | Pass |
| Tests: SQL int-div + review reject → `0.500` | Pass |

## Design critique

**Strong:** Matches Paul’s direction — environmental context + LLM self-correction, not anticipated-answer validation. `format_warehouse_context()` is reusable toward M4/M5 (NL derive). Merging execution-fix and semantic-fix into one `build_fix_prompt()` keeps retry paths coherent. `DeriveReviewRejected` guarded so it does not masquerade as a sandbox `ValueError` in the execution handler.

**Trade-off:** Every successful execution now costs **two** live LLM calls (codegen + review). Acceptable for M3 guinea pig; revisit if review becomes always-on at M4 scale (e.g. env toggle or review only after suspicious patterns).

## Nits (non-blocking)

| # | Nit | Follow-up |
|---|-----|-----------|
| N1 | Live review quality is model-dependent — CI mocks review; Aaron manual gate still required | Paul hand-test after clearing batting `storage.json` |
| N2 | Good fixture returns `"0.000"` when `AB == 0` — would fail auto-review mock if that path is hit | Future: derive should return `N/A` for undefined average, or review prompt notes zero-AB case |
| N3 | `_format_alias_pattern` has convention-specific branches | Fine for manifest introspection; generalize when more convention kinds ship |

## For Paul

- **Commit message:** `baseball: derive warehouse context + semantic review retry (M3c)`
- **Manual:** Clear `~/mycelium-networks/baseball/agents/batting/storage.json`, refresh, re-run `career_avg` — expect ≈**0.305**; `debug.operator_audit` may show execution failure, review rejection, then success.
- **Unrelated dirty files** left unstaged (fuzzy slice).