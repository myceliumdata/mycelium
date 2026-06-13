# Task: Program 2 — Polish (review nits P1–P7)

> **READY** — Move to `in-progress/` before starting.

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/attribute-provenance-program2-polish.md`](../../docs/plans/attribute-provenance-program2-polish.md) — **nit backlog**
- [`docs/plans/attribute-provenance-program2.md`](../../docs/plans/attribute-provenance-program2.md) — locked decisions
- Review nits source:
  - [`done/2026-06-13-2200-attribute-provenance-program2-slice1/review.md`](../done/2026-06-13-2200-attribute-provenance-program2-slice1/review.md)
  - [`done/2026-06-13-2300-attribute-provenance-program2-slice2/review.md`](../done/2026-06-13-2300-attribute-provenance-program2-slice2/review.md)
  - [`done/2026-06-13-2400-attribute-provenance-program2-slice3/review.md`](../done/2026-06-13-2400-attribute-provenance-program2-slice3/review.md)

**Prerequisite:** Program 2 Slices 1–3 approved and committed locally.

**Lane:** Cursor implements code + tests only. Do **not** edit `TODO.md`. No Program 3 operator UI.

---

## Objective

Close non-blocking review nits from Program 2 Slices 1–3 in one polish pass. See backlog table in [`attribute-provenance-program2-polish.md`](../../docs/plans/attribute-provenance-program2-polish.md).

---

## Implement

### P1 — Research prompt block ordering

**File:** `src/tools/research.py` — `build_research_prompts`

When disambiguation, operator deference, and peer context are all present, user prompt order must be:

1. Disambiguation (if any)
2. **Operator deference** (if any)
3. Peer context (if any)
4. Category guidance fragment (if any)
5. Research instruction + JSON payload

Fix the `insert_at` logic so peer block does not land before operator block. Add smoke test with all three context blocks present; assert `OPERATOR OVERRIDE` appears before peer specialist header in `user`.

### P2 — Shared specialist field version loader

**Duplication:** `src/network/introspection.py` `_bind_field_versions` vs `src/agents/query_provenance.py` `_storage_record` + field read.

Extract a shared helper (prefer `src/agents/specialist_fields.py` or a small `specialist_read` module if cleaner) e.g. `field_versions_from_storage(paths, category, entity_id, field_name) -> tuple[dict, ...]`.

Refactor introspection and query provenance to use it. Behavior unchanged; no new read tolerance for flat v1.

### P3 — Skip no-op bind version append

**File:** `src/agents/attribute_write.py` — `write_bind_fields` / `_write_specialist_version`

When current versioned value for a bind field already equals the incoming value (same string after strip), do **not** append a duplicate version. Still update `attr_sources`, cache, indexes, and registry row as needed.

Add smoke test: write same name twice → still one version in specialist storage.

### P4 — Multi-specialist write atomicity (best-effort)

**File:** `src/agents/attribute_write.py` — `write_bind_fields`

When multiple bind fields route to different specialist categories, a crash between saves can leave split state. Implement best-effort atomicity:

- Before saving, snapshot each affected specialist `storage.json` payload (in memory).
- Apply all in-memory mutations, then save each specialist.
- If a later save fails, restore earlier snapshots and re-save (best-effort rollback), then re-raise.

Add smoke test with monkeypatched second `SpecialistStorage.save` failure → first specialist storage restored to pre-write state.

If rollback is too invasive for this slice, document limitation in `attribute_write.py` module docstring and mark P4 as deferred in `output.md` — prefer implementing rollback.

### P5 — Admin bind status for empty employer

**File:** `src/network/introspection.py` — `_bind_field_statuses`

Remove the `employer` empty skip (`if field_name == "employer" and not value: continue`). Emit a row for every `mvr.bind_fields` entry; `value` may be `None`.

Update/add smoke test in `tests/test_network_status.py` or `tests/test_admin_daemon.py` asserting employer row exists when empty.

### P6 — Bootstrap CRM map documentation

**Files:** `src/network/category_mvr_bootstrap.py`, [`attribute-provenance-program2.md`](../../docs/plans/attribute-provenance-program2.md)

Add module docstring: `CRM_MVR_FIELD_CATEGORY` is **bootstrap/merge reference only** for example networks; runtime ownership is always `categories.json` `attribute_map`. Short footnote in program spec § Taxonomy bootstrap.

### P7 — Duplicate bind hard-cutover note

**Files:** `docs/onboarding.md` or `examples/networks/crm/README.md`

One paragraph: duplicate bind key hits return existing registry row without backfilling pre–Program 2 specialist versions; refresh network or wipe specialist storage to migrate (hard cutover per P2-7).

---

## Constraints

- **Do not touch:** Program 3 operator endpoints, entity row schema for new bind columns, `bind_versions[]`.
- **Do not** change unified write semantics beyond P3/P4.
- Keep **`./bin/ci-local` green**.

---

## Deliverables

Move this file to `prompts/cursor/done/2026-06-13-2500-attribute-provenance-program2-polish/` with:
- `prompt.md` (copy of this file)
- `output.md` — summary, P1–P7 checklist, **For Grok + Paul**
- Run `./bin/ci-local` and record result in `output.md`
- Mark items done in [`attribute-provenance-program2-polish.md`](../../docs/plans/attribute-provenance-program2-polish.md) exit criteria (checkboxes only in that plan file — not `TODO.md`)

---

## Review gate

Grok reviews before delivery push or Program 3 kickoff.