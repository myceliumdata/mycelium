# Cursor queue

**Active:** [`next/2026-06-14-1000-query-response-omit-empty-lists.md`](next/2026-06-14-1000-query-response-omit-empty-lists.md) — omit empty `required_fields`/`suggestions`, null `trace_id`

**Done (approved):** [`done/2026-06-14-0900-query-response-omit-na-fields/`](done/2026-06-14-0900-query-response-omit-na-fields/) — **Approved**

**Prior:** [`done/2026-06-14-0800-example-network-capstone-tests-gate-pairing/`](done/2026-06-14-0800-example-network-capstone-tests-gate-pairing/) — **Approved**

**Manual gate:** [`docs/manual-checks/2026-06-13-program2-post-program-gate.md`](../../docs/manual-checks/2026-06-13-program2-post-program-gate.md) — pending Paul run.

**Next:** Push after gate CLEAR; **Program 3** = entity protocol legacy cleanup.

**Git:** Ahead of `origin/main`. No push until Paul asks. See `WORKFLOW.md` §4.

---

## Cursor: when you finish a slice

1. `./bin/ci-local` green
2. `done/<slice>/` with `prompt.md` + `output.md`
3. Remove prompt from **`in-progress/`** and **`next/`**
4. **Do not commit or push**
5. Tell Paul: **"slice ready for review"**

Full checklist: `prompts/cursor/WORKFLOW.md` §3.