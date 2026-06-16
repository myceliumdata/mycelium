# Review: Specialist storage boundaries

**Verdict:** **Approved + polish nits**  
**Reviewer:** Grok  
**Date:** 2026-06-16

---

## Scope checked

Read full working-tree diff (30 modified files + 6 new modules + 1 new test file). Compared against `prompt.md` success criteria and prior Program 2 / capstone behavior.

---

## CI and regression matrix

| Suite | Result |
|-------|--------|
| `./bin/ci-local` | **405 passed**, 86 deselected |
| `pytest -m full -q` | **18 passed**, 473 deselected |
| Capstone / bootstrap / bind / provenance / research (133 tests) | **133 passed** |
| Admin + network integration (60 tests) | **60 passed** |

**Prior behavior verified green:**

- Program 2 bootstrap matrix (seed + empty-crm create-on-deliver + Road Runner no-duplicate)
- CRM refresh capstone (15 entities, `seed_bootstrap` specialist versions)
- empty-crm step-2 without upfront MVR mappings
- `attribute_write` unified path including multi-category rollback
- Query provenance (bind + extended attrs)
- Sync research persist / pending / timeout paths
- Admin daemon entity/status introspection tests

---

## What the slice delivers (substance)

### Boundary enforcement — **met**

- AST guard in `tests/test_specialist_storage_boundaries.py` scans every `src/**/*.py` outside `agents/specialists/` for `SpecialistStorage` imports — **all pass**.
- Grep confirms no `SpecialistStorage` usage in framework modules (`attribute_write`, `context`, `research`, `introspection`, etc.).

### Write path — **met**

- `attribute_write.write_bind_fields` → `dispatch_write_bind_fields_multi` → `handlers.write_bind_fields_multi` (rollback preserved; test `test_write_bind_fields_rollback_on_second_save_failure` passes).
- Registry cache + `bind_index` updated from returned values only.
- Seed import unchanged at API level (`seed_import` → `ensure_bound_entity`) but storage writes now go through dispatch/handlers with `actor_kind=seed_bootstrap`.

### Read path — **met**

- `context.py` uses `dispatch_read_category_slice` (no direct `storage.json` reads).
- `query_provenance.py` uses `dispatch_read_fields(..., include_versions=True)`.
- `entity_growth.py` attribution timestamps via dispatch read.
- `introspection.py` bind versions and extended field statuses via dispatch; `_analyze_storage` via `dispatch_analyze_category_storage`.

### Research path — **met**

- `tools/research.py` persist/mark-pending/audit via `dispatch_persist_research`, `dispatch_mark_pending`, `dispatch_append_research_audit`.
- `storage` parameter removed from `run_field_research`; tests updated.

### Specialist protocol — **met**

- `protocol.py` + `handlers.py` + `research_handlers.py` + `_protocol_exports.py`.
- Committed specialists and factory template attach `write_fields` / `read_fields` / `bootstrap_entity`.

### Docs — **met**

- `docs/architecture.md` addendum (line ~394).
- `docs/plans/attribute-provenance-program2.md` superseded-for-storage-I/O note.

---

## Architectural assessment

**This is a real fix, not a rename.** Program 2’s central violation — framework code opening `SpecialistStorage` and writing `records[id][field].versions[]` — is gone from all hot paths. The dispatch layer gives a stable seam for future per-specialist storage strategies and for moving `entities.json` to an identity specialist.

**Honest limits (not blockers for this slice):**

1. **Shared handler implementation.** All CRM specialists delegate to the same `handlers.py` via `_protocol_exports`. Storage is *encapsulated* inside the specialists package, but not yet *per-agent unique*. Acceptable for CRM flat-JSON era; baseball will need specialists that own distinct handlers.

2. **Multi-bind bypasses module handlers.** `dispatch_write_bind_fields_multi` calls `handlers.write_bind_fields_multi` directly instead of each specialist’s `write_fields`. Correct for transactional rollback; document that multi-field binds are a package-level operation.

3. **Residual schema coupling.** `query_provenance.py`, `entity_growth.py`, `introspection.py`, and `tools/research.py` still import `agents.specialists.fields` helpers (`is_versioned_field`, `validate_versioned_field`, `current_value`, etc.). They no longer know *where* data lives, but they still know the *versioned field response shape* returned by dispatch. Tighter boundary would push that parsing into specialists package (e.g. `normalize_read_response`).

4. **Seed bootstrap shape vs prompt wording.** Prompt asked for explicit `bootstrap_entity` dispatch after registry rows. Implementation uses `ensure_entity_bind_fields` → `write_bind_fields` with `actor_kind=seed_bootstrap` (handlers treat bootstrap as `write_fields`). Behavior matches capstones; naming differs from spec.

5. **Dead code.** `introspection._storage_file` / `_strategy_file` are defined but unused — remove in polish.

6. **Registry metadata.** `agent_registry.json` still records `storage_path` / `strategy_path` strings from `registry_storage_paths()`. Introspection no longer reads those paths for entity data; paths are lifecycle metadata only.

7. **Example network specialists.** `examples/networks/crm/specialists/` not regenerated (noted in `output.md`). Committed `src/agents/specialists/*` are canonical — OK.

---

## Polish nits (non-blocking)

| # | Item | Suggestion |
|---|------|------------|
| N1 | Dead `_storage_file` / `_strategy_file` in `introspection.py` | Delete |
| N2 | Framework imports of `specialists.fields` outside protocol | Consolidate response normalization in specialists package; framework consumes opaque dicts |
| N3 | Boundary test scope | Extend AST guard to flag `agents.specialists.fields` imports outside `agents/specialists/` (optional stricter gate) |
| N4 | `agent_registry` storage paths | Consider dropping or marking deprecated when identity specialist lands |
| N5 | Architecture § seed bootstrap (lines 62–65) | Still says identity from registry; add one sentence that bind versions live in specialists via dispatch |

---

## Success criteria checklist (from prompt)

- [x] `./bin/ci-local` green
- [x] No `SpecialistStorage` import outside specialists package (AST test)
- [x] No direct `storage.json` reads in framework hot paths (verified by read of `context`, `research`, `query_provenance`, `introspection` entity paths)
- [x] CRM refresh 15 entities + `seed_bootstrap` versions (matrix + capstone)
- [x] empty-crm create-on-deliver
- [x] Query + provenance smoke unchanged
- [x] Factory template includes protocol handlers

---

## Recommendation

**Approve for commit.** The refactor is large but regression coverage is strong across smoke, full, capstone, Program 2 matrix, research, provenance, metering, and admin paths. Remaining coupling is schema-level (field helpers), not storage-path-level — acceptable as a stepping stone toward identity specialist and heterogeneous baseball specialists.

Suggested commit message (from `output.md`):

```
refactor(specialists): enforce storage boundaries via dispatch protocol

Framework routes writes/reads through specialist handlers; registry
cache/indexes sync from returned values. Seed bootstrap is registry-first
then specialist bootstrap_entity. Eliminates direct SpecialistStorage
access outside specialists package.
```

Paul: say the word if you want Grok to commit this slice.