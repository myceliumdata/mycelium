# Cursor queue

**Active:** None — **MVR redesign program complete** (M1–M10 reviewed and committed locally)

**Program:** [`docs/plans/mvr-redesign-program.md`](../../docs/plans/mvr-redesign-program.md)

Program 2 (versioned bind storage) may start after Paul pushes and signs off.

**Git:** 13 local commits ahead of `origin/main` (M4–M10 + polish backlog). Push when Paul explicitly asks. See `WORKFLOW.md` §4.

---

## Cursor: when you finish a slice

1. `./bin/ci-local` green
2. `done/<slice>/` with `prompt.md` + `output.md`
3. Remove prompt from **`in-progress/`** and **`next/`**
4. **Do not commit or push**
5. Tell Paul: **"slice ready for review"**

Full checklist: `prompts/cursor/WORKFLOW.md` §3.