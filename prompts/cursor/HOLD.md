# Cursor queue

**Active:** *(empty — queue after 1410)*

**Last approved:** [`done/2026-06-14-1410-multi-match-step2-deliver-truncation/`](done/2026-06-14-1410-multi-match-step2-deliver-truncation/) — **Approved + polish nits** (pending Paul manual test)

**Prior:** [`1400`](done/2026-06-14-1400-provisional-validation-step2-deliver/) — manual validation test **passed** (Paul).

**Process:** Paul manual test `1410` (truncation / `len(results)`), then Program 2 gate when ready.

**Git:** Ahead of `origin/main`. No push until Paul asks. See `WORKFLOW.md` §4.

---

## Cursor: when you finish a slice

1. `./bin/ci-local` green
2. `done/<slice>/` with `prompt.md` + `output.md`
3. Remove prompt from **`in-progress/`** and **`next/`**
4. **Do not commit or push**
5. Tell Paul **slice ready for review**