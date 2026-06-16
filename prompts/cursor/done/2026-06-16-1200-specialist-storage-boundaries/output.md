# Specialist storage boundaries — dispatch protocol

## Summary

Framework code outside `src/agents/specialists/` no longer imports `SpecialistStorage` or reads `agents/*/storage.json` directly. Bind, seed, research, provenance, and context paths dispatch through `agents.specialists.protocol`; `entities.json` cache and indexes sync from specialist-returned values only.

## Protocol surface (`src/agents/specialists/protocol.py`)

- `resolve_owner`, `dispatch_write_fields`, `dispatch_read_fields`, `dispatch_bootstrap_entity`
- `dispatch_write_bind_fields_multi`, `dispatch_read_category_slice`
- `dispatch_analyze_category_storage`, `dispatch_entity_field_statuses`, `dispatch_ensure_category_storage`
- Research: `dispatch_mark_pending`, `dispatch_persist_research`, `dispatch_append_research_audit`

Handlers live in `handlers.py`, `research_handlers.py`; committed specialists attach via `_protocol_exports.attach_protocol_handlers(globals(), ...)`.

## Refactored framework modules

| Module | Change |
|--------|--------|
| `attribute_write.py` | Multi-category bind writes via dispatch; registry sync only |
| `context.py` | `dispatch_read_category_slice` |
| `query_provenance.py` | `dispatch_read_fields(..., include_versions=True)` |
| `entity_growth.py` | Attribution timestamps via dispatch read |
| `introspection.py` | Entity field statuses + bind versions via dispatch |
| `tools/research.py` | Persist/mark-pending/audit via dispatch (no `storage` param on `run_field_research`) |
| `agent_factory.py`, `create.py` | `dispatch_ensure_category_storage` |

## Specialists package

- `fields.py` — versioned field helpers (moved from `specialist_fields.py`)
- `specialist_fields.py` — thin re-export shim for tests
- `specialists/__init__.py` — exports protocol dispatch, not `SpecialistStorage`
- Factory template updated: `specialists.fields` import, protocol handlers, no `storage=` on research call

## Tests

- `tests/test_specialist_storage_boundaries.py` — AST guard: no `SpecialistStorage` import outside specialists package
- Research mocks updated: no `storage` kwarg; versioned `versioned_found` blobs (not flat v1)
- `./bin/ci-local`: **405 passed**, 86 deselected

## Docs

- `docs/architecture.md` — specialist storage boundaries addendum
- `docs/plans/attribute-provenance-program2.md` — superseded-for-storage-I/O note

## For Grok + Paul

- **Identity specialist future:** `entities.json` registry ownership can move to an identity specialist without changing dispatch contract — framework already syncs cache from specialist responses (S2).
- **Examples CRM specialists** (`examples/networks/crm/specialists/`) not regenerated; committed `src/agents/specialists/*` are canonical.
- Grok: run `pytest -m full` at review per WORKFLOW.
- Suggested commit:

```
refactor(specialists): enforce storage boundaries via dispatch protocol

Framework routes writes/reads through specialist handlers; registry
cache/indexes sync from returned values. Seed bootstrap is registry-first
then specialist bootstrap_entity. Eliminates direct SpecialistStorage
access outside specialists package.
```

- Do **not** commit from this slice deliverable.
