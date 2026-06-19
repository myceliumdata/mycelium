# Baseball derive retry-on-execution-error (M3b)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md`. **After M3** (`2026-06-19-1800`) on `main`.

**Priority:** Fix live `career_avg` failures (e.g. `OperationalError: near "%": syntax error`) without bloating the derive prompt with database dialect docs. **Retry loop:** feed execution/sandbox errors back to the LLM until success or max attempts.

**Parent:** M3 review + Paul design lock (June 2026): prefer LLM self-correction over finicky prompt contracts; max **5** tries; operator-visible logs; end user sees only final value or `N/A`.

**Principles:**

- **Do not expand** `build_derive_prompt()` with SQLite/placeholder encyclopedia — keep manifest context only.
- **End user / public JSON:** no retry narrative; `career_avg` is `0.305` or `N/A` like any other attr.
- **Operator visibility:** `audit_log` (and `response.debug` when present) records attempt count, error types, final outcome — not full LLM transcripts unless already in debug patterns.
- **Fail-closed:** after max attempts → `write_na_field`; **never** propagate `sqlite3.OperationalError` (or any derive exception) to MCP `outcome: error`.
- **Provenance:** cache **final successful** `computation.inline` only (not failed attempts).
- **M2 + M3 cache-hit paths unchanged.**
- **Do not edit `TODO.md`.**

---

## Objective

Replace M3 single-shot `generate_and_run_derive()` with a **retry loop** (default **5** attempts, env `MYCELIUM_DERIVE_MAX_ATTEMPTS`):

1. **Attempt 1:** existing manifest prompt → `generate_derive_source` → `validate_derive_source` → `run_derive_function`.
2. **On failure** (`DeriveSourceError`, `sqlite3.Error`, `ValueError`, `TypeError`, `OSError`): build a **fix prompt** containing:
   - prior generated source (truncated if huge, e.g. 8k chars)
   - exception type + message (e.g. `OperationalError: near "%": syntax error`)
   - same rules as attempt 1 (single `compute`, `query_warehouse` only, no imports)
3. **Retry** until success or max attempts exhausted.
4. Return `DeriveResolvedField` on success; `None` on exhaustion → batting `write_na_field`.

**Guinea pig regression:** mocked LLM that returns `%s` SQL on attempt 1 and correct `?` SQL on attempt 2 → deliver `0.500` on fixture without live API key.

---

## Locked behavior

| Case | Behavior |
|------|--------|
| Attempt 1 success | Same as M3 — cache, provenance |
| Attempt 2–5 success after error | Cache **winning** source only |
| All attempts fail | `N/A`; audit_log lists attempts + last error |
| Uncaught exception in derive path | **Forbidden** — must not reach `run_query` / MCP |
| `MYCELIUM_DERIVE_MAX_ATTEMPTS` | Default `5`; invalid/zero → treat as `5` or `1` (pick one, document in `output.md`) |

**Fix prompt shape (pack `derive_resolve.py`):**

```text
The previous derive function failed when executed.

Error: <type>: <message>

Failed source:
```python
<source>
```

Write a corrected compute(player_id, warehouse) function. Same rules as before.
Output only the Python function.
```

Do **not** add database brand names or placeholder cheat-sheets to the **initial** prompt — only error text on retries.

---

## Implement

### 1 — `derive_resolve.py` retry orchestration

- Refactor `generate_and_run_derive()` to loop `max_attempts`.
- Extract `_build_fix_prompt(attr, manifest, domain, *, source, error)` for attempts 2+.
- Catch **`sqlite3.Error`** (includes `OperationalError`) in the retry loop.
- Optional: `computation["derive_attempts"]` = winning attempt number in provenance metadata (integer only) — not required for v1.

### 2 — Operator logging

- `batting_specialist` `audit_log` entries when derive runs, e.g.:
  - `batting_specialist: derive career_avg attempt 1 failed OperationalError near "%"`
  - `batting_specialist: derive career_avg succeeded on attempt 2`
  - `batting_specialist: derive career_avg failed after 5 attempts`
- Ensure logs appear in graph state / MCP `debug` blob operators already inspect (follow existing specialist patterns).

### 3 — Tests

- **`tests/test_baseball_career_avg_derive.py`** (or new `test_derive_retry.py`):
  - Mock `llm_invoke` sequence: bad `%s` source first, good source second → `0.500`.
  - Mock always-bad → `N/A`, audit or internal hook asserts 5 attempts (spy on call count).
  - Assert no exception escapes `generate_and_run_derive`.
- **`tests/test_derive_sandbox.py`:** unchanged or add one case if needed.

### 4 — Docs (minimal)

- **`docs/manual-checks/2026-06-19-baseball-specialist-hand-test.md`** — one line: derive may retry silently; check `audit_log` / debug for attempt count if debugging.

---

## Non-goals

- Prompt dialect / `warehouse_query` contract JSON
- Exposing retry history in `provenance.entities[]` to clients
- Metering line items per derive attempt (deferred)
- Postgres adapter

---

## Verification

```bash
./bin/ci-local
uv run pytest tests/test_baseball_career_avg_derive.py tests/test_derive_sandbox.py -q
./bin/smoke-baseball-e2e
```

Manual (Paul): re-run `career_avg` on live Lahman Aaron — expect `≈0.305` without MCP `outcome: error`.

---

## For Grok + Paul (`output.md`)

- M3b done; note whether Aaron manual gate passed.
- Suggest `MYCELIUM_DERIVE_MAX_ATTEMPTS` in `.env.example` comment only if added.

**Suggested commit message:**

```
baseball: derive retry loop on execution error (M3b)
```