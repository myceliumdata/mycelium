# Review: MCP slice 3 — query-time messages (`2026-06-08-1500`)

**Verdict: Approve — ready to commit and push**

Implementation matches the prompt. The main risks from pre-review (empty-contributions path, out-of-scope wording, unified `assemble_response`) are all addressed. Smoke tests pass; architecture and TODO updated.

---

## What looks good

| Area | Notes |
|------|--------|
| **`build_query_message()`** | Classification-aware copy; category names, not module names; no `(via specialist)` suffixes |
| **Buckets** | `partition_attribute_buckets()` → found / researching / unavailable / out_of_scope |
| **`assemble_response_node`** | Single path through `response_assembled` + `build_query_message`; no `response_non_core` branch |
| **Out-of-scope** | All-unknown queries say “does not appear related”; no “researching” (smoke test #1) |
| **Mixed queries** | In-scope + garbage in one message (smoke test #2) |
| **Multi-match** | Collective `Found 2 records for 'Kevin Zhang'.` prefix (smoke test #3) |
| **Not found** | Short neutral copy: `No record found for '…'.` (smoke test #4) |
| **Specialist spin-up** | `_new_specialist_categories()` reads supervisor audit log for “setting up a {category} specialist” |
| **`debug`** | Explicit bucket lists merged into `response.debug` |
| **Docs / TODO** | `architecture.md` message contract; MCP onboarding slices 1–3 marked done |

**Smoke (review run):**

```text
tests/test_query_messages.py + test_core_graph + test_supervisor_routing + test_specialist_research_integration  → 22 passed
Full smoke suite  → 143 passed (1 pre-existing flake: test_langsmith_utils.py::test_custom_ui_base)
ruff check (slice 3 files)  → clean
```

---

## Required risks — resolved in slice 3

| Risk | Status |
|------|--------|
| Empty-contributions / all-unknown path | Fixed — `assemble_response` always uses `build_query_message`; out-of-scope-only never says “researching” |
| Mixed in-scope + garbage | Covered by smoke test |
| Multi-match collective message | Covered by Kevin Zhang smoke test |
| Debug buckets | Present in `response_assembled` / `response_non_core` debug |

---

## Minor nits (non-blocking)

1. **Unavailable bucket — weak positive assertion** — `test_run_query_email_na_in_same_response_when_research_mocked` asserts the old copy is gone but does not assert the new “not found for this record” sentence. Behavior is correct; a one-line positive assert would lock the contract.
2. **Found bucket — no dedicated smoke test** — Found values correctly omitted from `message` (integration test asserts email value not in message when mocked found). Optional: explicit `found=['email']` debug assert in that test.
3. **Specialist-internal / template copy** — Framework specialists and Jinja template still `model_copy` legacy messages after `response_non_core`; graph `assemble_response` is authoritative for CLI/MCP (as spec allows). Align template in a future polish pass if desired.
4. **`response_non_core` retained** — Still used by `routing.py` and specialist modules; now delegates to `build_query_message`, so non-graph paths also get new copy unless specialist overrides win.
5. **Uncommitted** — Slice 3 changes still on working tree; commit + push after approval.
6. **Paul MCP verify** — TODO notes restart + live `query_entity` with mixed attrs recommended post-merge.

---

## Out of scope (correctly deferred)

- Per-record multi-match messages (`TODO.md`)
- Thread checkpoint stale `response` on reused `thread_id`
- Specialist template message cleanup
- MCP slice 4 polish

---

## Unblocks

MCP onboarding **implementation complete** (slices 1–3). Next: **slice 4 polish** or **Paul MCP restart verify**, then admin daemon / other backlog per `TODO.md`.