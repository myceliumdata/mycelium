# Cursor queue

**Active:** [`next/2026-06-14-1400-provisional-validation-step2-deliver.md`](next/2026-06-14-1400-provisional-validation-step2-deliver.md) — **fix first** (Q5a validation on step 2)

**Next:** [`next/2026-06-14-1410-multi-match-step2-deliver-truncation.md`](next/2026-06-14-1410-multi-match-step2-deliver-truncation.md) — after `1400` approved + Paul manual validation test

**Process:** Paul + Grok manual test after **each** slice before advancing queue.

**Last approved:** [`done/2026-06-14-1305-admin-inspect-polish-nits/`](done/2026-06-14-1305-admin-inspect-polish-nits/)

**Manual gate:** [`docs/manual-checks/2026-06-13-program2-post-program-gate.md`](../../docs/manual-checks/2026-06-13-program2-post-program-gate.md) — defer full gate until after `1400` + `1410`

**Git:** Ahead of `origin/main`. No push until Paul asks. See `WORKFLOW.md` §4.

---

## Cursor: when you finish a slice

1. `./bin/ci-local` green
2. `done/<slice>/` with `prompt.md` + `output.md`
3. Remove prompt from **`in-progress/`** and **`next/`**
4. **Do not commit or push**
5. Tell Paul **slice ready for review**