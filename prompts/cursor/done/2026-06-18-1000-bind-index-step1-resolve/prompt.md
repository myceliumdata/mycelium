# Bind-index fallback for step-1 full MVR lookup (multi-team players)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting).

**Priority:** Ship blocker for baseball identity manual gate (Check 4). Fixes **problem 1** only: multi-team players must resolve via any bootstrap `bind_index` alias, not only the primary `bind_values` tuple indexed in field indexes.

**Parent:** [`docs/seed-bootstrap.md`](../../../docs/seed-bootstrap.md) § bind alias vs field alias; [`docs/plans/baseball-example-program.md`](../../../docs/plans/baseball-example-program.md) § Hank Aaron multi-team; ship gate [`docs/manual-checks/2026-06-17-baseball-identity-ship-gate.md`](../../../docs/manual-checks/2026-06-17-baseball-identity-ship-gate.md).

**Out of scope (separate slice — problem 2):** multi-grain fan-out when player misses and team grain wins; `same_bind_field_conflict` suggestion flood; polluted `field_aliases` from lazy LLM expansion. Do not change disambiguation or suggestion behavior in this slice.

---

## Problem (posterity)

Bootstrap correctly writes alternate team binds via `add_bind_alias` → `bind_index` only (primary `bind_values` unchanged; field indexes not rebuilt). Step-1 resolve uses `lookup_by_target_lookup` → field-index AND only. Result:

- `{name: "Hank Aaron", team: "Atlanta Braves"}` → **hit** (primary bind)
- `{name: "Hank Aaron", team: "Milwaukee Braves"}` → **miss** (alias bind in `bind_index` only)

`lookup_by_bind_values` already resolves alias keys; step-1 never calls it.

---

## Locked behavior (do not reinterpret)

### When bind_index fallback applies

After field-index `intersect_lookup` returns `[]`, if the lookup is a **full MVR** for this grain (`is_full_mvr_lookup(lookup, mvr)` — all bind fields present, non-empty), try `lookup_by_bind_values(normalized_lookup)`.

| Outcome | Return |
|---------|--------|
| bind_index hit | `[entity.id]` (singleton list, same shape as field-index hit) |
| bind_index miss | `[]` (unchanged) |

### When bind_index fallback does NOT apply

- **Partial lookups** (one bind field only) — used by `_same_bind_field_conflict_suggestions`, fuzzy paths, per-field fan-out filters. Field-index-only behavior unchanged.
- **Field index already hit** — do not consult bind_index (field index wins; should agree for primary binds).
- **Open-grain create_pending paths** — no change to create semantics; only the read path before 0-hit handling.

### Fan-out / grain router

`fan_out_lookup` and `_resolve_single_grain_step1` call `lookup_by_target_lookup`. Fixing the registry method fixes both without router changes.

### CRM regression

Single-grain CRM: full MVR lookups behave as today when primary bind matches field index. bind_index fallback only runs on 0-hit full MVR — CRM rows typically have matching primary bind + bind_index key, so no behavior change expected. Verify capstones.

---

## Implement

### 1. `EntityRegistry.lookup_by_target_lookup` (`src/agents/entity_registry.py`)

1. Run existing `intersect_lookup` on `_field_indexes`.
2. If non-empty → return as today.
3. If empty and `is_full_mvr_lookup(lookup, self._mvr)`:
   - Normalize via `normalized_lookup_values(lookup)` from `network.mvr`.
   - `entity = self.lookup_by_bind_values(norm)`.
   - If entity → return `[entity.id]`.
4. Return `[]`.

Keep `lookup_by_bind_values` unchanged. Document the two-index model in the method docstring (field index for partial/AND; bind_index fallback for full MVR alias binds).

### 2. Tests (required)

**Unit / registry** (`tests/test_entity_store_evolution.py` or new `tests/test_bind_index_step1_lookup.py`):

- Register player with primary `{name, team: Brooklyn}`; `add_bind_alias` for `{name, team: Los Angeles}`.
- `lookup_by_target_lookup({"name", "team: Brooklyn"})` → 1 id (field index).
- `lookup_by_target_lookup({"name", "team: Los Angeles"})` → 1 id, **same uuid** (bind_index fallback).
- Partial `lookup_by_target_lookup({"team": "Los Angeles"})` → field-index behavior only; must **not** return entity via bind_index alone.

**Lahman handler** (`tests/test_lahman_seed_handler.py`):

- Extend `test_lahman_seed_handler_multi_team_same_player_id`: after bootstrap, assert `lookup_by_target_lookup` (not only `lookup_by_bind_values`) resolves both team tuples to one id.

**Graph / step-1** (`tests/test_mvr_target_resolve.py` or baseball fixture test):

- Baseball player grain fixture: primary + alias binds; `run_query(EntityQuery(lookup={...}, grain="player"))` with alias team → `lookup_resolved`, `total_matches == 1`.

Use existing baseball test fixtures (`_baseball_registry`, lahman `multi_team` seed) — **no** full Lahman warehouse in unit tests.

### 3. Docs (required)

**`docs/seed-bootstrap.md`** — in the bind alias vs field alias table, add one line: step-1 full MVR lookup consults `bind_index` when field-index AND misses.

**`docs/manual-checks/2026-06-17-baseball-identity-ship-gate.md`** — Check 4: document that `{name: "Hank Aaron", team: "Milwaukee Braves"}` with `"grain": "player"` should pass after this slice (optional second command alongside Atlanta Braves).

Do **not** edit `TODO.md`.

---

## Verification (Cursor)

```bash
./bin/ci-local
```

Manual (Grok/Paul after merge — optional in `output.md`):

```bash
export ROOT=/tmp/mycelium-baseball-benchmark
export MYCELIUM_NETWORK_ROOT="$ROOT"
./bin/baseball-query '{"lookup": {"name": "Hank Aaron", "team": "Milwaukee Braves"}, "grain": "player"}'
# Expect: lookup_resolved, total_matches: 1
```

**No data reload required** for problem 1 — existing benchmark roots already have correct `bind_index` keys from bootstrap.

---

## Principles

- Framework generic — no baseball strings in `src/` production code.
- Minimal diff — registry lookup composition only; no bootstrap or Lahman handler changes.
- Match existing normalization (`normalize_field_index_value` / `make_bind_key`).

---

## Deliverables

Per `prompts/cursor/WORKFLOW.md` completion checklist:

- `prompts/cursor/done/2026-06-18-1000-bind-index-step1-resolve/`
  - `prompt.md` (this file)
  - `output.md` — summary, test counts, **For Grok + Paul** (ship gate note, problem 2 deferred)
- Do not commit.

**Suggested commit message:** `fix(registry): step-1 full MVR lookup falls back to bind_index for alias binds`