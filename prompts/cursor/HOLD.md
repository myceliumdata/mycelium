# Cursor queue

**Active:** [`next/2026-06-14-1100-target-step1-lookup-clarity.md`](next/2026-06-14-1100-target-step1-lookup-clarity.md) — step-1 lookup clarity (outcomes, suggestions, confirm_new_entity)

**Supersedes:** `2026-06-14-1000-query-response-omit-empty-lists.md` (merged into 1100)

**Done (approved):** [`done/2026-06-14-0900-query-response-omit-na-fields/`](done/2026-06-14-0900-query-response-omit-na-fields/) — **Approved**

**Manual gate:** [`docs/manual-checks/2026-06-13-program2-post-program-gate.md`](../../docs/manual-checks/2026-06-13-program2-post-program-gate.md) — pending Paul run.

**Git:** Ahead of `origin/main`. No push until Paul asks. See `WORKFLOW.md` §4.

---

## Cursor: when you finish a slice

1. `./bin/ci-local` green
2. `done/<slice>/` with `prompt.md` + `output.md`
3. Remove prompt from **`in-progress/`** and **`next/`**
4. **Do not commit or push**
5. Tell Paul: **"slice ready for review"**

Full checklist: `prompts/cursor/WORKFLOW.md` §3.