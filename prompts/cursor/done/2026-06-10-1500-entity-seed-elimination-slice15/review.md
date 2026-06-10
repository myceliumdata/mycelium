# Review — Seed elimination Slice 15 (registry-only resolution)

**Reviewer:** Grok (June 2026)  
**Verdict:** **Approve** (was *Approve + fix slice* — fix `1545` reviewed and approved June 2026).

---

## Summary

Slice 15 removes seed branches from `entity_resolution.py`, adds `lookup_entities_by_key`, updates routing/dispatch/introspection call sites, and migrates entity-protocol test fixtures to `import_seed_for_test`. Slice 15 verify set passes. Governance respected: no `review.md` from Cursor, no `TODO.md` edits.

One out-of-scope touch (`research_gate.py`) is documented and reasonable — multiple validated registry rows (e.g. Kevin Zhang) must not block research after all matches carry `_registry: True`. Full simplification remains Slice 16.

---

## Checklist

| Item | Verdict | Notes |
|------|---------|-------|
| Registry-only `resolve_entity` | Pass | Seed imports removed from resolution module |
| `lookup_entities_by_key` | Pass | UUID + name; used by routing |
| Suggestions from registry | Pass | `_iter_registry_entities` (uses private `_data` — nit) |
| Call sites (routing, dispatch, introspection) | Pass | No `agents.seed` in modified `src/` resolution path |
| Test fixtures | Pass | `import_seed_for_test` / `import_seed_at_root` in `network_helpers` |
| `research_gate.py` | Pass* | Out of prompt file list but justified; defer full cleanup to Slice 16 |
| Slice 15 verify | Pass | 42 passed (prompt command) |
| Broader entity smoke | Pass | 48 passed on `test_entity_*.py` touched by slice |
| **Full smoke suite** | **Fail** | **3 failures** in `test_supervisor_routing.py` |

---

## Blocking — supervisor routing tests

Cursor ran the **slice verify set only**, not full smoke. Full smoke (`uv run pytest -m smoke -q`) reports:

```
FAILED tests/test_supervisor_routing.py::test_supervisor_agent_plans_no_specialists_without_attrs
FAILED tests/test_supervisor_routing.py::test_supervisor_agent_classifies_requested_attributes
FAILED tests/test_supervisor_routing.py::test_supervisor_triggers_creation_for_unregistered_specialist
```

**Root cause:** `supervisor_agent` uses `resolve_entity` (registry-only). Three tests use `entity_key="any-key"` with **seed.json only** (or no fixture import) and never call `import_seed_for_test`. After Slice 15:

- Isolated env: `any-key` → `unknown` / no match (audit: *"unknown entity"*), not *"resolved via seed"*.
- Full suite: order-dependent — passes/fails based on leaked `entities.json` state from other tests.

**Required fix (before Slice 16):**

Update `tests/test_supervisor_routing.py` supervisor integration tests to:

1. Set `MYCELIUM_ENTITIES_PATH` (and network root as needed).
2. `import_seed_for_test(seed)` after writing `seed.json` (or use `import_seed_at_root`).
3. `reset_entity_registry()` in setup/teardown.
4. Assert **`resolved via registry`** (not `resolved via seed`) where applicable.

`test_supervisor_routing.py` was not in the Slice 15 prompt file list, but the resolution change **requires** these updates — include in a small **fix slice** or amend Slice 15 completion.

Re-run **`uv run pytest -m smoke -q`** before sign-off.

---

## Nits (non-blocking)

| Nit | Notes |
|-----|-------|
| `_iter_registry_entities` | Peeks at `registry._data` — spec mentioned `list_entities()` which does not exist; acceptable for now |
| Verify scope | Document full-smoke result in fix slice `output.md` after repair |

---

## Tests (re-verified)

```bash
uv run ruff check src/agents/entity_resolution.py src/agents/routing.py src/agents/dispatch.py
uv run pytest tests/test_entity_key_suggestions.py tests/test_entity_unknown_mvr.py \
  tests/test_entity_registry_bind.py tests/test_network_status.py -m smoke -q
→ 42 passed

uv run pytest -m smoke -q
→ 267 passed, 3 failed (supervisor routing — blocking)
```

---

## Recommendation

~~Do not commit until fix lands.~~ **Fix `1545` approved** — commit Slice 15 + fix together; mark done in `TODO.md`; proceed to Slice 16.

Suggested commit message (after fix):

```
Registry-only entity resolution (Slice 15).

lookup_entities_by_key; registry suggestions; test fixtures import seed;
research_gate fix for multiple validated registry rows.
```