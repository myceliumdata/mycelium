# Review: Specialist normalized read responses

**Verdict:** **Approved**  
**Reviewer:** Grok  
**Date:** 2026-06-16

---

## Standing principle (Grok — carry forward)

**Component isolation matters, especially while the system is still growing.** When reviewing design or slices (including baseball), surface any decision that:

- Reaches into another component’s internal representation (storage layout, versioned blobs, registry internals)
- Duplicates knowledge that should live in one owner
- Couples the framework to a domain-specific shape that blocks heterogeneous specialists

The two June 2026 specialist slices establish the pattern: **dispatch + published snapshot contract** at the boundary; implementation stays inside `src/agents/specialists/`.

---

## Scope checked

Read full working-tree diff for this slice (includes stacked changes from `2026-06-16-1200-specialist-storage-boundaries` still uncommitted). Verified new `snapshots.py`, handler read paths, framework consumers, boundary test extension, deleted `specialist_fields.py` shim, specialist `_research_context` + template updates.

---

## CI and regression matrix

| Suite | Result |
|-------|--------|
| `./bin/ci-local` | **405 passed**, 85 deselected |
| `pytest -m full -q` | **18 passed**, 472 deselected |
| Provenance + research + sync research + Program 2 matrix + capstones + boundaries + entity_growth (105 tests) | **105 passed** |

---

## Success criteria (from prompt)

- [x] `./bin/ci-local` green
- [x] No `specialists.fields` / `specialist_fields` import in `src/` outside `src/agents/specialists/` (AST guard extended)
- [x] No `is_versioned_field` / `current_version` / `validate_versioned_field` in `query_provenance.py`, `entity_growth.py`, `tools/research.py`
- [x] `read_fields` returns `FieldSnapshot`; `include_versions=True` → `provenance` sub-object
- [x] Research operator deference + peer context tests pass
- [x] CRM provenance + entity growth attribution behavior preserved

---

## What works now

### Normalized contract (`snapshots.py`)

- `field_snapshot` / `field_context_snapshot` / `normalize_context_fields` / `entity_field_status_row`
- Internal versioned storage parsed **only** inside specialists package

### Framework consumers — clean

| Module | Uses snapshot keys only |
|--------|-------------------------|
| `query_provenance.py` | `entry["provenance"]` |
| `entity_growth.py` | `entry["updated_at"]` |
| `tools/research.py` | `value`, `status`, `sources`, `operator.set` — no `specialists.fields` |
| `introspection.py` | Bind versions via dispatch + `provenance.versions` |

### Specialists

- `_research_context` calls `normalize_context_fields` for own storage
- Peer slices from `read_category_slice` already normalized
- `specialist_fields.py` shim **deleted**; tests import `agents.specialists.fields` directly

### Boundary test

`test_specialist_storage_boundaries.py` now guards both `SpecialistStorage` and `agents.specialists.fields` / `agents.specialist_fields` imports outside the specialists package.

---

## Architectural assessment

**This completes the isolation story started in the storage-boundaries slice.**

| Layer | Owner | Framework knows |
|-------|--------|-----------------|
| Storage files & versioned layout | Specialists | Nothing |
| Read/write dispatch | `protocol.py` | Function names only |
| Cross-component API | `FieldSnapshot` / `FieldContextSnapshot` | Published keys only |

A warehouse-backed baseball specialist can keep Lahman rows internally and map to the same snapshots at the boundary — framework and research tooling stay unchanged.

**Remaining coupling (acceptable, explicit):**

1. **`entities.json`** — still framework-maintained registry/index cache (future identity specialist).
2. **Snapshot contract** — framework knows `updated_at`, `provenance`, `operator` keys. That is the **intentional public API**, not storage layout. Document changes to snapshots as protocol versioning when baseball diverges.
3. **`strip_bind_fields`** in `context.py` — legacy helper; production path uses normalized slices. `examples/networks/crm/specialists/contact_specialist.py` still uses old pattern (non-canonical copy) — nit only.

---

## Stacked commit note

Working tree includes **both** specialist slices (1200 storage boundaries + 1400 normalized reads). Recommend **one refactor commit** or two sequential commits on `main` before baseball work:

```
refactor(specialists): storage boundaries and normalized read snapshots
```

(or two messages as in each slice’s `output.md`).

---

## Polish nits (non-blocking)

| # | Item |
|---|------|
| N1 | Remove or update stale `examples/networks/crm/specialists/contact_specialist.py` (`strip_bind_fields` leak) |
| N2 | `strip_bind_fields` — deprecate if only used by legacy example + one unit test |
| N3 | Consider documenting `FieldSnapshot` / `FieldContextSnapshot` in `docs/architecture.md` as protocol v1 (one short schema block) |

---

## Recommendation

**Approve.** Slice delivers what Paul asked for: framework no longer parses internal specialist storage schema. Combined with storage boundaries, this is a solid vantage point for baseball design.

Paul: say the word to commit (one or two commits). Grok will not push.