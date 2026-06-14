# Fix multi-match step-2 deliver truncation when research gate fires

> **READY** — Move to `in-progress/` before starting (see `prompts/cursor/WORKFLOW.md`).

**Context (Paul + Grok, June 2026):** MCP/Claude reported step 1 `total_matches: 2` but step 2 returned **1** row. Root cause (separate from validation): when `research_gate_allows` fails for a batch (any `provisional` row with attrs requested), `assemble_response` calls `response_research_gated(query, matched[0])` — **M8 batch deliver bypassed**. Message incorrectly says “Found **provisional** record …” even when `matched[0]` is **validated**.

**Prerequisite:** Slice **`1400-provisional-validation-step2-deliver`** **Approved** and Paul manual validation test passed. After `1400`, live Wrong Corp may be `validated` — **do not rely on Paul's network**; use test fixtures.

**Related:** [`TODO.md`](../../TODO.md) item 0; M8 batch deliver [`tests/test_mvr_batch_deliver.py`](../../tests/test_mvr_batch_deliver.py).

---

## Read first

- [`src/agents/dispatch.py`](../../src/agents/dispatch.py) — `assemble_response_node` research-gate branch
- [`src/agents/responses.py`](../../src/agents/responses.py) — `response_research_gated`
- [`src/agents/research_gate.py`](../../src/agents/research_gate.py)
- [`docs/plans/entity-research-gate-phase6.md`](../../docs/plans/entity-research-gate-phase6.md)
- MCP policy `multi_match` (describe_network) — `results` should contain **every** match for disambiguation

---

## Required fixes

### A. Failing test first (mandatory)

Add smoke test **`test_multi_match_research_gate_returns_all_identity_rows`** (or similar):

1. Seed CRM + `bind_provisional("Andrea Kalmans", "Wrong Corp")` — Wrong Corp stays `provisional`; seed Andrea @ Lontra `validated`.
2. Step 1: `lookup: {name: "Andrea Kalmans"}`, `requested_attributes: ["email"]` → `total_matches: 2`.
3. Step 2: `delivery_id` only.
4. **Assert today (before fix):** documents bug — `len(results) == 1`.
5. **After fix:** `len(results) == 2`; both ids present; employers distinguish rows.

Use mocked email research if needed (see `test_mvr_batch_deliver.py`). When gate blocks research, attrs may be absent — identity fields (`id`, `name`, `employer`) must still appear for **all** scope entities.

### B. Return all N identity rows when batch is research-gated

When `is_research_gated(current)` and `len(matched) > 1` (or any gated batch):

- `results[]` must include **every** match in `matched_records` (same as identity-only batch deliver / `response_found` with `base_records=_identity_records_from_match(matched)`).
- Do **not** truncate to `matched[0]` only.

When gate fires for **single** provisional match, one row is fine.

### C. Fix message accuracy

Replace misleading template in `response_research_gated` when used for batch gating:

- Do not claim the returned row is “provisional” if `_validation_state == validated`.
- Prefer batch-level message, e.g. “N matches; attribute research blocked for M provisional row(s). Core validation must complete before researching requested attributes.”
- Or per-record status in `message` / `debug` — align with [`TODO.md`](../../TODO.md) per-record messages backlog if minimal fix is batch summary only.

### D. Preserve M8 behavior

All-validated multi-match + attrs must still return `assembled` with N rows (`test_batch_step2_deliver_with_attrs_researches_all_entities` unchanged).

---

## Out of scope

- Changing when research gate fires (gate logic stays; fix delivery shape)
- Provisional promotion (slice `1400`)
- Admin UI / MCP tool changes

---

## Verification

```bash
./bin/ci-local
```

**Paul manual (after Grok review + commit):**

Manufacture mixed state if live network no longer has provisional Wrong Corp:

```bash
# uv run python one-liner or pytest that prints step2 public_dict
# OR: bind_provisional via test helper on copy of network
```

1. Step 1 name-only Andrea → `total_matches: 2`
2. Step 2 deliver with attrs from step 1 → **`results` length 2** (identity fields at minimum)
3. Message does not call validated Lontra row “provisional”

---

## Governance

- Do not edit `TODO.md`.
- In `output.md` → **For Grok + Paul**: truncation fixed; test name; manual verify steps.
- Do not commit or push.

## When finished

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-14-1410-multi-match-step2-deliver-truncation/`
3. Remove from `in-progress/` and `next/`
4. Tell Paul **slice ready for review**

---

## Exit criteria

- Research-gated multi-match step-2 returns **N** identity rows in `results[]`
- Message accurate for mixed validated/provisional batch
- M8 all-validated batch tests still green
- `./bin/ci-local` green

Suggested commit message:

```
fix(query): return all matches when step-2 research gate blocks attrs

Multi-match deliver no longer truncates to matched[0]; fix gated
message for mixed validated/provisional batches.
```