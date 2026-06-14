# Cursor queue

**Active:** [`next/2026-06-14-1435-partial-lookup-fuzzy-employer-suggestions.md`](next/2026-06-14-1435-partial-lookup-fuzzy-employer-suggestions.md)

**Last approved:** [`done/2026-06-14-1430-partial-lookup-fuzzy-name-suggestions/`](done/2026-06-14-1430-partial-lookup-fuzzy-name-suggestions/) — **Approved + polish nits**

**Design:** [`docs/plans/fuzzy-lookup-policy.md`](../../docs/plans/fuzzy-lookup-policy.md)

**Process:** Cursor `1435` → Grok review → Program 2 gate when ready.

**Git:** Ahead of `origin/main`. No push until Paul asks. See `WORKFLOW.md` §4.

---

## Cursor: when you finish a slice

1. `./bin/ci-local` green
2. `done/<slice>/` with `prompt.md` + `output.md`
3. Remove prompt from **`in-progress/`** and **`next/`**
4. **Do not commit or push**
5. Tell Paul **slice ready for review**