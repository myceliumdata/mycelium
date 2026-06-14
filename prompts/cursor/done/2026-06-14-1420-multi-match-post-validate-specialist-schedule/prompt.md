# Fix multi-match same-turn specialist scheduling after batch validate

> **READY** — Move to `in-progress/` before starting (see `prompts/cursor/WORKFLOW.md`).

**Context (Paul + Grok, June 2026):** After slice `1400`, multi-match step-2 deliver with attrs can promote a provisional row in `validate_entity`, but **specialists never run in the same turn**. Supervisor defers invoke when any row is provisional; `validate_entity_node` only re-schedules specialists when `len(matched) == 1`. Result: `assembled` with `contributions=0`, email in `researching` bucket, `results[]` id-only until a **second** query.

**Paul repro (live CRM):** Demote Andrea @ Wrong Corp to `provisional`; step 1 `lookup: {name: Andrea Kalmans}` + `email`; step 2 deliver → Wrong Corp promotes but no emails. Re-run (both validated) works.

**Prerequisite:** Slices `1400` and `1410` approved on `main`.

**Out of scope:** Research gate policy changes; admin/MCP; single-match paths (already work).

---

## Read first

- [`src/agents/dispatch.py`](../../src/agents/dispatch.py) — `validate_entity_node` (lines ~414–442 single-match-only reschedule), `invoke_specialists_node`
- [`src/agents/supervisor.py`](../../src/agents/supervisor.py) — deferred specialist scheduling when provisional
- [`src/graphs/core.py`](../../src/graphs/core.py) — `_route_after_metering` / `_specialists_planned`
- [`tests/test_mvr_create_on_deliver.py`](../../tests/test_mvr_create_on_deliver.py) — `test_multi_match_step2_promotes_provisional_bind` (extend)
- [`tests/test_mvr_batch_deliver.py`](../../tests/test_mvr_batch_deliver.py) — M8 batch patterns + mocked research

---

## Required fix

### A. Re-schedule specialists after batch validation (multi-match)

In `validate_entity_node`, after promoting provisional row(s), when **all** of the following hold:

- `graph_requested_attributes(current)` non-empty
- `current.classifications` present
- `research_gate_allows(matched=updated_matches)` (gate open — all rows validated)
- Batch had at least one provisional processed **or** supervisor left `specialists_to_invoke` empty while attrs requested

Then schedule specialists for **multi-match** the same way as single-match today:

- `_collect_specialists_to_invoke(classifications, audit)`
- `planner_context(matched=updated_matches, ids=[all entity ids], specialists_to_invoke=...)`
- Set `context` on state so `_specialists_planned` routes to `build_context` → `invoke_specialists`

**Do not** schedule when gate still closed (any row still provisional after validation, e.g. employer `"A"` failure).

Prefer generalizing the existing single-match block (`len(matched) == 1` guard → `research_gate_allows` + attrs requested) rather than duplicating logic.

### B. Tests (smoke — mandatory)

Extend **`test_multi_match_step2_promotes_provisional_bind`** (already mocks email research):

| Assert | |
|--------|--|
| Wrong Corp `validation_state: validated` | keep |
| `step2.outcome == "assembled"` | |
| `len(step2.results) >= 2` | |
| Every result row has `email` populated (mock value) | **new — core proof** |
| `contributions > 0` in debug or research calls hit both entity ids | |

Optional: assert `test_multi_match_research_gate_returns_all_identity_rows` still passes (gate closed → still no invoke).

### C. Preserve existing behavior

| Path | Unchanged |
|------|-----------|
| Single-match promote + attrs | still researches same turn |
| Research-gated multi-match (provisional remains) | no specialist invoke |
| M8 all-validated batch deliver | unchanged |
| Identity-only step-2 (no attrs) | unchanged |

---

## Verification

```bash
./bin/ci-local
```

**Paul manual (after Grok review):**

1. Demote Wrong Corp to `provisional` in `entities.json`
2. Step 1 Andrea name + `email` → step 2 deliver **once**
3. Wrong Corp `validated` **and** both rows have `email` in `results` (with API keys) or `assembled` + contributions without re-query

---

## Governance

- Do not edit `TODO.md`.
- In `output.md` → **For Grok + Paul**: closes 1400 nit N1; manual steps.
- Do not commit or push.

## When finished

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-14-1420-multi-match-post-validate-specialist-schedule/`
3. Remove from `in-progress/` and `next/`
4. Tell Paul **slice ready for review**

---

## Exit criteria

- Multi-match step-2: provisional promotes + attrs research in **same turn** when gate opens after validate
- Gated multi-match (provisional remains) still skips invoke
- `./bin/ci-local` green

Suggested commit message:

```
fix(query): schedule specialists after multi-match batch validation

Re-invoke attribute specialists in the same turn when validate_entity
promotes the last provisional row and the research gate opens.
```