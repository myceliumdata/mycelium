# M3b output — derive retry on execution error

## Done

- **`derive_resolve.py`** — `generate_and_run_derive()` retry loop (default **5** attempts via `MYCELIUM_DERIVE_MAX_ATTEMPTS`; invalid/zero → **5**). `build_fix_prompt()` feeds failed source + exception back to LLM. Catches `DeriveSourceError`, `sqlite3.Error`, `ValueError`, `TypeError`, `OSError`. Returns `DeriveRunResult(field, audit_log)`.
- **`batting_specialist.py`** — extends graph `audit_log` with derive attempt lines; fail-closed to `N/A` after exhaustion.
- **`tests/baseball_derive_fixtures.py`** — `CAREER_AVG_DERIVE_BAD_SOURCE` (`%s` placeholder → `OperationalError`).
- **`tests/test_baseball_career_avg_derive.py`** — mocks `invoke_llm_for_prompt`; retry success (bad→good → `0.500`); exhaust attempts → `N/A` + 5 LLM calls.
- **`bin/smoke-baseball-e2e`** — `_patch_career_avg_derive_mock` patches `invoke_llm_for_prompt`.
- **`docs/manual-checks/2026-06-19-baseball-specialist-hand-test.md`** — M3b-1 row (silent retries; check `audit_log`).

## Locked behavior

| Setting | Value |
|---------|-------|
| `MYCELIUM_DERIVE_MAX_ATTEMPTS` | Default `5`; non-integer or ≤0 → `5` |
| End-user JSON | Final value or `N/A` only — no retry narrative |
| Operator | `audit_log` lines: `derive career_avg attempt N failed …`, `succeeded on attempt N`, `failed after N attempts` |
| Provenance | Winning source only (same as M3) |

## Verification

```text
./bin/ci-local                    # 576 smoke passed
./bin/smoke-baseball-e2e          # 12 scenarios (career_avg_derive_mocked ok)
```

## Manual (Paul)

Re-run live Lahman Aaron `career_avg` after clearing stale batting cache — expect ≈**0.305** without MCP `outcome: error`. On bad first codegen, retries are silent to the client; inspect `audit_log` / debug for attempt lines.

## For Grok + Paul

- M3b complete; mark slice done on roadmap.
- Aaron manual gate not run in CI (requires live `OPENAI_API_KEY`).
- No `.env.example` change — `MYCELIUM_DERIVE_MAX_ATTEMPTS` documented here only unless you want it in example env comments.

## Suggested commit message

```
baseball: derive retry loop on execution error (M3b)
```
