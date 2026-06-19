# Baseball M2 polish (M2a + M2b + M2c nits)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md`. **After M2c** (M2c now landed — polish is next optional slice).

**Priority:** Non-blocking nits from Grok reviews:
- M2a — [`review.md`](../done/2026-06-19-1400-baseball-warehouse-manifest-m2a/review.md)
- M2b — [`review.md`](../done/2026-06-19-1500-baseball-generic-warehouse-resolver-m2b/review.md)
- M2c — [`review.md`](../done/2026-06-19-1600-baseball-identity-bind-provenance-m2c/review.md)

**Do not edit `TODO.md`.**

---

## Objective

Small cleanup on warehouse manifest surfacing and pack resolver — no new stats or conventions.

---

## M2a nits

| # | Fix |
|---|-----|
| A1 | `warehouse_manifest_capabilities()` — remove duplicate field: keep `path`, drop `full_manifest_path`. Update tests. |
| A2 | Hoist `maybe_write_warehouse_manifest` import to module top in `lahman_seed.py` and `pack_ontology.py` if no import cycle; else one-line comment why lazy. |
| A3 | `format_mcp_instructions()` — one sentence when `warehouse_manifest` present: full manifest on disk; grains/aliases in describe_network JSON. |

---

## M2b nits

| # | Fix |
|---|-----|
| B1 | Deduplicate `_load_warehouse_resolve()` — move to `warehouse_resolve.py` (e.g. `load_module()`) or tiny pack `specialist_loader.py`; both specialists call it. |
| B2 | Add minimal-fixture test for bio raw-column alias (`bats` or `debut`) — extend `People.csv` with column + value; assert deliver `found`. |
| B3 | Provenance `parameters` — add `attribute` and batting `column` when resolved (full-parameters policy). |
| B4 | Update [`docs/manual-checks/2026-06-19-baseball-specialist-hand-test.md`](../../docs/manual-checks/2026-06-19-baseball-specialist-hand-test.md): `bats`/`debut`/`birth_city` ✅ after M2b when column present; adjust “Should NOT work” table. |

---

## M2c nits

| # | Fix |
|---|-----|
| C1 | Add multi-attr integration test or smoke row: `requested_attributes: ["debut_team", "career_hr", "birth_date"]` + `provenance: true` — bind registry actor, warehouse `parameters.warehouse`. |
| C2 | Assert `player` bind in `test_baseball_player_identity_specialist.py` alongside debut fields. |
| C3 | Hand-test doc note: if bind provenance still shows `research`, clear `agents/player_identity/storage.json` and re-deliver. |

---

## Verification

```bash
./bin/ci-local
uv run pytest tests/test_warehouse_manifest.py tests/test_baseball_batting_specialist.py tests/test_baseball_bio_specialist.py tests/test_baseball_player_identity_specialist.py -q
./bin/smoke-baseball-e2e
```

---

## For Grok + Paul (output.md)

- M2 polish done.

**Suggested commit message:**

```
polish(baseball): M2 warehouse manifest and resolver nits
```