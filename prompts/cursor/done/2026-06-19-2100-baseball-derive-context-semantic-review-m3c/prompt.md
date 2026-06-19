# Baseball derive — rich warehouse context + LLM semantic review (M3c)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md`. **After M3b** (`2026-06-19-1900`) + debug nit (`3653cd6`) on `main`.

**Priority:** Fix live `career_avg: "0.000"` when codegen **runs** but returns a wrong answer (SQLite integer division in SQL). Do **not** encode per-attribute output rules or warehouse ground-truth checks in framework code.

**Parent:** Paul design lock (June 2026): `derive_candidates` is M3 training wheels; long-term path is M4/M5 open derive where the LLM infers constraints from **warehouse environment context**, not from anticipated answer keys. Retry stays **LLM-mediated** (execution errors **and** semantic review), not rule-engine validation.

**Principles:**

- **No** per-attribute output specs (`unit_interval_rate`, `career_avg` validators, H/AB re-queries).
- **No** hardcoded stat names in prompts (remove `"For batting averages use three decimal places"`).
- **Yes** generic manifest **conventions** and **execution environment** facts (grain, stint, SQLite arithmetic, rate-from-aggregates pattern).
- **Yes** full manifest context on **every** retry prompt (fix + review-reject), not error text alone.
- **Yes** post-execution **semantic review** LLM pass before accepting a result — model decides plausibility from context.
- **End user:** still only final value or `N/A`; no retry narrative in `message`.
- **Operator:** `audit_log` + `debug.operator_audit` for execution failures **and** review rejections.
- **Fail-closed:** max attempts exhausted → `write_na_field`; never MCP `outcome: error`.
- **Do not edit `TODO.md`.**

---

## Problem (Paul live test)

| Attempt | Outcome | Value |
|---------|---------|-------|
| 1 | `OperationalError` (`%s`) | — |
| 2 | Ran clean | `"0.000"` (wrong — SQL `SUM(H)/SUM(AB)` integer truncation) |

M3b accepts any successful execution. Fix prompt on attempt 2 lacked manifest context and did not question plausibility.

---

## Objective

1. **Rich shared context block** — single helper used by derive, fix, and review prompts.
2. **Generic manifest conventions** — environmental facts, not `career_avg` answer keys.
3. **Semantic review step** — after `run_derive_function` succeeds, one LLM call asks “is this result plausible given context?” before cache.
4. **Review rejection → retry** — same attempt budget as M3b; fix prompt includes manifest context + returned value + rejection reason.

`derive_candidates` list unchanged for M3 scope gate.

---

## Locked behavior

| Case | Behavior |
|------|----------|
| Codegen + run success + review **ACCEPT** | Cache winning source (same as M3/M3b) |
| Codegen + run success + review **REJECT** | Counts as failed attempt; semantic fix prompt; retry |
| Execution error (M3b) | Fix prompt **with full manifest context**; retry |
| All attempts exhausted | `N/A`; audit lists execution + review failures |
| Review LLM parse failure / empty | Treat as `DeriveReviewRejected("unparseable review response")` → retry |
| `MYCELIUM_DERIVE_MAX_ATTEMPTS` | Default `5` (unchanged) |

**Attempt loop (one iteration):**

```
codegen → run_derive_function → [on error: fix+continue]
                              → review_llm → [REJECT: semantic fix+continue]
                              → ACCEPT: return DeriveResolvedField
```

Each loop iteration consumes one attempt number (review reject does not add a second attempt counter inside the same iteration).

---

## Implement

### 1 — Shared context formatter (`derive_resolve.py`)

Extract `format_warehouse_context(manifest, domain) -> str` including:

- **Domain** name, **grain** (explicit note: multiple rows per player when grain includes `stint` / `yearID`).
- **Tables** from manifest `tables` block: name, `row_count`, column list.
- **Conventions** (sorted key → rule) from `warehouse_domains.json`.
- **Alias patterns** (read-only examples, not instructions to copy blindly):
  ```
  Resolved alias patterns in this domain (committed code uses these):
  - career_hr: career_sum on column HR
  - career_rbi: career_sum on column RBI
  ...
  ```
  Derive from `domains[domain].aliases` + convention names — no hardcoded attr list in Python beyond walking manifest.
- **Execution environment** (static block or convention-driven):
  - SQLite read-only warehouse via `query_warehouse(warehouse, sql, params)`.
  - Integer aggregates stay integer; **ratio/rate arithmetic should happen in Python** after fetching separate aggregates unless explicitly cast.
  - Placeholder style: `?` for sqlite3 (errors on wrong placeholders are retried via M3b).

Use this block in `build_derive_prompt`, `build_fix_prompt`, and `build_review_prompt`.

### 2 — Manifest conventions (`warehouse_domains.json`)

Add **generic** batting conventions (wording is environmental, not `career_avg`-specific):

```json
"rate_from_aggregates": "For career rate stats from counting columns: SUM each operand across all domain grain rows for playerID, then divide in Python",
"sqlite_integer_aggregates": "SUM of integer columns returns integers; do not rely on SQL division for ratios"
```

Optional one-line grain note in conventions or context formatter: stint ⇒ aggregate before career rates.

**Do not** add `derive_candidates` object map or per-attribute output specs.

### 3 — Prompt builders

**`build_derive_prompt`**

- Use `format_warehouse_context`.
- Ask for `compute(player_id, warehouse) -> str` for the given **attribute label** (M3) — phrased as “derive this attribute from the warehouse using the context above; infer appropriate units, aggregation, and formatting from column semantics and conventions.”
- **Remove** line: `For batting averages use three decimal places`.
- Keep sandbox rules (no imports, `query_warehouse` only).

**`build_fix_prompt`** (execution errors)

- Include **full** `format_warehouse_context` (not just attr/domain).
- Error + failed source (truncated 8k) + same sandbox rules.

**`build_review_prompt`** (new)

```text
<format_warehouse_context>

Attribute requested: <attr>
player_id used in test run: <player_id>  (helps model reason about plausibility)

The following function executed without error and returned:
VALUE: <value>

Source:
```python
<source>
```

Given the warehouse context above, is VALUE a plausible answer for the requested attribute?

Reply in this exact format (no code):
VERDICT: ACCEPT
or
VERDICT: REJECT
REASON: <one short paragraph>
```

**`build_semantic_fix_prompt`** (review reject)

- Full manifest context.
- Prior source, returned value, REASON from review.
- “Write a corrected compute function. Output only Python.”

Alternatively merge semantic fix into one `build_fix_prompt(..., *, review_reason=None)` — pick one clean path.

### 4 — Review orchestration

- `class DeriveReviewRejected(ValueError)` in pack with `.reason: str`.
- `parse_review_verdict(text) -> tuple[Literal["accept","reject"], str]`.
- `invoke_llm_for_review(prompt, *, review_llm_invoke=None)` — same model/env as codegen when live; separate hook for tests.
- In `generate_and_run_derive`:
  - After successful `run_derive_function`, call review.
  - ACCEPT → succeed (audit: `succeeded on attempt N`).
  - REJECT → `last_error = DeriveReviewRejected(reason)`, audit: `attempt N review rejected: <reason>`, continue loop with semantic fix prompt on next iteration.

Catch `DeriveReviewRejected` only inside the loop (not outward).

### 5 — Operator logging

Audit lines (extend M3b patterns):

- `batting_specialist: derive career_avg attempt 2 review rejected: implausible …`
- `batting_specialist: derive career_avg succeeded on attempt 3`

`operator_audit` in MCP debug already surfaces `: derive ` lines — no `dispatch.py` change unless new line format breaks filter (keep `: derive ` substring).

### 6 — Tests

**Fixtures (`tests/baseball_derive_fixtures.py`)**

```python
CAREER_AVG_DERIVE_SQL_INT_DIV_SOURCE
```

SQL `SUM(H) / NULLIF(SUM(AB), 0)` with `?` — runs, returns `"0.000"` on fixture (4 H / 8 AB).

**Review mock helper**

Tests pass `review_llm_invoke` (or detect review prompts in combined mock):

- Auto-**REJECT** when prompt contains `VALUE: 0.000` (or `VALUE: "0.000"`).
- Auto-**ACCEPT** otherwise.

**`tests/test_baseball_career_avg_derive.py`**

| Test | Mock sequence | Expect |
|------|---------------|--------|
| `test_career_avg_derive_retries_after_sql_integer_division` | codegen: `[SQL_INT_DIV, GOOD_SOURCE]`; review: reject 0.000, accept 0.500 | `0.500`; audit has review rejected + succeeded |
| `test_career_avg_derive_retries_after_sqlite_error` | existing bad `%s` → good (review accept both or accept only final) | still passes |
| Existing mocked/provenance/cache tests | review auto-accept | unchanged outcomes |

**`tests/test_derive_review.py`** (new, small)

- `parse_review_verdict` ACCEPT/REJECT parsing.
- `format_warehouse_context` includes grain, conventions, alias patterns from minimal manifest dict.

No live OpenAI in CI.

### 7 — Docs (minimal)

- **`docs/manual-checks/2026-06-19-baseball-specialist-hand-test.md`** — M3c row: derive uses manifest context + LLM semantic review; implausible results retry silently; clear batting storage if bad value cached.
- **`prompts/cursor/done/.../output.md`** — note Paul manual gate.

Optional: one sentence in `examples/networks/baseball/README.md` under derive — only if README already mentions M3.

---

## Non-goals

- Framework `validate_derive_output` / typed output specs
- Per-attribute manifest maps
- Warehouse H/AB ground-truth re-query in Python
- SQLite/placeholder encyclopedia in attempt-1 prompt
- NL `question` derive (M4) — but context formatter should be reusable
- Second derive model env var (use same `MYCELIUM_DERIVE_MODEL` unless tests need split hooks only)
- Exposing review transcripts in client `provenance`

---

## Verification

```bash
uv run pytest tests/test_baseball_career_avg_derive.py tests/test_derive_review.py tests/test_derive_sandbox.py -q
./bin/ci-local
./bin/smoke-baseball-e2e
```

**Manual (Paul):**

```bash
rm -f ~/mycelium-networks/baseball/agents/batting/storage.json
./bin/refresh-example-network baseball --sync-only
```

Re-run `career_avg` on Hank Aaron — expect ≈ **0.305**; `debug.operator_audit` may show execution failure, review rejection, then success.

**Step 1:**

```json
{
  "lookup": {"player": "Hank Aaron"},
  "requested_attributes": ["career_avg"],
  "provenance": true
}
```

**Step 2:** `{"delivery_id": "<from step 1>"}`

---

## For Grok + Paul (`output.md`)

- M3c done; manual Aaron gate pass/fail.
- Note whether review added noticeable latency (one extra LLM call per attempt that reaches successful execution).

**Suggested commit message:**

```
baseball: derive warehouse context + semantic review retry (M3c)
```