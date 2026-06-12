# Program 1 — Slice 2: Read path — specialists + introspection

**Status:** Ready after Slice 1 review  
**Program:** [`attribute-provenance-program1.md`](attribute-provenance-program1.md)  
**Depends on:** Slice 1 (`specialist_fields.py`, versioned research writes)

---

## Objective

All **read** paths use `specialist_fields` helpers. Admin `/status` exposes `versions[]` per extended field. Framework specialists regenerated from template.

---

## Implement

### 1 — `src/agents/factory/templates/specialist_agent.py.j2`

Replace inline `_field_has_value`, `_field_display_value`, `_field_is_pending`, `_field_is_na`, pending-mark logic with imports from `agents.specialist_fields`.

`_field_display_value` → `current_value` + status formatting (`N/A`, `pending`).

`_fields_needing_research` — use `current_version` / `field_has_value` / `field_is_na` on versioned entries.

### 2 — Regenerate framework specialists

Regen and commit:

- `contact_specialist.py`
- `demographic_specialist.py`
- `professional_specialist.py`
- `social_specialist.py`

Per `ci-framework-specialists-commit` practice (committed fallbacks).

### 3 — `src/network/introspection.py`

- `_entity_field_statuses` — read via `specialist_fields.current_version`; validate versioned shape (fail loud on flat v1).
- `_analyze_storage` — count found/pending/na using current version status.
- Extend `EntityFieldStatus` dataclass with `versions: list[dict[str, Any]]` (tuple in frozen dataclass) — full `versions[]` for extended fields; empty for bind fields.

### 4 — `admin-ui/src/types.ts`

Add optional `versions?: Array<Record<string, unknown>>` to `EntityFieldStatus`.

### 5 — `admin-ui/src/App.tsx`

Entity field table: per extended field, `<details>` showing JSON or simple list of versions (`id`, `at`, `status`, `value`, `sources`, `actor`). Bind rows unchanged.

### 6 — Tests

- `tests/test_network_status.py` — v2 fixtures; assert `versions` in JSON status when populated.
- `tests/test_admin_daemon.py` — if entity drill-down covered, assert versions present.
- Framework specialist smoke tests still pass.

### 7 — Docs

`docs/architecture.md` — admin surfaces version history for extended attrs.

---

## Do NOT

- `QueryResponse.provenance` (Slice 3)
- MVR / entity registry changes
- `TODO.md`

---

## Verification

`./bin/ci-local` green.