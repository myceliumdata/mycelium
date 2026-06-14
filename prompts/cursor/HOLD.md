# Cursor queue

**Active:** [`next/2026-06-14-0900-query-response-omit-na-fields.md`](next/2026-06-14-0900-query-response-omit-na-fields.md) — omit N/A `QueryResponse` public JSON fields by outcome

**Done (approved):** [`done/2026-06-14-0800-example-network-capstone-tests-gate-pairing/`](done/2026-06-14-0800-example-network-capstone-tests-gate-pairing/) — **Approved**

**Prior:** [`done/2026-06-14-0715-empty-crm-mvr-bootstrap-create-on-deliver/`](done/2026-06-14-0715-empty-crm-mvr-bootstrap-create-on-deliver/) — **Approved**

**Program:** [`docs/plans/attribute-provenance-program2.md`](../../docs/plans/attribute-provenance-program2.md) — **Complete**

**Done:** [`done/2026-06-13-2500-attribute-provenance-program2-polish/`](done/2026-06-13-2500-attribute-provenance-program2-polish/) — **Approved**

**Prior:** Slices 1–3 — Approved

**Manual gate:** [`docs/manual-checks/2026-06-13-program2-post-program-gate.md`](../../docs/manual-checks/2026-06-13-program2-post-program-gate.md) — pending Paul run; automated pairing in place.

**Next:** Push after gate CLEAR; **Program 3** = entity protocol legacy cleanup ([`entity-protocol-legacy-cleanup-program.md`](../../docs/plans/entity-protocol-legacy-cleanup-program.md)).

**Git:** Ahead of `origin/main` (Program 2 + polish + fixes + capstones). No push until Paul asks. See `WORKFLOW.md` §4.

---

## Cursor: when you finish a slice

1. `./bin/ci-local` green
2. `done/<slice>/` with `prompt.md` + `output.md`
3. Remove prompt from **`in-progress/`** and **`next/`**
4. **Do not commit or push**
5. Tell Paul: **"slice ready for review"**

Full checklist: `prompts/cursor/WORKFLOW.md` §3.