# Task: Program 2 — MVR / entity storage Slice 2 (read surfaces)

> **READY** — Move to `in-progress/` before starting.

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/attribute-provenance-program2.md`](../../docs/plans/attribute-provenance-program2.md) — program context + locked decisions
- [`docs/plans/attribute-provenance-program2-slice2.md`](../../docs/plans/attribute-provenance-program2-slice2.md) — **locked spec**
- [`docs/plans/attribute-provenance-and-storage.md`](../../docs/plans/attribute-provenance-and-storage.md) — three-layer model
- [`docs/architecture.md`](../../docs/architecture.md) — storage + MVR sections

**Prerequisite:** Slice 1 approved — see [`done/2026-06-13-2200-attribute-provenance-program2-slice1/review.md`](../done/2026-06-13-2200-attribute-provenance-program2-slice1/review.md) (Approved + polish nits).

**Lane:** Cursor implements code + tests only. Do **not** edit `TODO.md`. Do **not** change unified write API or research prompts (Slice 3).

---

## Objective

Expose MVR/bind field version history on **read paths**: `provenance=true` query responses and admin entity drill-down. Default flat `results[]` unchanged.

**Locked:** Version history lives in **specialist `versions[]` only** — no `bind_versions[]` on entity rows. Ownership resolved via `categories.json` `attribute_map`.

---

## Implement

Follow [`attribute-provenance-program2-slice2.md`](../../docs/plans/attribute-provenance-program2-slice2.md) exactly:

1. `src/agents/query_provenance.py` — include bind/MVR fields with versioned specialist storage
2. `src/network/introspection.py` — bind field drill-down includes `versions[]`
3. Admin UI (`admin-ui/`) — bind field rows show expandable version timeline (reuse extended-field UI)
4. MCP schema — update `mycelium://schema/query-response` if provenance block documents bind attrs
5. Tests — `test_query_provenance.py`, `test_admin_daemon.py`; admin-ui build passes
6. Docs — optional provenance example + read surfaces table update

---

## Constraints

- **Read only** — no operator write endpoints (Program 3)
- **Backward compat** — omit bind fields with no versioned specialist entry yet
- **Do not touch:** `attribute_write.py` unified write semantics (Slice 1), research operator deference templates (Slice 3)
- Hot-path display value still from entity cache; versions from specialist file
- Keep **`./bin/ci-local` green**

---

## Deliverables

Move this file to `prompts/cursor/done/2026-06-13-2300-attribute-provenance-program2-slice2/` with:
- `prompt.md` (copy of this file)
- `output.md` — summary + **For Grok + Paul** section
- Run `./bin/ci-local` and record result in `output.md`

---

## Review gate

Grok reviews before Slice 3 is queued.