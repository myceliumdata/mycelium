# Registry `source_keys` + field alias index — Lahman handler cleanup

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting).

**Priority:** First of two baseball identity slices. **Slice 2** (`2026-06-17-2000-baseball-closed-identity-lazy-aliases`) depends on the alias-index API from this slice.

**Parent:** Paul + Grok June 2026 — `lahman.playerID` / `teamID` / `franchID` as source metadata; bootstrap-once (no cross-refresh merge); drop in-memory `player_ids` map; shared ambiguous team aliases (`Dodgers` → multiple entities) via **field index**, not `bind_index`.

**Principles:**

- **Public `id` stays uuid4** — `source_keys` are provenance/joins only; not in default `results[]`.
- **Framework generic** — no `lahman` imports in `src/`; baseball handler writes namespaced keys.
- **Bootstrap-once** — no merge-by-`source_keys` across refresh; `reset_entity_registry()` before handler remains OK.
- **Two alias mechanisms** — do not conflate them (see K4 below).

---

## Problem (posterity)

v1 `LahmanSeedHandler` dedups players with an in-memory `player_ids: dict[str, str]` map. `playerID` is not persisted. Team/player warehouse joins cannot resolve `entity_id` after bootstrap.

Separately, fan-team nicknames like `"Dodgers"` must map to **multiple** team entities. `bind_index` is 1:1 (one key → one `entity_id`); `add_bind_alias` overwrites on collision. **Field indexes** already support many `entity_id`s per normalized value, but aliases are not indexed today (`add_bind_alias` skips field-index rebuild).

---

## Locked scope

| # | Decision |
|---|----------|
| K1 | **`RegistryEntity.source_keys`** — `dict[str, str]` (e.g. `{"lahman.playerID": "aaronha01"}`). Namespaced keys; values are source-system identifiers. Not MVR; not returned in default match dicts unless tests explicitly assert storage. |
| K2 | **Reverse index + lookup** — per-grain `source_key_index` persisted in the entities document (or rebuilt on load). API: `EntityRegistry.lookup_by_source_key(key: str, value: str) -> RegistryEntity | None`. Optional: `set_source_keys(entity_id, keys)` helper. |
| K3 | **Lahman handler** — remove `player_ids` in-memory map. First sight of `playerID`: `lookup_by_source_key("lahman.playerID", …)`; on miss create entity and write `source_keys`. Multi-team rows: same lookup → `add_bind_alias` for additional `(name, team)` pairs (unchanged L7 behavior). |
| K4 | **Field aliases vs bind aliases** — **Bind alias** (`add_bind_alias`): alternate **full** MVR `bind_values` → `bind_index` only (player multi-team). **Field alias** (new `add_field_alias`): extra normalized value(s) for one bind field → **field index only**; **duplicate normalized values across different entities allowed** (team `"Dodgers"` on Brooklyn + LA). Do **not** write shared ambiguous nicknames into `bind_index`. |
| K5 | **`build_field_indexes`** — include each entity's `field_aliases` (new `dict[str, list[str]]` on `RegistryEntity`, default `{}`) in per-field inverted indexes alongside canonical `bind_values`. |
| K6 | **Lahman team `source_keys`** — when committing a team row, set at least `lahman.teamID` (pick stable representative per distinct `Teams.name` from warehouse SQL). When `franchID` is available for that row, also set `lahman.franchID`. Document if one name maps many `teamID`s (v0: one representative ID is OK). |
| K7 | **Lahman player `source_keys`** — set `lahman.playerID` on create. |
| K8 | **Tests** — unit tests for `lookup_by_source_key`, `add_field_alias` multi-entity lookup; update `test_lahman_seed_handler_multi_team_same_player_id`; new test: two team entities + shared field alias `"Dodgers"` → `lookup_by_target_lookup({"name": "Dodgers"})` returns 2 ids on **team** registry. |
| K9 | **Docs** — short addition to `docs/seed-bootstrap.md` or `examples/networks/baseball/README.md`: `source_keys`, field vs bind alias. Update `docs/plans/baseball-example-program.md` identity layer bullet (one paragraph). |

---

## Read first

- `prompts/cursor/WORKFLOW.md`
- `src/agents/entity_registry.py` — `add_bind_alias`, `build_field_indexes` / `field_index.py`
- `src/storage/entity_store.py` — entities document persistence
- `examples/networks/baseball/bootstrap_handlers/lahman_seed.py`, `lahman_common.py`
- `tests/test_lahman_seed_handler.py`, `tests/test_entity_store_evolution.py`
- `prompts/cursor/done/2026-06-17-1700-lahman-seed-handler/prompt.md` — L6/L7
- `docs/plans/conversations/2026-06-15-baseball-example-design.md` — identity layers

---

## Implement

### Framework (`src/`)

- Extend `RegistryEntity` with `source_keys` and `field_aliases`.
- Extend `EntitiesDocument` with `source_key_index` (define serialization; rebuild on load if preferred — document choice in `output.md`).
- `EntityRegistry.lookup_by_source_key`, `set_source_keys` (or equivalent), `add_field_alias(entity_id, field, alias_value)`.
- Update `build_field_indexes` to merge `field_aliases`.
- Ensure `add_bind_alias` behavior unchanged for player multi-team full binds.

### Baseball pack

- `lahman_seed.py`: drop `player_ids` dict; use K3/K6/K7.
- `lahman_common.py`: helper for team name → representative `teamID` / `franchID` if needed.

### Tests

- Framework unit tests (registry round-trip, source key lookup, field alias multi-match).
- Lahman integration tests still green; multi-team player test still passes without in-memory map.
- `./bin/ci-local` green.

---

## Scope boundaries (strict)

**May modify:**

- `src/agents/entity_registry.py`, `src/agents/field_index.py`, `src/storage/entity_store.py` (if needed)
- `examples/networks/baseball/bootstrap_handlers/`
- `tests/`
- `docs/seed-bootstrap.md`, `examples/networks/baseball/README.md`, `docs/plans/baseball-example-program.md` (short)

**Do not modify:**

- `target_resolve` / query graph (slice 2)
- Lazy LLM alias expansion (slice 2)
- `create_pending` gating (slice 2)
- Query grain selection (slice 3)
- Bootstrap batch LLM for aliases
- Cross-refresh merge / skip `reset_entity_registry`
- `TODO.md`

---

## Explicit non-goals

- Populating team nicknames at bootstrap (lazy slice 2)
- `source_keys` in MCP `results[]` or public API
- Franchise specialist / derivative entities
- Changing team canonical-name enrichment (still v0 `Teams.name` labels)

---

## Exit criteria

| # | Criterion |
|---|-----------|
| E1 | No `player_ids` in-memory map in `lahman_seed.py` |
| E2 | `lookup_by_source_key("lahman.playerID", …)` works after bootstrap |
| E3 | `add_field_alias` allows two team entities sharing field alias; lookup returns both |
| E4 | Player multi-team same `playerID` test still passes |
| E5 | `./bin/ci-local` green |
| E6 | `output.md` documents disk shape for `source_keys` / `field_aliases` / index |

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- **For Grok + Paul** in `output.md`: note any EntityStore migration concerns.

## When finished

Per `prompts/cursor/WORKFLOW.md` — no commit/push.

**Suggested commit message:**

```
feat(registry): source_keys and field alias index

Persist Lahman source IDs on RegistryEntity; field aliases for
multi-entity nickname lookup; Lahman handler drops in-memory playerID map.
```