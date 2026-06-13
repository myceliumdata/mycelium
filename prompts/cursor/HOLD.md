# Cursor queue

**Active:** [`next/2026-06-13-2400-attribute-provenance-program2-slice3.md`](next/2026-06-13-2400-attribute-provenance-program2-slice3.md) — Program 2 Slice 3 (polish)

**Program:** [`docs/plans/attribute-provenance-program2.md`](../../docs/plans/attribute-provenance-program2.md)

**Done:** [`done/2026-06-13-2300-attribute-provenance-program2-slice2/`](done/2026-06-13-2300-attribute-provenance-program2-slice2/) — **Approved** (uncommitted; commit when Paul ready)

**Prior:** [`done/2026-06-13-2200-attribute-provenance-program2-slice1/`](done/2026-06-13-2200-attribute-provenance-program2-slice1/) — **Approved + polish nits**

**Next:** Program 3 kickoff (after Slice 3 approved).

**Git:** Local commit ahead of `origin/main`. No push until Paul asks. See `WORKFLOW.md` §4.

---

## Cursor: when you finish a slice

1. `./bin/ci-local` green
2. `done/<slice>/` with `prompt.md` + `output.md`
3. Remove prompt from **`in-progress/`** and **`next/`**
4. **Do not commit or push**
5. Tell Paul: **"slice ready for review"**

Full checklist: `prompts/cursor/WORKFLOW.md` §3.