# Specialist normalized read responses — eliminate framework schema coupling

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting).

**Context:** Slice `2026-06-16-1200-specialist-storage-boundaries` removed direct `SpecialistStorage` / `storage.json` access from framework code. **Residual coupling:** framework modules still import `agents.specialists.fields` and parse versioned storage shapes (`versions[]`, `is_versioned_field`, `current_version`, etc.) from dispatch read responses and graph context.

Paul confirmed (June 2026): shared `handlers.py` for early CRM specialists is OK. **This slice** makes **read/context responses** specialist-owned so framework never parses internal storage schema.

**Fixes concern #3:** Once framework only consumes normalized snapshots, changing specialist storage strategy (or baseball warehouse-backed shapes) does not require editing `query_provenance.py`, `entity_growth.py`, or `tools/research.py`.

**Prerequisite:** Storage-boundaries slice merged or present in working tree (dispatch protocol exists).

---

## Locked decisions (Paul, June 2026)

| # | Decision |
|---|----------|
| N1 | Framework **must not** import `agents.specialists.fields` (or parse `versions[]` / `current_version_id`) outside `src/agents/specialists/`. |
| N2 | Specialists (via handlers/protocol) return **framework-ready snapshots** — opaque to storage layout. |
| N3 | `tools/research.py` consumes **normalized** context only; no versioned-field helpers. |
| N4 | External query/provenance/admin behavior unchanged for CRM smoke + capstone tests. |

---

## Read first

- `prompts/cursor/WORKFLOW.md`
- `prompts/cursor/done/2026-06-16-1200-specialist-storage-boundaries/prompt.md` + `review.md`
- `src/agents/specialists/handlers.py` — `read_fields`, `read_category_slice`
- `src/agents/specialists/protocol.py`
- `src/agents/context.py`
- `src/agents/query_provenance.py`
- `src/agents/entity_growth.py`
- `src/tools/research.py` — `peer_specialists_for_entity`, `peer_display_for_prompt`, `operator_overrides_for_target_fields`
- `src/agents/specialists/contact_specialist.py` — `_research_context` (passes raw `storage` row)
- `tests/test_specialist_storage_boundaries.py`

---

## Objective

Define and enforce a **normalized field snapshot contract** returned by all specialist read/context dispatch paths. Refactor framework consumers to use snapshot fields only. Extend the import boundary test to forbid `agents.specialists.fields` outside the specialists package.

---

## Normalized contract (implement in specialists package)

Add documented types/helpers in `src/agents/specialists/` (e.g. `snapshots.py` or extend `handlers.py`):

### `FieldSnapshot` (per field, per entity)

Returned by `read_fields` / module `read_fields` handler for **every** requested field key (missing → `status: "empty"`):

```python
{
    "value": str | None,           # current display value
    "status": str,                 # found | na | pending | empty
    "updated_at": str | None,      # ISO8601 of current version (any status)
    "provenance": {                # present only when include_provenance=True
        "current_version_id": str | None,
        "versions": list[dict],    # copy safe for API
    } | None,
}
```

### `FieldContextSnapshot` (for graph / research context slices)

Returned by `read_category_slice` per field (extended attrs only; bind fields still excluded):

```python
{
    "value": str | None,
    "status": str,                 # found | na | pending | empty
    "sources": list[str],          # URLs for prompt display (empty if N/A)
    "updated_at": str | None,
    "operator": {                  # for research deference block
        "set": bool,
        "value": str | None,
        "at": str | None,
        "note": str | None,
    },
}
```

**Normalization lives only in specialists package** — map from internal versioned storage via existing `fields.py` helpers.

---

## Implement

### 1 — Normalize read outputs

- `handlers.read_fields`: always return `{field: FieldSnapshot}`; when `include_versions=True`, set `provenance` sub-object (rename param to `include_provenance` in handlers; keep `include_versions` as alias on dispatch for backward compat or update all call sites).
- `handlers.read_category_slice`: return `{entity_id: {field: FieldContextSnapshot}}` — **not** raw storage rows.
- `handlers.entity_field_statuses_for_category`: already returns status rows — ensure consistent with snapshots (may reuse normalizer).
- Update `protocol.dispatch_read_fields` docstring to document contract.

### 2 — Framework consumers (no `specialists.fields` imports)

| Module | Change |
|--------|--------|
| `query_provenance.py` | Use `entry["provenance"]` from `FieldSnapshot`; drop any `versions[]` parsing |
| `entity_growth.py` | Use `entry["updated_at"]` from snapshot; remove `is_versioned_field` / `validate_versioned_field` |
| `context.py` | `strip_bind_fields` may become unnecessary for normalized slices — context `specialists` dict holds `FieldContextSnapshot` maps only |
| `tools/research.py` | Remove **all** `agents.specialists.fields` imports. `peer_display_for_prompt` reads `value` + `sources` from `FieldContextSnapshot`. `operator_overrides_for_target_fields` reads `operator` block from normalized `context["storage"]` **or** delete and build overrides list in specialist `_research_context` via specialist helper |

### 3 — Specialist `_research_context` (template + committed specialists)

`_research_context` currently passes raw storage row:

```python
"storage": strip_bind_fields(raw)  # leaks versioned shape into tools.research
```

Replace with normalized map:

```python
"storage": normalize_context_fields(raw, category="contact")  # specialists helper
```

Update `specialist_agent.py.j2` and regenerate or patch committed `contact_specialist`, `demographic_specialist`, `professional_specialist`, `social_specialist`.

Peer slices in context are already from `read_category_slice` — after step 1 they are normalized; `_research_context` peer copy should pass through without re-parsing raw rows.

### 4 — Boundary test extension

Extend `tests/test_specialist_storage_boundaries.py`:

- Fail if any `src/**/*.py` **outside** `src/agents/specialists/` imports `agents.specialists.fields` or `agents.specialist_fields`.
- **Allowlist:** none in `src/` except optionally keep `src/agents/specialist_fields.py` as deprecated shim — if shim remains, it must not be imported by framework modules (only tests). Prefer: delete shim + point tests at `agents.specialists.fields` directly.

### 5 — Tests

- Update tests that construct raw versioned blobs for framework modules to use normalized snapshots.
- All existing smoke tests green: `./bin/ci-local`
- Explicitly re-run:
  - `tests/test_query_provenance.py`
  - `tests/test_research.py` (operator deference, peer context)
  - `tests/test_specialist_sync_research.py`
  - `tests/test_program2_bootstrap_matrix.py`
  - `tests/test_example_network_capstones.py`
  - `tests/test_specialist_storage_boundaries.py`

---

## Success criteria

- [ ] `./bin/ci-local` green
- [ ] Grep: no `specialists.fields` / `specialist_fields` import in `src/` outside `src/agents/specialists/`
- [ ] Grep: no `is_versioned_field` / `current_version` / `validate_versioned_field` in `src/tools/research.py`, `src/agents/query_provenance.py`, `src/agents/entity_growth.py`, `src/agents/context.py`
- [ ] `read_fields(..., include_versions=True)` returns snapshots with `provenance` key — framework never inspects internal `versions[]` layout
- [ ] Research operator deference + peer context blocks still render correctly in tests
- [ ] CRM provenance query + entity growth attribution timestamps unchanged behaviorally

---

## Out of scope

- Changing write/bind/seed dispatch (storage-boundaries slice)
- Per-specialist unique storage backends (baseball warehouse)
- `entities.json` → identity specialist
- **`TODO.md`** — do not edit

---

## May modify

- `src/agents/specialists/**`
- `src/agents/context.py`, `query_provenance.py`, `entity_growth.py`
- `src/tools/research.py`
- `src/agents/factory/templates/specialist_agent.py.j2`
- `src/agents/specialist_fields.py` (delete or deprecate shim)
- `tests/**` as needed
- `docs/architecture.md` — one paragraph on normalized read contract (task-scoped only)

---

## Deliverables

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-16-1400-specialist-normalized-read-responses/` with `prompt.md`, `output.md` (**For Grok + Paul** section)
3. Do not commit

Suggested commit message:

```
refactor(specialists): normalized read snapshots for framework consumers

Specialist dispatch returns FieldSnapshot/FieldContextSnapshot shapes.
Framework and research tooling no longer import specialists.fields or
parse versioned storage layout. Extends storage boundary guard.
```