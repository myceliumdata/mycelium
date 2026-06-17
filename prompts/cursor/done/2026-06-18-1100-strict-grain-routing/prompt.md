# Strict lookup-key grain routing — remove fan-out, rename bind fields, drop `EntityQuery.grain`

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting).

**Priority:** Baseball identity ship — problem 2. Paul reloads benchmark data; this slice is a **breaking** manifest + handler + protocol change. Run after `2026-06-18-1000-bind-index-step1-resolve` is merged.

**Principles:** Delete confusing machinery, don't flag it. No fan-out, no grain-disambiguation LLM, no `EntityQuery.grain`. Lookup keys **are** the contract. Framework stays generic — behavior driven by `network.json` bind field names.

---

## Problem (posterity)

Multi-grain fan-out (`query_grain_router.py`) strips keys per grain, re-fans-out after alias expansion, and invokes a grain-disambiguation LLM. With overlapping `name` on team + player grains it returns wrong results (e.g. Hank Aaron + Milwaukee → three team entities). `EntityQuery.grain` was an escape hatch for that machinery. Without our design context the code looks bonkers to humans and future LLMs.

**Locked contract (baseball):**

| Lookup keys | Grain | Meaning |
|-------------|-------|---------|
| `player` + `team` | `player` | Person on a roster |
| `team` only | `team` | Fan-facing franchise |
| `player` only | — | `lookup_incomplete` (`required_fields: ["team"]`) |
| anything else | — | `not_found` or `lookup_incomplete` with clear message |

Disjoint bind field names — no fan-out needed.

---

## Baseball manifest + bootstrap (breaking)

### `examples/networks/baseball/network.json`

```json
"team":   { "bind_fields": ["team"], ... }
"player": { "bind_fields": ["player", "team"], ... }
```

### Lahman handler + fixtures

- Team rows: `bind_values: {"team": team_name}` (was `name`)
- Player rows: `bind_values: {"player": display_name, "team": team_label}` (was `name`)
- `add_bind_alias` / `ensure_entity_bind_fields` use new keys
- Update `examples/networks/baseball/guide.md`, `README.md`

### `docs/plans/baseball-example-program.md` + `docs/query-grain-router.md`

- **Replace** fan-out / disambiguation mermaid with lookup-key routing table (short).
- Delete or archive sections on fan-out filtering, trigger A LLM, cross-grain 3c.

---

## Framework — delete fan-out, add key inference

### Remove (or gut if imports remain)

- `src/agents/query_grain_router.py` — `fan_out_lookup`, `filter_lookup_for_grain`, `resolve_lookup_multi_grain`, `_result_from_grain_hits`, grains_with_filtered_lookup fan-out paths
- `src/agents/grain_disambiguation.py` — delete if nothing references it
- `resolve_target_step1` branches that call `resolve_lookup_multi_grain`

### Add / replace

**`infer_grain_from_lookup(lookup, mvr_config) -> str | LookupError`**

- Normalize keys via `normalized_lookup_values`.
- For each declared grain, check whether lookup keys are a **superset match** for that grain's full MVR (all bind fields present → that grain) or exact single-field match for single-bind grains.
- Baseball rules above; generic rule: **exactly one grain matches** → use it; **zero** → `lookup_incomplete` / `not_found`; **two+** → `ValueError` or `lookup_incomplete` ("ambiguous lookup keys") — should not happen with disjoint field names.

**`resolve_target_step1` (multi-grain path):**

1. `id` only → keep `resolve_id_all_grains` (unchanged).
2. `lookup` → `infer_grain_from_lookup` → `_resolve_single_grain_step1(query, grain=inferred)`.
3. Single-grain networks (CRM) → unchanged.

### Remove public `grain` override

- **`EntityQuery`:** delete `grain` field + validator branch; update `models/state.py` docstrings.
- **`resolve_target_step1`:** delete `grain: str | None = None` parameter (tests must not pass it).
- **`issue_target_delivery`:** keep internal `grain` from resolve result (delivery scope).
- MCP / `responses.py` / JSON schema introspection: remove `grain` from step-1 query examples.

---

## Tests — no `grain` arg on queries (mandatory)

**Rule:** Step-1 tests use **lookup key shapes only**. No `EntityQuery(..., grain=...)`. No `resolve_target_step1(..., grain=...)`.

**Still OK:** `get_entity_registry(grain="team")` / `load_mvr(grain="player")` when **setting up** registry rows — that is store selection, not routing.

### Delete or replace `tests/test_query_grain_router.py`

Remove tests that only validate fan-out / disambiguation LLM:

- `test_filter_lookup_name_and_team_splits_grains`
- `test_fan_out_name_and_team_filters_team_grain`
- `test_mock_disambiguation_*` (all three)
- `test_zero_hit_alias_retry_smoke` (multi-grain re-fan-out)
- `test_entity_query_grain_skips_fan_out`

**Keep / rewrite** (rename file → `tests/test_strict_grain_routing.py`):

| Scenario | Lookup (new keys) | Expected |
|----------|-------------------|----------|
| Team canonical | `{team: "New York Yankees"}` | `lookup_resolved`, team grain |
| Team nickname + alias expander | `{team: "Bronx Bombers"}` | resolved on team grain (mock expander) |
| Dodgers multi-match | `{team: "Dodgers"}` + field aliases | 2 team ids, team grain |
| Player full MVR | `{player: "Washington", team: "Washington Nationals"}` | player grain (no team grain hit) |
| Player alias bind | `{player: "Hank Aaron", team: "Los Angeles Dodgers"}` | `lookup_resolved` (bind_index slice) |
| `player` only | `{player: "Hank Aaron"}` | `lookup_incomplete`, `required_fields` includes `team` |
| Hank Aaron + Milwaukee | `{player: "Hank Aaron", team: "Milwaukee Braves"}` | `lookup_resolved`, 1 match |
| Duplicate id all grains | `resolve_id_all_grains` | unchanged |
| Delivery grain on scope | id step-1 → step 2 | `scope.grain` set |
| CRM single grain | `{name, employer}` create_pending | unchanged |

Use `_prepare_baseball_multi_grain` fixture but update `bind_values` to `team` / `player`+`team` keys.

### Update other tests

| File | Change |
|------|--------|
| `tests/test_closed_identity_lazy_aliases.py` | Drop `grain="team"` on `resolve_target_step1`; use `{team: "Bronx Bombers"}`, `{team: "Dodgers"}`, `{team: "XYZZY"}` |
| `tests/test_mvr_target_resolve.py` | `test_baseball_player_alias_bind_step1_lookup_resolved` — remove `grain="player"`; use `player`+`team` keys |
| `tests/test_multi_mvr_entity_stores.py` | Expect team `bind_fields == ["team"]` |
| `tests/test_lahman_seed_handler.py` | Assert `player` / `team` bind keys on committed rows |
| Any test using `lookup={"name": ...}` on team grain | → `lookup={"team": ...}` |

Grep repo for `grain="team"`, `grain="player"`, `EntityQuery(.*grain` in tests after edits — only registry setup helpers should remain.

---

## Ship gate + manual checks

Update `docs/manual-checks/2026-06-17-baseball-identity-ship-gate.md`:

- Helpers: `./bin/baseball-query` with new keys (commit script if still untracked).
- Check 4: `{player, team}` not `{name, team}`; Milwaukee Braves should resolve.
- Check 5 team grain: `{team: "Brooklyn Dodgers"}` (or equivalent).

**Paul must re-bootstrap** after this slice (`--root /tmp/mycelium-baseball-benchmark --yes --no-default`).

---

## Verification

```bash
./bin/ci-local
```

Do not edit `TODO.md`.

---

## Deliverables

- `prompts/cursor/done/2026-06-18-1100-strict-grain-routing/`
  - `prompt.md`, `output.md` with **For Grok + Paul**
- Do not commit.

**Suggested commit message:** `refactor(routing): strict lookup-key grain inference; remove fan-out and EntityQuery.grain`