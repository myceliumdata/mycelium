# Specialist normalized read responses

## Summary

Framework modules no longer import `agents.specialists.fields` or parse versioned storage layout (`versions[]`, `current_version_id`). Specialist dispatch returns framework-ready snapshots; consumers use `value`, `status`, `updated_at`, `provenance`, `sources`, and `operator` only.

## Normalized contract (`src/agents/specialists/snapshots.py`)

| Shape | Used by |
|-------|---------|
| `FieldSnapshot` | `read_fields`, provenance, entity growth attribution |
| `FieldContextSnapshot` | `read_category_slice`, graph context, research prompts |

Handlers normalize at the specialists package boundary; `include_versions=True` on dispatch maps to `include_provenance` and sets the `provenance` sub-object.

## Framework refactors

| Module | Change |
|--------|--------|
| `query_provenance.py` | Reads `entry["provenance"]` from snapshots |
| `entity_growth.py` | Uses `entry["updated_at"]`; category-tree agent resolution |
| `introspection.py` | Bind versions from `provenance.versions` |
| `tools/research.py` | Peer/operator blocks from snapshot fields only |
| `context.py` | Unchanged dispatch; slices are already normalized |

## Specialists + template

`_research_context` uses `normalize_context_fields` for own storage; peer slices pass through as normalized maps from `read_category_slice`.

## Cleanup

- Deleted `src/agents/specialist_fields.py` shim; tests import `agents.specialists.fields` directly
- Extended `tests/test_specialist_storage_boundaries.py` to guard `SpecialistStorage` and `specialists.fields` imports outside specialists package

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 405 passed, 85 deselected
```

## For Grok + Paul

- **Identity specialist future:** snapshot contract is stable for framework; warehouse-backed specialists can map internal storage to the same shapes without framework changes.
- Grok: run `pytest -m full` at review per WORKFLOW.
- Suggested commit:

```
refactor(specialists): normalized read snapshots for framework consumers

Specialist dispatch returns FieldSnapshot/FieldContextSnapshot shapes.
Framework and research tooling no longer import specialists.fields or
parse versioned storage layout. Extends storage boundary guard.
```

- Do **not** commit from this slice deliverable.
