# M2 polish output — warehouse manifest + resolver + bind nits

## Done

### M2a (A1–A3)
- Dropped duplicate `full_manifest_path` from `warehouse_manifest_capabilities()` (kept `path`).
- Hoisted `maybe_write_warehouse_manifest` to module top in `lahman_seed.py` and `pack_ontology.py`.
- `format_mcp_instructions()` mentions warehouse manifest path + describe_network JSON when present.

### M2b (B1–B4)
- **`specialist_loader.py`** — shared `load_sibling` / `load_warehouse_resolve`; batting/bio use it.
- **`bats` deliver test** — extended `People.csv` fixture; asserts `L`.
- **Full `parameters`** — `attribute` + batting `column` on warehouse provenance writes.
- **Hand-test doc** updated for M2b/M2c status (`bats`, `career_rbi`, `career_hits`, bind provenance).

### M2c (C1–C3)
- **`tests/test_baseball_multi_attr_deliver.py`** — `debut_team` + `career_hr` + `birth_date` provenance.
- **Player bind** asserted in identity provenance test (`player`, `debut_team`, `debut_year`).
- Hand-test note: clear `agents/player_identity/storage.json` if stale `research` provenance.

### Smoke
- `multi_attr_bind_and_warehouse_provenance` scenario (11 scenarios total).

## Verification

```text
./bin/ci-local                    # 572 smoke passed
uv run pytest tests/test_warehouse_manifest.py tests/test_baseball_*.py tests/test_mcp_onboarding.py -q
./bin/smoke-baseball-e2e          # 11 scenarios
```

## Suggested commit message

```
polish(baseball): M2 warehouse manifest and resolver nits
```
