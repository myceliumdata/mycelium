# Cursor queue

**Active:** [`next/2026-06-14-1430-partial-lookup-fuzzy-name-suggestions.md`](next/2026-06-14-1430-partial-lookup-fuzzy-name-suggestions.md) — partial name typo → `lookup_suggested` (Claude `Andrea Kalman` repro)

**Last approved:** [`1420`](done/2026-06-14-1420-multi-match-post-validate-specialist-schedule/) — manual test passed

**Process:** Cursor `1430` → Grok review → Paul manual (`Andrea Kalman` → suggestions). Program 2 gate after.

**Git:** Ahead of `origin/main`. No push until Paul asks. See `WORKFLOW.md` §4.

---

## Cursor: when you finish a slice

1. `./bin/ci-local` green
2. `done/<slice>/` with `prompt.md` + `output.md`
3. Remove prompt from **`in-progress/`** and **`next/`**
4. **Do not commit or push**
5. Tell Paul **slice ready for review**