# Task: Program 1 — Attribute provenance Slice 2 (read path + admin)

> **BLOCKED until Slice 1 approved** — Do not claim this file until `prompts/cursor/done/2026-06-11-1100-attribute-provenance-slice1/review.md` exists with **Approved** (or **Approved + fix slice** where fix is done). If not approved, skip and report.

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/attribute-provenance-program1.md`](../../docs/plans/attribute-provenance-program1.md) — program context (P1-10, P1-11)
- [`docs/plans/attribute-provenance-program1-slice2.md`](../../docs/plans/attribute-provenance-program1-slice2.md) — **locked spec**
- [`docs/plans/ci-framework-specialists-commit.md`](../../docs/plans/ci-framework-specialists-commit.md) — regen + commit practice
- [`src/agents/specialist_fields.py`](../../src/agents/specialist_fields.py) — from Slice 1

**Depends on:** Slice 1 shipped (`specialist_fields.py`, versioned research writes).

**Lane:** Cursor implements code + tests only. Do **not** edit `TODO.md`. Do **not** add `QueryResponse.provenance` (Slice 3).

---

## Objective

All **read** paths use `specialist_fields` helpers. Admin `/status` exposes `versions[]` per extended field. Framework specialists regenerated from template and **committed**.

---

## Implement

Follow [`attribute-provenance-program1-slice2.md`](../../docs/plans/attribute-provenance-program1-slice2.md) exactly:

### 1 — `src/agents/factory/templates/specialist_agent.py.j2`

- Replace inline `_field_has_value`, `_field_display_value`, `_field_is_pending`, `_field_is_na` with imports from `agents.specialist_fields`.
- `_field_display_value` — use `current_value` + format `N/A` / `pending` from `current_status`.
- `_mark_fields_pending` — use `field_has_value` / `field_is_pending` / `field_is_na` on versioned entries.
- `_fields_needing_research` — use `current_version` helpers; preserve stale-retry / `last_error` semantics on **current** pending version.

### 2 — Regenerate and commit framework specialists

Regen from updated template; **commit** all four (CI contract):

- `src/agents/specialists/contact_specialist.py`
- `src/agents/specialists/demographic_specialist.py`
- `src/agents/specialists/professional_specialist.py`
- `src/agents/specialists/social_specialist.py`

Use `AgentFactory` / `regenerate_specialists_from_registry()` (document exact command in `output.md`). No hand-edits to generated logic.

### 3 — `src/network/introspection.py`

- `_entity_field_statuses` — read via `specialist_fields.current_version`; `validate_versioned_field` on extended attrs (fail loud on flat v1).
- `_analyze_storage` — count found/pending/na from current version status.
- Extend `EntityFieldStatus` with `versions: tuple[dict[str, Any], ...]` — full `versions[]` for extended fields; empty tuple for bind fields.

### 4 — `admin-ui/src/types.ts`

Add optional `versions?: Array<Record<string, unknown>>` to `EntityFieldStatus`.

### 5 — `admin-ui/src/App.tsx`

Entity field drill-down: per extended field, `<details>` listing versions (`id`, `at`, `status`, `value`, `sources`, `actor`). Bind rows unchanged.

### 6 — Tests

- `tests/test_network_status.py` — v2 fixtures; assert `versions` in JSON when populated.
- `tests/test_admin_daemon.py` — assert versions on entity drill-down if covered.
- `tests/test_specialist_entity_vocab.py` — framework specialists still pass.
- Versioned storage smoke paths green.

### 7 — Docs

`docs/architecture.md` — admin surfaces version history for extended attrs.

---

## Constraints

- **Flat v1 rejection** on read paths (introspection + specialists) — same operator message as Slice 1.
- **Do not touch:** `QueryResponse`, `EntityQuery.provenance` response builder, `entities.json` / MVR / `bind_index`, `research.py` write path (unless blocking bugfix ≤10 lines — document in `output.md`).
- `./bin/ci-local` green (includes admin-ui build).

---

## Governance (mandatory)

- **Do not edit `TODO.md`.** Roadmap updates are for Grok + Paul after review.
- In `output.md`, add **"For Grok + Paul"**: what to check off, any roadmap notes.
- Cursor delivers: code, tests, task-scoped docs, and `output.md` only.
- **No commit before review** — leave changes in working tree; note suggested commit message in `output.md`.

---

## Deliverables

Move this file to `prompts/cursor/done/2026-06-11-1200-attribute-provenance-slice2/` with:
- `prompt.md` (copy of this file)
- `output.md` — summary + **For Grok + Paul** section
- Run `./bin/ci-local` and record result in `output.md`

---

## Review gate

Grok reviews before Slice 3 merge.
