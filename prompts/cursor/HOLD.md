# Cursor queue

**Active:** None — **Program 2 Slice 1** committed locally (awaiting push; Slice 2 not queued)

**Program:** [`docs/plans/attribute-provenance-program2.md`](../../docs/plans/attribute-provenance-program2.md)

**Done:** [`done/2026-06-13-2200-attribute-provenance-program2-slice1/`](done/2026-06-13-2200-attribute-provenance-program2-slice1/) — **Approved + polish nits**

**Next:** Queue Slice 2 (provenance + admin bind fields) when Paul asks.

**Git:** Local commit ahead of `origin/main`. No push until Paul asks. See `WORKFLOW.md` §4.

---

## Cursor: when you finish a slice

1. `./bin/ci-local` green
2. `done/<slice>/` with `prompt.md` + `output.md`
3. Remove prompt from **`in-progress/`** and **`next/`**
4. **Do not commit or push**
5. Tell Paul: **"slice ready for review"**

Full checklist: `prompts/cursor/WORKFLOW.md` §3.