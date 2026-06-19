# M2a output — warehouse capability manifest

## Done

- **`examples/networks/baseball/warehouse_domains.json`** — pack domain map (batting, bio, pitching, team_season) with specialist, tables, grain, and batting `career_sum` convention.
- **`src/network/warehouse_manifest.py`** — generator: merges pack domains with sqlite introspection (`PRAGMA table_info` + `COUNT(*)` per domain table only).
- **Hooks:** `LahmanSeedHandler` after warehouse ingest; `install_pack_ontology_from_example` on sync-only / ontology install when warehouse exists (idempotent rewrite).
- **`build_network_capabilities()`** — adds `warehouse_manifest` summary (`present`, `path`, `dataset_id`, `domains`, `tables`) when `warehouse_manifest.json` exists.
- **`tests/test_warehouse_manifest.py`** — 6 tests (domains config, introspection, refresh write, idempotent rewrite, capabilities summary, merge unit).
- **`examples/networks/baseball/README.md`** — short operator note (auto-generated, not hand-edited).

## Verification

```text
./bin/ci-local                    # 565 smoke passed
uv run pytest tests/test_warehouse_manifest.py -q   # 6 passed
```

## Table cap policy

Introspection is limited to tables listed in `warehouse_domains.json` domain `tables` arrays (union across domains). Full Lahman refresh only touches Batting, People, Pitching, Teams — not all 30+ Lahman tables. Missing CSV/tables are omitted from `tables` block.

## Next

Queue **M2b** — generic warehouse stat resolver (depends on manifest).

## Suggested commit message

```
baseball: warehouse capability manifest + describe_network surfacing (M2a)
```
