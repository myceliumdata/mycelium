# Cursor queue

**Active:** MVR redesign slice **M7** in `prompts/cursor/next/2026-06-13-1600-mvr-redesign-slice-m7.md` (after M6 approved + committed locally)

**Program:** [`docs/plans/mvr-redesign-program.md`](../../docs/plans/mvr-redesign-program.md) (slices M1–M10)

Program 2 (versioned bind storage) waits until MVR redesign ships.

**Git:** Grok commits approved slices locally on `mycelium`; push `origin` only when Paul explicitly asks (after program complete). See `WORKFLOW.md` §4.

---

## Cursor: when you finish a slice

1. `./bin/ci-local` green
2. `done/<slice>/` with `prompt.md` + `output.md` — code on disk matches `output.md`
3. Remove your prompt from **`in-progress/`** and **`next/`** (no stale duplicate)
4. **Do not commit or push**
5. Tell Paul: **"slice ready for review"**

Full checklist: `prompts/cursor/WORKFLOW.md` §3.