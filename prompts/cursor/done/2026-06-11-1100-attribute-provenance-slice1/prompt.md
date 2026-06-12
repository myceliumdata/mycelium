# Task: Program 1 — Attribute provenance Slice 1 (schema + research write)

> **READY** — Move to `in-progress/` before starting.

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/attribute-provenance-program1.md`](../../docs/plans/attribute-provenance-program1.md) — program context
- [`docs/plans/attribute-provenance-program1-slice1.md`](../../docs/plans/attribute-provenance-program1-slice1.md) — **locked spec**
- [`docs/architecture.md`](../../docs/architecture.md) — storage section

**Lane:** Cursor implements code + tests only. Do **not** edit `TODO.md`. Do **not** regen specialists or change introspection (Slice 2).

---

## Objective

Versioned provenance for extended specialist attributes. Research appends `versions[]`. Flat v1 field shape fails loud. Hard cutover — no lazy migration.

---

## Implement

Follow [`attribute-provenance-program1-slice1.md`](../../docs/plans/attribute-provenance-program1-slice1.md) exactly:

1. `src/agents/specialist_fields.py` — shared helpers
2. `src/tools/research.py` — append versions on research/pending persist
3. `src/agents/entity_growth.py` — `at` from current version
4. `src/agents/specialists/base.py` — `versioned_provenance_v1` strategy template
5. `tests/test_specialist_fields.py` + update all flat storage fixtures in tests
6. Brief `docs/architecture.md` storage note

---

## Constraints

- **Breaking change:** invalid flat v1 entries raise clear `ValueError`
- **No migration** on read — do not convert old shape
- **Do not touch:** `entities.json`, MVR, bind_index, specialist jinja template, introspection, `QueryResponse`, admin-ui
- Keep **full pytest green** — if specialist read path breaks, minimally bridge only in tests or document blockers in `output.md` for Slice 2 (prefer fixing read path only if ≤10 lines in research-adjacent code; otherwise Slice 2 owns template)

---

## Deliverables

Move this file to `prompts/cursor/done/2026-06-11-1100-attribute-provenance-slice1/` with:
- `prompt.md` (copy of this file)
- `output.md` — summary + **For Grok + Paul** section
- Run `./bin/ci-local` (or full pytest) and record result in `output.md`

---

## Review gate

Grok reviews before Slice 2 is queued.
