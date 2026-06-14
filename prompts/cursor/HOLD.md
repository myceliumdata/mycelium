# Cursor queue

**Active:** [`next/2026-06-14-1435-partial-lookup-fuzzy-employer-suggestions.md`](next/2026-06-14-1435-partial-lookup-fuzzy-employer-suggestions.md) — after `1430` review

**Pending review:** [`done/2026-06-14-1430-partial-lookup-fuzzy-name-suggestions/`](done/2026-06-14-1430-partial-lookup-fuzzy-name-suggestions/) — Cursor delivered (name partial fuzzy)

**Design:** [`docs/plans/fuzzy-lookup-policy.md`](../../docs/plans/fuzzy-lookup-policy.md) — fuzzy on all bind fields; fuzzy on any-field search when TODO ships

**Last approved:** [`1420`](done/2026-06-14-1420-multi-match-post-validate-specialist-schedule/) — manual test passed

**Process:** Grok review `1430` → Cursor `1435` → Program 2 gate when ready.

**Git:** Ahead of `origin/main`. No push until Paul asks. See `WORKFLOW.md` §4.

---

## Cursor: when you finish a slice

1. `./bin/ci-local` green
2. `done/<slice>/` with `prompt.md` + `output.md`
3. Remove prompt from **`in-progress/`** and **`next/`**
4. **Do not commit or push**
5. Tell Paul **slice ready for review**