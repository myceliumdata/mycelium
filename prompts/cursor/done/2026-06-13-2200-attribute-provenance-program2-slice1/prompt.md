# Task: Program 2 — MVR / entity storage Slice 1 (unified write)

> **READY** — Move to `in-progress/` before starting.

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/attribute-provenance-program2.md`](../../docs/plans/attribute-provenance-program2.md) — program context + locked decisions
- [`docs/plans/attribute-provenance-program2-slice1.md`](../../docs/plans/attribute-provenance-program2-slice1.md) — **locked spec**
- [`docs/plans/attribute-provenance-and-storage.md`](../../docs/plans/attribute-provenance-and-storage.md) — three-layer model
- [`docs/architecture.md`](../../docs/architecture.md) — storage + MVR sections

**Lane:** Cursor implements code + tests only. Do **not** edit `TODO.md`. Do **not** change query provenance, admin version UI, or research prompts (Slices 2–3).

---

## Objective

Unified write API for MVR bind fields: canonical `versions[]` in **taxonomy-owned** specialist storage; entity row = cache + protocol + indexes. Route seed bind, registry bind, and step-2 create-on-deliver through one path.

**Locked:** No `bind_versions[]` on entity rows. No hardcoded CRM category map in Python — use `categories.json` `attribute_map`.

---

## Implement

Follow [`attribute-provenance-program2-slice1.md`](../../docs/plans/attribute-provenance-program2-slice1.md) exactly:

1. Taxonomy bootstrap — `name` / `employer` in sample categories + `attribute_map`
2. `src/agents/attribute_write.py` — unified write + owner resolution
3. Refactor `entity_registry` bind paths to use unified write
4. Wire `seed_import` + `target_deliver.bind_provisional_from_scope`
5. `specialists/base.py` storage strategy notes
6. `tests/test_attribute_write.py` + update fixtures as needed
7. Minimal `architecture.md` + architecture storage doc note

---

## Constraints

- **Hard cutover** — no lazy migration of registry-only MVR into specialist storage on read
- **Index replace** — correcting a bind field removes old index keys (no aliases)
- **Do not touch:** `query_provenance.py` bind exclusion (Slice 2), admin UI version rows (Slice 2), research operator deference templates (Slice 3), operator HTTP endpoints (Program 3)
- Keep **`./bin/ci-local` green**

---

## Deliverables

Move this file to `prompts/cursor/done/2026-06-13-2200-attribute-provenance-program2-slice1/` with:
- `prompt.md` (copy of this file)
- `output.md` — summary + **For Grok + Paul** section
- Run `./bin/ci-local` and record result in `output.md`

---

## Review gate

Grok reviews before Slice 2 is queued.