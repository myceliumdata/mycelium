# Cursor queue

**Active:** None — **Program 2 + polish complete** (committed locally)

**Program:** [`docs/plans/attribute-provenance-program2.md`](../../docs/plans/attribute-provenance-program2.md) — **Complete**

**Done:** [`done/2026-06-13-2500-attribute-provenance-program2-polish/`](done/2026-06-13-2500-attribute-provenance-program2-polish/) — **Approved**

**Prior:** Slices 1–3 — Approved

**Next:** Delivery push when Paul asks; Program 3 kickoff when ready.

**Git:** 5 commits ahead of `origin/main` (Program 2 + polish). No push until Paul asks. See `WORKFLOW.md` §4.

---

## Cursor: when you finish a slice

1. `./bin/ci-local` green
2. `done/<slice>/` with `prompt.md` + `output.md`
3. Remove prompt from **`in-progress/`** and **`next/`**
4. **Do not commit or push**
5. Tell Paul: **"slice ready for review"**

Full checklist: `prompts/cursor/WORKFLOW.md` §3.