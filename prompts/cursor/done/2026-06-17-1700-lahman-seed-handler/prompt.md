# LahmanSeedHandler — baseball pack bootstrap (v1 identity + warehouse)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting).

**Context:** Paul + Grok agreed June 2026. Framework slices **1400** (multi-MVR entity stores) and **1500** (manifest fail-fast) are committed. Baseball `network.json` already declares **player** + **team** grains. **This slice** ships the **network-pack** bootstrap handler that ingests Lahman CSV seed, loads a v0 warehouse, and commits **team** and **player** entity grains. **Query orchestrator grain selection** is a **follow-on slice**.

**Parent design:** [`docs/plans/baseball-example-program.md`](../../../docs/plans/baseball-example-program.md)

**Regression anchor:** CRM examples and capstones unchanged (433 smoke baseline after 1500).

---

## Locked decisions (Paul, June 2026)

| # | Decision |
|---|----------|
| L1 | **Pack handler only** — code under `examples/networks/baseball/bootstrap_handlers/`; loaded via `network.json` `bootstrap.module` + `handler` (same pattern as CRM framework handler). |
| L2 | **Seed location** — `<network_root>/seed/` only (zip `lahman_1871-2025_csv.zip`, extracted `lahman_1871-2025_csv/`, or flat `*.csv`). **Do not** commit Lahman zip or CSVs to git. |
| L3 | **Warehouse** — `<network_root>/warehouse/lahman.sqlite`; v1 loads **at minimum** `People`, `Teams`, `Appearances` (UTF-8-sig CSV → TEXT columns). May also load `Batting`, `Pitching`, `TeamsFranchises` for forward compatibility. |
| L4 | **Team grain (v0)** — distinct non-empty `Teams.name` labels (trimmed) → `entities/team.json` via `ensure_entity_bind_fields` on **team** registry (`bind_fields: ["name"]`). Uses Lahman season row labels as v0 fan-facing names (canonical-names specialist deferred). |
| L5 | **Player display name (v0)** — `trim(nameFirst) + " " + trim(nameLast)` from `People`. |
| L6 | **One uuid per Lahman `playerID`** — `playerID` is **bootstrap dedup key only** (stored in entity provenance/metadata if needed; **not** public `id`, not MVR). |
| L7 | **Multi-team aliases → same player uuid** — each distinct `(player_display_name, team_label)` from `Appearances`×`People`×`Teams` must resolve to the **same** entity id for a given `playerID`. First pair creates the row; later pairs add **additional `bind_index` keys** (and field-index entries) without creating duplicate entities. |
| L8 | **No seed → 0 entities** — handler returns `BootstrapResult(entities_committed=0, handler_id="lahman_seed")` (same contract as CRM missing seed). |
| L9 | **Framework fixes required for multi-grain bootstrap** — (a) `category_mvr_bootstrap` merges **all** manifest MVR bind fields across grains (includes baseball `team`); (b) `write_bind_fields` uses **`reg._mvr`**, not bare `load_mvr()`, when `registry=` is passed. |
| L10 | **CRM `team` category mapping (v0)** — map bind field `team` → `professional` category in `CRM_MVR_FIELD_CATEGORY` merge reference (baseball example copies CRM sample categories until baseball ontology exists). Document in baseball README. |

---

## `network.json` (committed example — update bootstrap block only)

```json
"bootstrap": {
  "module": "bootstrap_handlers.lahman_seed",
  "handler": "LahmanSeedHandler"
}
```

Keep existing `mvr`, `metering`, `experiment` blocks.

---

## Pack layout

```
examples/networks/baseball/bootstrap_handlers/
  lahman_common.py    # seed resolution, CSV ingest, SQL extracts
  lahman_seed.py      # class LahmanSeedHandler
```

At runtime after refresh: `<network_root>/bootstrap_handlers/` (copied by `copy_example_network` — already skips only generated runtime dirs).

**Import convention:** pack modules use `from bootstrap_handlers.lahman_common import ...` (network root on `sys.path` — existing pack loader).

---

## Handler behavior (`LahmanSeedHandler.run`)

1. `resolve_network_seed(paths.root)` — return `None` if no usable seed → L8.
2. `resolve_lahman_csv_dir(seed)` — zip extract idempotent to `seed/lahman_1871-2025_csv/` if needed.
3. `ingest_warehouse(csv_dir, warehouse_path)` — rebuild sqlite (drop/recreate tables on bootstrap).
4. **Teams:** for each distinct `Teams.name` label → `ensure_entity_bind_fields({"name": label}, registry=team_registry, ...)`.
5. **Players:** iterate distinct `(playerID, player_display_name, team_label)` from Appearances join:
   - Maintain in-memory `playerID → entity_id` for bootstrap pass.
   - First sight of `playerID`: `ensure_entity_bind_fields({"name": ..., "team": ...}, registry=player_registry, ...)`; record mapping.
   - Later pairs for same `playerID`: **do not** call `ensure_entity_bind_fields` (would duplicate). Use `assign_bind_index` + field-index rebuild on existing entity, then `save_entity`. Optionally store `playerID` in entity metadata field if you add a non-MVR internal field pattern — **not required** if in-memory map suffices for bootstrap pass.
6. Return `BootstrapResult` with `handler_id="lahman_seed"`, `entities_by_grain={"team": n, "player": m}`, `entities_committed` = sum, `sources_processed` includes seed path + `warehouse/lahman.sqlite` when ingested.

---

## Read first

- `prompts/cursor/WORKFLOW.md`
- `docs/plans/baseball-example-program.md` — grains, uuid4, multi-team player bind
- `src/network/bootstrap/handlers/default_seed.py` — handler contract
- `src/network/bootstrap/handlers/resolve.py` — pack load
- `src/agents/entity_registry.py` — `assign_bind_index`, per-grain registries
- `src/agents/attribute_write.py` — `ensure_entity_bind_fields`, `write_bind_fields`
- `src/network/category_mvr_bootstrap.py`
- `examples/networks/baseball/network.json`, `guide.md`, `README.md`
- `tests/test_multi_mvr_entity_stores.py` — `test_baseball_bootstrap_commits_zero_rows`
- `tests/test_network_bootstrap.py` — pack handler stub pattern

---

## Implement

### 1 — `lahman_common.py`

- `resolve_network_seed(network_root: Path) -> Path | None`
- `resolve_lahman_csv_dir(seed: Path) -> Path | None`
- `ingest_warehouse(csv_dir, warehouse_path) -> dict[str, int]` (table → row count)
- `distinct_team_labels(warehouse_path) -> list[str]`
- `distinct_player_team_rows(warehouse_path) -> list[tuple[str, str, str]]` — `(playerID, display_name, team_label)` ordered stable

Use `utf-8-sig` for CSV reads.

### 2 — `lahman_seed.py`

- `class LahmanSeedHandler` with `run(self, ctx) -> BootstrapResult`

### 3 — Framework (L9, L10)

- **`category_mvr_bootstrap.py`:** `_required_bind_fields(paths)` from `load_mvr_config()` all grains; merge any missing bind fields into `categories.json` (add `team` → `professional` in `CRM_MVR_FIELD_CATEGORY`).
- **`attribute_write.py`:** `write_bind_fields` → `mvr = reg._mvr` (not `load_mvr()`).

If bootstrap needs a small **framework** helper for alias attachment (e.g. `add_bind_alias(entity_id, bind_values, *, registry)`), add to `entity_registry.py` with tests — keep minimal.

### 4 — Example manifest + README

- Update `examples/networks/baseball/network.json` bootstrap block (L1).
- Update `examples/networks/baseball/README.md` — seed layout, handler, warehouse path, grains populated; note `bootstrap_experiment.py` remains legacy spike (disposition unchanged).

### 5 — Tests

**New `tests/test_lahman_seed_handler.py`:**

| Test | Assert |
|------|--------|
| No seed | `handler_id == "lahman_seed"`, 0 entities |
| Minimal fixture | Copy baseball manifest + `bootstrap_handlers/`; write tiny CSVs under `seed/` (3 team names, 1 player, 1 appearance) → 3 team + 1 player commits |
| **Multi-team same player** | Fixture: same `playerID` in two `Appearances` rows (two `Teams.name`) → **1** player entity, **2** `bind_index` keys, lookups on both `(name, team)` pairs return same `id` |

**Update `test_baseball_bootstrap_commits_zero_rows`:** copy `bootstrap_handlers/` with manifest; expect `lahman_seed` handler_id when no seed.

**CRM capstones** must stay green.

Use inline tiny CSV fixtures — **no** 40MB zip in repo.

### 6 — Docs

Short update to `docs/plans/baseball-example-program.md` checklist #2 / #5 — note v1 scripted `LahmanSeedHandler` ships (one paragraph max). **Do not edit `TODO.md`.**

---

## Explicit non-goals

- Query graph / `target_resolve` / supervisor grain selection
- Full 27-table Lahman warehouse
- LLM canonical team names / alias expansion
- `bootstrap_experiment.py` removal or rewrite
- Multi-grain query-time alias expansion beyond bootstrap index keys
- Committing Lahman data files
- Franchise specialist / `franchID` organization

---

## Exit criteria

| # | Criterion |
|---|-----------|
| E1 | `LahmanSeedHandler` in pack; baseball manifest points at it |
| E2 | Seed → warehouse sqlite + team/player grain files |
| E3 | Multi-team same `playerID` → one uuid, multiple bind keys (test proves) |
| E4 | No seed → 0 entities, `lahman_seed` handler_id |
| E5 | `write_bind_fields` uses registry grain MVR; category merge includes `team` |
| E6 | CRM capstones / 1500 manifest strictness unchanged |
| E7 | `./bin/ci-local` green |

---

## Completion (Cursor)

Per `prompts/cursor/WORKFLOW.md`: claim from `next/` first, `./bin/ci-local`, `done/` folder with `output.md`, no commit/push.

**Suggested commit message:**

```
feat(baseball): LahmanSeedHandler pack bootstrap

Ingest Lahman CSV seed into warehouse/lahman.sqlite; commit team and
player entity grains with playerID dedup and multi-team bind aliases.
Extend category MVR merge and write_bind_fields grain policy.
```

---

## For Grok + Paul

- Improvised Cursor work (option A) is in git stash: `cursor-improvised lahman seed handler (option A — compare later)` — compare diff after review.
- **Next slice after approval:** query orchestrator grain selection (`target_resolve`, supervisor).