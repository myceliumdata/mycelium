# Cursor queue

**Active:** [`next/2026-06-14-1420-multi-match-post-validate-specialist-schedule.md`](next/2026-06-14-1420-multi-match-post-validate-specialist-schedule.md) — multi-match same-turn email after batch promote (1400 nit N1)

**Last approved:** [`1410`](done/2026-06-14-1410-multi-match-step2-deliver-truncation/) — **Approved + polish nits** (Paul manual test passed)

**Prior:** [`1400`](done/2026-06-14-1400-provisional-validation-step2-deliver/) — manual validation test **passed** (Paul).

**Process:** Cursor `1420` → Grok review → Paul manual (Wrong Corp provisional → one step-2 with emails). Then Program 2 gate when ready.

**Git:** Ahead of `origin/main`. No push until Paul asks. See `WORKFLOW.md` §4.

---

## Cursor: when you finish a slice

1. `./bin/ci-local` green
2. `done/<slice>/` with `prompt.md` + `output.md`
3. Remove prompt from **`in-progress/`** and **`next/`**
4. **Do not commit or push**
5. Tell Paul **slice ready for review**