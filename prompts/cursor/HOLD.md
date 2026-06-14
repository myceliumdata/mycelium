# Cursor queue

**Active:** [`next/2026-06-14-1410-multi-match-step2-deliver-truncation.md`](next/2026-06-14-1410-multi-match-step2-deliver-truncation.md) — **after** Paul manual validation test on `1400`

**Last approved:** [`done/2026-06-14-1400-provisional-validation-step2-deliver/`](done/2026-06-14-1400-provisional-validation-step2-deliver/) — **Approved + polish nits** (pending Paul manual test)

**Process:** Paul + Grok manual test `1400` before starting `1410`.

**Git:** Ahead of `origin/main`. No push until Paul asks. See `WORKFLOW.md` §4.

---

## Cursor: when you finish a slice

1. `./bin/ci-local` green
2. `done/<slice>/` with `prompt.md` + `output.md`
3. Remove prompt from **`in-progress/`** and **`next/`**
4. **Do not commit or push**
5. Tell Paul **slice ready for review**