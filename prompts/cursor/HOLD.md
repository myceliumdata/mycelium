# Cursor queue

**Active:** **Program 2 — MVR / entity storage** Slice 1 (unified write)

**Program:** [`docs/plans/attribute-provenance-program2.md`](../../docs/plans/attribute-provenance-program2.md)

**Prompt:** [`next/2026-06-13-2200-attribute-provenance-program2-slice1.md`](next/2026-06-13-2200-attribute-provenance-program2-slice1.md) — move to `in-progress/` when Cursor starts.

MVR redesign (M1–M10) complete. Requirements locked June 2026.

**Git:** `origin/main` current. See `WORKFLOW.md` §4.

---

## Cursor: when you finish a slice

1. `./bin/ci-local` green
2. `done/<slice>/` with `prompt.md` + `output.md`
3. Remove prompt from **`in-progress/`** and **`next/`**
4. **Do not commit or push**
5. Tell Paul: **"slice ready for review"**

Full checklist: `prompts/cursor/WORKFLOW.md` §3.