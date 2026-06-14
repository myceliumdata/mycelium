# Review — Slice 1530: Legacy graph and resolution removal

**Verdict:** ✅ **Approved + polish nits**

**Reviewer:** Grok  
**Date:** 2026-06-14  
**CI:** `./bin/ci-local` green — **288 passed**, 13 deselected

---

## Scope check

| Requirement | Status |
|-------------|--------|
| `EntityQuery` drops `entity_key` / `binding`; `extra="forbid"` | ✅ |
| Step 1 requires `id` or `lookup` only | ✅ validators + smokes |
| Remove `entity_query_is_legacy_*`, `legacy_entity_key_allowed` | ✅ |
| Remove `resolve_entity`, `resolve_entity_key`, `resolve_entity_for_lookup`, `lookup_entities_by_key` | ✅ |
| Replace `lookup_by_name` → `lookup_by_field` | ✅ `target_resolve` + `registry_helpers` |
| Remove `legacy_entity_lookup_map` | ✅ grep clean in `src/` |
| Supervisor deliver-only (no legacy short-circuit) | ✅ |
| Dispatch legacy branches removed | ✅ |
| Legacy outcome builders removed from `responses.py` | ✅ grep clean |
| `routing.py` deleted | ✅ |
| Specialists use `current_id` in error paths | ✅ |
| Admin UI drops `entity_validated` success badge | ✅ |
| Mandatory smokes: reject `entity_key`, supervisor path | ✅ |
| `MYCELIUM_ALLOW_LEGACY_ENTITY_KEY` removed | ✅ |
| `describe_network` policy untouched | ✅ (1550) |
| No `TODO.md` edit | ✅ |

---

## What looks good

- **~700 lines deleted** from production — legacy graph path is gone; `src/` has zero `query.entity_key` references.
- **`EntityQuery` hard reject** at model boundary (`extra="forbid"`) — no env-flag escape hatch; MCP still rejects legacy JSON at parse time.
- **`registry_helpers.lookup_entities_by_name`** is a clean test fixture bridge using `lookup_by_field`, not resurrecting `lookup_entities_by_key`.
- **Fuzzy rankers kept** for target `lookup_suggested` only (`target_resolve` imports `_rank_suggestions` / `_rank_employer_suggestions`).
- **Critical target smokes retained** — deliver, resolve, MCP public, admin daemon, network status all green.

---

## Test deferral (accepted — 1540 next)

17 legacy `entity_key` test modules excluded via `pytest_ignore_collect` in `conftest.py`. Smoke count drops **427 → 288** until **1540** migrates them. This matches the slice prompt (“minimal fixes here; bulk migration 1540”) and `1540-test-migration` is queued.

`test_core_graph.py` still uses `entity_key` but is **`@pytest.mark.full` only** — not in smoke CI; 1540 prompt already lists it.

---

## Polish nits (non-blocking)

| # | Nit | Suggested follow-up |
|---|-----|---------------------|
| N1 | `conftest.py` has **both** `pytest_ignore_collect` (excludes 17 modules) **and** `pytest_collection_modifyitems` (skip marker) — the latter is dead code once ignore_collect runs | **P7** → remove redundant `modifyitems` hook in **1540** or **1560** |
| N2 | Stale claim file left in `prompts/cursor/in-progress/2026-06-14-1530-legacy-graph-removal.md` | Delete on commit (Grok cleaning up) |
| N3 | `_rank_suggestions(entity_key: str)` param name is legacy vocabulary | Cosmetic rename in **1560** if desired |

---

## CI

```
./bin/ci-local — all steps passed
288 passed, 13 deselected
```

Full integration (`pytest -m full`) not required — not program final slice. **1540** should restore full smoke count before **1560** integration gate.

---

## Commit

```
refactor(query): remove legacy entity_key graph and resolution path
```

**Breaking:** `EntityQuery` no longer accepts `entity_key` or `binding`; legacy outcomes (`entity_unknown`, `entity_key_unresolved`, etc.) removed from response builders.

**Next slice:** `1540-test-migration` (restore deferred test modules).