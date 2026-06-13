# Cursor queue

**Active:** None — **Program 2 complete** (Slices 1–3 committed locally)

**Program:** [`docs/plans/attribute-provenance-program2.md`](../../docs/plans/attribute-provenance-program2.md) — **Complete**

**Done:** [`done/2026-06-13-2400-attribute-provenance-program2-slice3/`](done/2026-06-13-2400-attribute-provenance-program2-slice3/) — **Approved + polish nits**

**Prior:** Slices 1–2 — Approved

**Next:** Program 3 kickoff when Paul + Grok lock spec and queue prompt.

**Git:** 3 commits ahead of `origin/main` (Program 2). No push until Paul asks. See `WORKFLOW.md` §4.

---

## Cursor: when you finish a slice

1. `./bin/ci-local` green
2. `done/<slice>/` with `prompt.md` + `output.md`
3. Remove prompt from **`in-progress/`** and **`next/`**
4. **Do not commit or push**
5. Tell Paul: **"slice ready for review"**

Full checklist: `prompts/cursor/WORKFLOW.md` §3.