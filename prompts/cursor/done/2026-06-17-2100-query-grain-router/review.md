# Review — 2026-06-17-2100-query-grain-router

**Verdict: Approved + polish nits**

---

## CI

| Step | Result |
|------|--------|
| `./bin/ci-local` (Grok re-run) | **Pass** |
| smoke pytest | **493 passed**, 100 deselected |
| ruff | clean |
| admin-ui build | ok |

```bash
./bin/ci-local
# CI local: all steps passed.
```

`output.md` claim: 493 smoke passed — matches.

---

## Delivery

`prompt.md` + `output.md` in `done/`. Prompt removed from `in-progress/` and `next/`. Implementation matches claims — router, disambiguation, delivery grain, docs, and 8 smoke tests all present on disk.

**Commit note:** Slice landed as `4d00e9d` (Grok finished after Cursor server died; Paul authorized). Scope is clean — no 1800 default-seed hunks mixed in.

---

## Framework isolation (Paul gate)

| Check | Result |
|-------|--------|
| `lahman` / `baseball` in new `src/` modules | **None** |
| Baseball fixtures | `tests/test_query_grain_router.py` + `examples/networks/baseball/` only |

**Pass.**

---

## Diff reviewed

All 15 files in `4d00e9d` read.

| File | Notes |
|------|--------|
| `src/agents/query_grain_router.py` | **New** — fan-out, filter, 0-hit alias retry, `_result_from_grain_hits`, id-all-grains |
| `src/agents/grain_disambiguation.py` | **New** — structured LLM, injectable `GrainDisambiguator`, safe fallback when key missing |
| `src/agents/target_resolve.py` | Multi-grain orchestration in `resolve_target_step1`; `grain` on `TargetResolveResult`; `_resolve_single_grain_step1` extraction |
| `src/agents/dispatch.py` | `issue_target_delivery(grain=…)`; `_state_with_resolve_grain` for `validate_entity` |
| `src/agents/target_deliver.py` | Step-2 hydration/bind uses `scope.grain` |
| `src/models/state.py` | `EntityQuery.grain`, `LookupSuggestion.grain`, step-2 validator |
| `src/network/delivery.py` | `DeliveryScope.grain` persisted at issue |
| `src/mycelium_mcp/server.py` | Schema copy for grain + multi-grain notes |
| `src/network/introspection.py` | Policy string updated; links `query-grain-router.md` |
| `docs/query-grain-router.md` | **New** — filtering table, mermaid flows, trigger A, 3c, id search, grain override |
| `docs/architecture.md` | One-line runtime-store link (2100-only hunk) |
| `tests/test_query_grain_router.py` | **New** — 8 smoke; monkeypatch path isolation |

`/review` subagent: not used (diff large but bounded; full read completed).

---

## Spec compliance

| # | Criterion | Result |
|---|-----------|--------|
| E1 | Fan-out with per-grain filtering; skip empty filtered | **Pass** — `filter_lookup_for_grain`, `fan_out_lookup`, tests |
| E2 | 0-hit pipeline (alias retry → re-fan-out → suggest/not_found) | **Pass** — code path in `resolve_lookup_multi_grain`; no dedicated smoke test in this file (relies on slice-2 coverage) |
| E3 | Disambiguation LLM trigger A only; mock tests | **Pass** — `_result_from_grain_hits` gates on ≥2 grains; mock inject tests |
| E4 | 3c `ambiguous` → `lookup_suggested` + `grain` | **Pass** |
| E5 | `delivery.grain` set and honored on step 2 | **Pass** — `issue_target_delivery`, `load_delivery_scope`, dispatch `resolve_grain` |
| E6 | `docs/query-grain-router.md` with mermaid | **Pass** |
| E7 | No baseball-specific code in `src/` | **Pass** |
| E8 | `./bin/ci-local` green | **Pass** |

---

## Legacy / dual-path

| Check | Result |
|-------|--------|
| CRM single-grain (`len(grains)==1`) bypasses fan-out | **Pass** — early return in `resolve_target_step1` |
| CRM `create_pending` on open grain 0-hit | **Pass** — `test_crm_single_grain_create_pending_still_works` |
| Existing single-grain multi-match (no disambiguation LLM) | **Pass** — `_result_from_grain_hits` single-grain branch |

---

## Tests

**Strong:** filter table, team-skip, fan-out filtering, mock `chosen_grain` / `ambiguous`, id→delivery grain, `EntityQuery.grain` override, CRM regression, env isolation via monkeypatch.

**Gaps (non-blocking):**

- No smoke for Dodgers-style “2 hits one grain, 0 LLM” through `resolve_target_step1` (doc example only).
- No smoke for `chosen` outcome (single `{grain, entity_id}`).
- No smoke for duplicate id across grains → `not_found`.
- No explicit 0-hit alias retry assertion in this module (E2 code present; test thin).
- CRM “employer partial multi-match unchanged” relies on existing suite, not re-asserted here.

---

## Design critique

**Strong**

- Clean split: `query_grain_router` orchestrates, `grain_disambiguation` isolates LLM, `target_resolve` keeps CRM single-grain path untouched.
- Lazy import avoids circular dependency.
- `GrainDisambiguator` injection makes trigger A testable without API key.
- `DeliveryScope.grain` + dispatch `resolve_grain` closes the step-1→step-2 loop correctly.
- Test env pollution bug (baseball `apply_network_paths` leaking into CRM tests) caught and fixed with monkeypatch — good hygiene.

**Sub-optimal (not blocking)**

1. **`_partial_lookup_result`** calls `_rank_bind_field_fuzzy_suggestions`, which uses `get_entity_registry()` (default grain only). On multi-grain networks, partial lookups that participate on a non-default grain may get fuzzy suggestions from the wrong store. Baseball’s common paths (full `name` or `name+team`) avoid this today; worth a follow-up if partial team `name` queries matter.
2. **`_lookup_suggested_message`** has no branch for `cross_grain_ambiguous` — 3c responses get the generic “near-miss names” message, which may confuse agents.
3. **`disambiguator: Any | None`** on `resolve_target_step1` — should be `GrainDisambiguator | None` for consistency.
4. **`registry._mvr`** private access in `hydrate_matches_for_deliver` — works but couples to registry internals.

---

## Nits

| ID | Severity | Item |
|----|----------|------|
| P1 | LOW | `_partial_lookup_result` fuzzy path should pass grain into entity-resolution helpers (or fan-out partial per grain). |
| P2 | LOW | `responses._lookup_suggested_message`: add `cross_grain_ambiguous` copy (“pick grain + suggested_lookup”). |
| P3 | LOW | `docs/query-grain-router.md` links `seed-bootstrap.md` — file not committed until slice 1800 lands (broken link on clean 2100-only tree). |
| P4 | LOW | Doc markdown: `` `**name**` `` / `` `**team**` `` formatting in `query-grain-router.md` lines 23, 80 — render awkwardly. |
| P5 | LOW | Test gaps: Dodgers no-LLM, `chosen` outcome, duplicate-id `not_found`, explicit E2 alias-retry smoke. |
| P6 | LOW | Type `disambiguator` parameter on `resolve_target_step1`. |
| P7 | LOW | Tests import private `network.paths._RUNTIME_ENV_FIELDS` — consider public test helper. |
| P8 | LOW | Extend `bin/smoke-baseball-e2e` with team-grain scenario (noted in `output.md`). |

Queue P1–P2 + P5 into polish slice or baseball e2e follow-up as Paul prefers. P3 resolves when 1800 lands.

---

## For Paul

- **Verdict:** Approved — slice 3 design locked behavior is implemented; CRM path preserved; CI green.
- **Committed:** `4d00e9d` on `main` (ahead of origin).
- **Next in queue:** `2026-06-18-0900-registry-source-keys-polish-nits.md` (LOW).
- **Optional:** baseball team-grain smoke in `bin/smoke-baseball-e2e` now that router is live.
- **Push:** local only until you ask.