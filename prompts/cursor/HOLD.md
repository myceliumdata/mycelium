# Cursor queue

**Active:** *(empty — awaiting next slice)*

**Last approved:** [`done/2026-06-14-1300-admin-restore-inspect-split-query-layout/`](done/2026-06-14-1300-admin-restore-inspect-split-query-layout/) — **Approved + polish nits**

**Manual gate:** [`docs/manual-checks/2026-06-13-program2-post-program-gate.md`](../../docs/manual-checks/2026-06-13-program2-post-program-gate.md) — run Check 0c-vi after 1300 (inspect vs query)

**Git:** Ahead of `origin/main`. No push until Paul asks. See `WORKFLOW.md` §4.

---

## Cursor: when you finish a slice

1. `./bin/ci-local` green
2. `done/<slice>/` with `prompt.md` + `output.md`
3. Remove prompt from **`in-progress/`** and **`next/`**
4. **Do not commit or push**
5. Tell Paul: **"slice ready for review"**

Full checklist: `prompts/cursor/WORKFLOW.md` §3.