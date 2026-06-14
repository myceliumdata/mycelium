# Cursor queue

**Active:** [`next/2026-06-14-1215-admin-query-confirm-new-entity-wire.md`](next/2026-06-14-1215-admin-query-confirm-new-entity-wire.md) — admin confirm_new_entity wire (blocking fix from 1200 review)

**Last approved:** [`done/2026-06-14-1200-admin-query-unified-mvr-lookup/`](done/2026-06-14-1200-admin-query-unified-mvr-lookup/) — **Approved + fix slice** (Grok, 2026-06-14)

**Manual gate:** [`docs/manual-checks/2026-06-13-program2-post-program-gate.md`](../../docs/manual-checks/2026-06-13-program2-post-program-gate.md) — Check 0c-vi uses unified panel; confirm checkbox needs 1215 fix.

**Git:** Ahead of `origin/main`. No push until Paul asks. See `WORKFLOW.md` §4.

---

## Cursor: when you finish a slice

1. `./bin/ci-local` green
2. `done/<slice>/` with `prompt.md` + `output.md`
3. Remove prompt from **`in-progress/`** and **`next/`**
4. **Do not commit or push**
5. Tell Paul: **"slice ready for review"**

Full checklist: `prompts/cursor/WORKFLOW.md` §3.