# Review — framework MVR generic vocabulary

**Verdict: Approved + polish nits**

**Reviewer:** Grok  
**Date:** 2026-06-18

---

## CI

| Step | Result |
|------|--------|
| `uv sync --all-extras` | ok |
| `admin-ui` build | ok |
| `ruff` | ok |
| smoke tests | **474 passed**, 97 deselected |

---

## Delivery

`output.md` matches the working tree: 36 modified files + `tests/test_mvr_generic_vocabulary.py` + `docs/architecture.md`. Prompt archived under `done/2026-06-18-1400-framework-mvr-generic-vocabulary/`. No missing implementation vs prompt scope.

---

## Diff reviewed

Full `git diff` read (all 36 changed files + new test). No `/review` subagent (diff ~640 lines, manageable).

**Files:** `docs/architecture.md`; `src/agents/{attribute_write,context,dispatch,entity_registry,entity_resolution,entity_validation,responses,target_deliver,target_resolve}.py`; `src/agents/factory/templates/specialist_agent.py.j2`; `src/agents/specialists/{contact,demographic,professional,social}_specialist.py`; `src/agents/specialists/snapshots.py`; `src/models/state.py`; `src/mycelium_mcp/server.py`; `src/network/{bootstrap/handlers/default_seed,category_mvr_bootstrap,create,mvr,seed_import}.py`; 15 test modules; `tests/test_mvr_generic_vocabulary.py`.

---

## Spec compliance

| # | Criterion | Result |
|---|-----------|--------|
| G1 | `IdentityRecord.bind_values` | Pass |
| G2 | `LookupSuggestion` — `suggested_lookup` only; new reason strings | Pass |
| G3 | Registry CRM helpers removed; dict-shaped bind at call sites | Pass (`ensure_entity_bind` / `bind_provisional` thin wrappers in `attribute_write.py` — acceptable for CRM example/tests) |
| G4 | Dynamic MVR bind in context/snapshots | Pass |
| G5 | `run_mvr_validation(entity, mvr=…)` + categories map | Pass |
| G6 | Generalized suggestion builders | Pass |
| G7 | Responses/dispatch messages MVR-generic | **Partial** — identity summary keys MVR-driven; several message builders still assume `name` + `employer` (see nits) |
| G8 | `registry_entity_to_match` MVR keys | Pass |
| G9 | Generic `default_seed` | Pass |
| G10 | `EXAMPLE_BIND_FIELD_CATEGORY_FALLBACK` | Pass |
| G11–G14 | Create copy, MCP, specialists, architecture | Pass |
| G15 | Real MVR field names in API surfaces | **Partial** — `results[]` correct via `registry_entity_to_match` + `shape_results`; supervisor reshaping drops non-CRM bind keys (see nits) |
| E1 | No `frozenset({"name", "employer"})` in `src/` | Pass (+ guard test) |
| E2 | `IdentityRecord` + MCP schema | Pass |
| E3 | Validation driven by MVR | Pass |
| E4 | CRM capstones + CI green | Pass |
| E5 | Breaking changes documented | Pass |
| E6 | No `CRM-shaped` / `CRM people` in `src/` | Pass |

---

## Legacy / dual-path

CRM example behavior preserved: seed import, capstones, fuzzy employer suggestions, same-bind-field conflict on name+employer all green. Suggestion consumers must use `suggested_lookup` only (documented).

---

## Tests

New `test_mvr_generic_vocabulary.py`: frozenset guard + `bind_from_record` with `name`/`team`. Existing tests updated for `bind_values`, new reason strings, removed registry helpers. Gap: no smoke test that identity-only `assembled`/`found` `results[]` includes all MVR bind fields when grain is not CRM (would have caught supervisor nit).

---

## Design critique

**Strong:** Core refactor is clean and aligned with Paul’s “framework generic, network specific” goal. `registry_entity_to_match(mvr=…)`, `mvr_bind_field_set()`, generalized validation/suggestions, and `default_seed` per-grain MVR are the right primitives. Removing parallel `LookupSuggestion.name`/`employer` simplifies MCP clients.

**Sub-optimal (non-blocking):** `supervisor._identity_records_from_match` still projects rows to `{id, name, employer}` before `shape_results`, so non-CRM grains would lose bind fields (e.g. `team`) on identity-only responses. Message templates in `responses.py` and `dispatch.py` hardcode `employer` phrasing instead of iterating active MVR fields. `_rank_employer_suggestions` alias remains though Paul confirmed no old-schema dependents.

---

## Nits (non-blocking → polish backlog)

| # | Location | Nit |
|---|----------|-----|
| P27 | `supervisor._identity_records_from_match` | Pass through MVR bind keys (or delegate to `registry_entity_to_match` shape) — required before baseball identity queries |
| P28 | `responses.py` / `dispatch.py` message builders | Build “at {field}” phrases from active MVR bind fields, not hardcoded `employer` |
| P29 | `entity_resolution._rank_employer_suggestions` | Remove alias if no callers outside tests |
| P30 | `admin-ui` TS types | Align `LookupSuggestion` with MCP schema (noted in `output.md`) |
| P31 | `test_mvr_generic_vocabulary` | Add end-to-end assertion that `results[]` keys match grain MVR on identity-only deliver |

Logged in `docs/plans/mvr-redesign-polish-m10.md` post-M10 section.

---

## For Paul

**Commit message (use as-is):**

```
refactor(mvr): generic bind vocabulary; remove CRM field hardcoding

IdentityRecord and suggestions use bind_values; validation and context
follow active MVR; drop name/employer-only registry helpers.
```

Grok will commit locally after this review. **No push** unless you ask.

**Next:** P27/P28 polish before baseball `playerID`/stat query work, or a tiny follow-up slice. Then baseball source-key bridge per prior thread.