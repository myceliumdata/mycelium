# Framework MVR generic vocabulary — finish CRM field-name cleanup

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting).

**Priority:** Before baseball `playerID`/uuid work — colleagues reviewing framework; remove CRM-shaped **field names and APIs** from `src/` while keeping CRM **example network** behavior unchanged.

**Parent:** MVR redesign M10 backlog **P14** (partial bind generalization), [`docs/plans/mvr-redesign-polish-m10.md`](../../../docs/plans/mvr-redesign-polish-m10.md), June 2026 Paul thread on CRM terminology residue.

**Principles:**

- **Runtime identity is already MVR-driven** (`bind_values`, per-grain stores) — this slice fixes **types, helpers, messages, and validation** that still assume `name` + `employer`.
- **Framework generic; networks specific** — no `baseball` / `lahman` in `src/`. CRM stays under `examples/networks/crm/` (seed shape, queries, capstones).
- **Breaking changes OK** where they reduce CRM coupling — document in `output.md`; Grok reviews before commit.

---

## Problem (posterity)

June 2026 rename (`SeedRecord` → `IdentityRecord`, target protocol, `bind_values` on disk) **completed**. What remains: framework **surfaces** still hard-code CRM bind field names (`employer`, `name`+`employer` helpers, suggestion reasons, validation table, `BIND_FIELDS` frozensets, MCP/CLI copy).

`rg '\bemployer\b' src/` hits ~30 files. Multi-grain baseball (`name`+`team`) works at storage layer but not at all API/message layers.

---

## Locked scope

| # | Decision |
|---|----------|
| G1 | **`IdentityRecord`** — `id` + `bind_values: dict[str, str]` (aligned with `RegistryEntity`); remove typed `name` / `employer` fields. |
| G2 | **`LookupSuggestion`** — `suggested_lookup` is authoritative; remove parallel `name` / `employer` convenience fields. Rename reasons: `same_bind_field_conflict` (was `same_name_different_employer`), `bind_field_fuzzy_match` (was `employer_sequence_ratio`); keep `sequence_ratio` for name fuzzy where applicable **or** generalize to primary bind field from MVR. |
| G3 | **Registry CRM helpers removed** — delete or deprecate-with-thin-wrapper: `lookup_by_bind_key(name, employer)`, `ensure_bound_entity(name, employer)`, `bind_provisional(name, employer)`. Call sites use `lookup_by_bind_values`, `ensure_entity_bind_fields`, `bind_provisional_from_scope` / dict-shaped bind. |
| G4 | **`bind_from_record` / context** — bind slice from **active grain MVR** `bind_fields`, not `frozenset({"name","employer"})`. `dispatch_read_category_slice(..., bind_fields=...)` receives dynamic set. |
| G5 | **`run_mvr_validation`** — validate **all** `load_mvr().bind_fields` from entity `bind_values`; map field → specialist via `categories.json` `attribute_map` (`resolve_attribute_owner`), not hardcoded `_MVR_VALIDATORS` name/employer table. Generic string rules (min length, not all-digit) per bind field unless category-specific rules exist. |
| G6 | **`target_resolve` / `entity_resolution`** — generalize suggestion builders: given partial lookup + MVR, suggest rows conflicting on one bind field (not employer-only). |
| G7 | **`responses.py` / `dispatch.py` messages** — identity summary keys from MVR `bind_fields`; user-facing copy uses “bind fields” / field labels, not “employer” unless that field exists in active MVR. |
| G8 | **`registry_entity_to_match`** — returns `id` + MVR bind keys only (already mostly true; drop hardcoded employer key if redundant). |
| G9 | **`default_seed` handler** — generic: for each seed row, map `mvr.bind_fields` from seed dict keys (CRM `seed.json` still has `name`/`employer`; baseball unaffected). Docstring: “default JSON seed handler”, not “CRM handler”. |
| G10 | **`CRM_MVR_FIELD_CATEGORY`** — rename/rehome: **not** a CRM-named constant in generic bootstrap. Move fallback map to `examples/networks/crm/` (e.g. committed snippet) **or** rename to neutral `EXAMPLE_BIND_FIELD_CATEGORY_FALLBACK` with comment “CRM example merge helper only”. Runtime still uses `categories.json` `attribute_map` only. |
| G11 | **`network create` skeleton** — neutral default `mvr` description (no “CRM people” string); default grain `person` + `name`/`employer` OK as **illustrative** create template. |
| G12 | **MCP / CLI copy** — help text and schema descriptions MVR-generic; health ping may keep CRM fixture values but comment as “default-network smoke fixture”, not framework vocabulary. |
| G13 | **Framework specialists** — regenerate `src/agents/specialists/{contact,demographic,professional,social}_specialist.py` from updated `specialist_agent.py.j2` (bind_values / dynamic bind in template). |
| G14 | **`docs/architecture.md`** — update identity/result shape bullets to MVR-generic (no “results always include employer”). |

---

## Read first

- `prompts/cursor/WORKFLOW.md`
- `src/models/state.py` — `IdentityRecord`, `LookupSuggestion`
- `src/agents/entity_registry.py` — `registry_entity_to_match`, CRM helpers
- `src/agents/context.py`, `src/agents/specialists/snapshots.py`
- `src/agents/target_resolve.py`, `src/agents/entity_resolution.py`
- `src/agents/entity_validation.py`, `src/agents/responses.py`
- `src/network/category_mvr_bootstrap.py`, `src/network/bootstrap/handlers/default_seed.py`
- `src/network/mvr.py`, `src/mycelium_mcp/server.py`, `src/main.py`
- `tests/test_mvr_target_resolve.py`, `tests/test_target_step1_lookup_clarity.py`, `tests/test_entity_validation.py`
- `docs/plans/mvr-redesign-polish-m10.md` § P14

---

## Implement

### Models & protocol

- Refactor `IdentityRecord`, `lookup_suggestion()`, MCP JSON schema export.
- Update `LookupSuggestion` consumers (admin, introspection, tests) to use `suggested_lookup` only.

### Agents & graph

- Generalize bind/context/snapshots/responses/dispatch/supervisor paths per G4–G8.
- Update suggestion reason strings and message templates; fix any admin-ui expectation if reason strings are asserted (prefer substring “bind” not “employer”).

### Validation

- `run_mvr_validation(entity)` or equivalent reading `bind_values` + MVR + categories map.
- Preserve CRM capstone behavior: absurd employer `"A"` still fails when `employer` is in MVR.

### Bootstrap & network create

- Generic `default_seed` row → `ensure_entity_bind_fields` with fields present in seed row ∩ MVR.
- Neutral create template strings.

### Specialists

- Template: `context.bind` as dict keyed by MVR fields; `IdentityRecord` construction uses `bind_values`.
- Regenerate four framework specialists.

### Tests

| Test | Assert |
|------|--------|
| CRM capstones / `test_example_network_capstones` | Still green — CRM network unchanged |
| `test_multi_mvr_entity_stores` | Player grain bind context uses `name`+`team`, not employer |
| New: `test_bind_from_record_uses_mvr_fields` | Baseball or stub MVR with `team` field appears in bind |
| New: `test_no_hardcoded_crm_bind_frozenset_in_src` | Guard: no `frozenset({"name", "employer"})` in `src/` |
| Suggestion tests | Updated reason strings; same-bind-field conflict still works for CRM name+employer |

Run `./bin/ci-local` — all smoke tests green.

---

## Scope boundaries (strict)

**May modify:**

- `src/` (framework), `tests/`, `docs/architecture.md` (identity/MVR sections only)
- `src/agents/factory/templates/specialist_agent.py.j2` (+ regen specialists)
- `examples/networks/crm/` **only** if needed for moved `CRM_MVR_FIELD_CATEGORY` fallback file

**Do not modify:**

- `examples/networks/baseball/` (no baseball work in this slice)
- `TODO.md`
- CRM `seed.json` row shape (`name`, `employer` stay)
- Query orchestrator grain-selection (separate future slice)
- Derivative / warehouse / `playerID` bridge

---

## Explicit non-goals

- Removing word “CRM” from docs when referring to the **example network**
- Changing `examples/networks/crm-metering` query JSON (still valid CRM MVR)
- Admin UI full redesign
- Renaming `seed.json` / `seed_bootstrap` bootstrap vocabulary (intentionally kept per prior slice)

---

## Exit criteria

| # | Criterion |
|---|-----------|
| E1 | No `frozenset({"name", "employer"})` (or equivalent hardcoded pair) in `src/` |
| E2 | `IdentityRecord` uses `bind_values`; MCP schema updated |
| E3 | `run_mvr_validation` driven by MVR + categories map |
| E4 | CRM capstones + `./bin/ci-local` green |
| E5 | `output.md` lists breaking changes for colleagues (MCP schema, suggestion reasons, removed helpers) |
| E6 | `rg 'CRM-shaped|CRM people' src/` → no matches |

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- **For Grok + Paul** in `output.md`: note any admin-ui / MCP client follow-ups for external colleagues.

## When finished

Per `prompts/cursor/WORKFLOW.md` — no commit/push.

**Suggested commit message:**

```
refactor(mvr): generic bind vocabulary; remove CRM field hardcoding

IdentityRecord and suggestions use bind_values; validation and context
follow active MVR; drop name/employer-only registry helpers.
```