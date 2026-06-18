# Review — 2026-06-18-1800-baseball-mvr-record-types-debut-bind

**Verdict: Approved + polish nits**

## CI

| Step | Result |
|------|--------|
| `./bin/ci-local` | **506** smoke passed; ruff clean; admin-ui build ok |
| `./bin/smoke-baseball-e2e` | **6/6** (with `MYCELIUM_NETWORK_ROOT` unset — see P1) |
| `./bin/smoke-crm-e2e` | **7/7** (same) |

## Delivery

`output.md` matches the working tree: framework rename, baseball manifests, Lahman bootstrap rewrite, routing tests, smoke scripts, router doc rename. Implementation is present — not tests-only.

## Diff reviewed

Read or spot-checked:

- `src/network/mvr.py` — `RecordTypePolicy`, `new_records` required, legacy key rejection
- `src/agents/target_resolve.py` — `bootstrap_only` partial 0-hit → `_resolve_bootstrap_only_zero_hit`
- `examples/networks/baseball/bootstrap_handlers/lahman_common.py` — `distinct_player_debut_rows`
- `examples/networks/baseball/bootstrap_handlers/lahman_seed.py` — one row per `playerID`
- `examples/networks/*/network.json` — all four examples
- `tests/test_strict_record_type_routing.py`, `tests/test_multi_record_type_entity_stores.py`, `tests/test_lahman_seed_handler.py`
- `docs/query-record-type-router.md`, `examples/networks/baseball/guide.md`
- `bin/smoke-baseball-e2e`, `bin/smoke-crm-e2e`

No `/review` subagent (large but coherent slice; full grep + CI + e2e sufficient).

## Spec compliance

| Criterion | Result |
|-----------|--------|
| E1 `mvr.record_types` + `default_record_type` | **Pass** |
| E2 Required `new_records` (`bootstrap_only` \| `query_allowed`) | **Pass** |
| E3 Legacy keys rejected (`grains`, `default_grain`, `identity_mode`, `seed_grain`) | **Pass** (code); **Pass** tests for MVR; **Gap** — no test for `seed_grain` (P3) |
| E4 `grain` → `record_type` in `src/` | **Pass** (only legacy error strings remain) |
| E5 Baseball bind `player` + `debut_team` + `debut_year` | **Pass** |
| E6 Lahman one bind per `playerID`, no appearance alias loop | **Pass** (`test_lahman_seed_handler_multi_team_same_player_id`) |
| E7 Partial `{player}` 0-hit `bootstrap_only` → `not_found` | **Pass** |
| E8 CRM `query_allowed` unchanged | **Pass** (smoke + routing tests) |
| E9 Active docs vocabulary sweep | **Partial** — router doc + seed-bootstrap + guide good; many stragglers (P2) |
| E10 `./bin/ci-local` green | **Pass** |

## Design critique

**Strong**

- `new_records` names the real axis (who may mint rows) and survives annual Lahman refresh without “closed world” confusion.
- `record_type` is clearer than `grain` in manifests; `src/` rename is thorough.
- Partial 0-hit fix is correctly gated on `bootstrap_only`, not baseball-specific strings.
- Lahman SQL for debut bind matches the locked semantics; multi-team appearance fixture proves one `bind_index` entry per player.
- Fail-fast on legacy manifest keys avoids silent half-migration.

**Acceptable tradeoffs**

- `lahman_seed` skips rows when `source_keys` already exist — re-bootstrap after this slice requires wiping `entities/player.json` (or full refresh root), not incremental bind migration. Documented in `output.md`.
- `bin/smoke-baseball-e2e` uses `setdefault` for `MYCELIUM_NETWORK_ROOT` — a pre-existing env pointing at an old manifest breaks the script (P1).

## Naming stragglers (active docs / ops)

Grep after slice — **not** in `src/` or `tests/` (except legacy-rejection tests):

| Location | Issue |
|----------|-------|
| `README.md` | `per-grain`, `entities/<grain>.json`, `default_grain` |
| `docs/onboarding.md` | `mvr.grains`, `default_grain`, `seed_grain`, `entities/<grain>.json` |
| `docs/database-notes.md` | `entities/<default_grain>.json` |
| `docs/architecture.md` | Multiple `per-grain` / `active-grain`; line 347 still says baseball `name`+`team` |
| `docs/plans/baseball-example-program.md` | Locked table still `player`+`team`, bind_index story, “grain” throughout |
| `docs/manual-checks/2026-06-17-baseball-identity-ship-gate.md` | `query-grain-router.md`, `get_entity_registry(grain=…)`, `delivery.grain` |
| `docs/manual-checks/2026-06-18-baseball-query-hand-test-plan.md` | Header updated; body still `delivery.grain`, `{player, team}` queries, “Player grain” sections |
| `docs/seed-bootstrap.md` | “bootstrap grain”, “multi-grain” in § JSON→MVR / Related APIs |
| `prompts/cursor/HOLD.md` | Stale routing lock (`{player, team}`), dead link to `query-grain-router.md` |
| `TODO.md` | `mvr.grains` in MCP health_check item (Grok+Paul) |

**Untracked artifact:** `examples/networks/baseball/checkpoints.sqlite` — do **not** commit; delete or gitignore.

**Live roots:** `~/mycelium-networks/*` and `/tmp/mycelium-baseball-benchmark` need manifest + entity store refresh before hand tests.

## Nits (non-blocking)

| ID | Severity | Item |
|----|----------|------|
| P1 | LOW | `smoke-baseball-e2e` / `smoke-crm-e2e`: document or `unset` inherited `MYCELIUM_NETWORK_ROOT` when it carries legacy `network.json` |
| P2 | LOW | Doc vocabulary sweep — table above (follow-on polish slice or Grok pass) |
| P3 | LOW | Add `test_legacy_seed_grain_rejected` mirroring MVR legacy tests |
| P4 | LOW | Hand test plan body: bulk-replace Q01–Q16 to `debut_team`/`debut_year`; `delivery.record_type` |
| P5 | LOW | `baseball-example-program.md` locked decisions § — align with slice 1800 design |
| P6 | LOW | `seed-bootstrap.md` bind-alias bullet still describes appearance-driven player aliases — update for debut bind |

## For Paul

- **Commit locally** (Grok): `feat(mvr): record_type + new_records; baseball player debut bind`
- **Re-bootstrap required** before hand gate on full Lahman root (wipe old `player`+`team` entities).
- Update live network manifests under `~/mycelium-networks/` or imports will fail on `legacy mvr.grains`.
- **Do not push** until you are ready for the breaking manifest change on `origin`.
- **Next:** doc polish slice (P2) or update `HOLD.md` + `baseball-example-program.md` when convenient.