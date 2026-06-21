# Network create v2 — optional `--seed`

**Status:** Shipped (June 2026)  
**Trigger:** Paul + Grok agreed post seed-elimination: breaking-change window; empty networks are first-class.

## Goal

`mycelium network create` must work **without** `--seed`, matching the `crm-empty` example pattern. When `--seed` is supplied, behavior stays as today (copy + bootstrap import into `entities.json`).

`bin/refresh-example-network` already copies `seed.json` when the committed example includes one and imports at refresh time. This slice **formalizes** that as the shared bootstrap path and makes operator output explicit.

## Current vs target

| Surface | Today (v1) | Target (v2) |
|---------|------------|-------------|
| `network create --seed` | **Required** | **Optional** |
| `network create` (no seed) | Not supported | Ontology + manifest + guide; **no** `seed.json`, **no** `entities.json` until first bind |
| `network create --seed FILE` | Copy + `import_seed_file` | Unchanged |
| `refresh-example-network crm-seeded` | Copy `seed.json` + import | Same; report bootstrap in script output |
| `refresh-example-network crm-empty` | No seed, no import | Same |

## Shared bootstrap contract

Extract or reuse one code path for “seed file at `<root>/seed.json` → import into `entities.json`”:

1. `apply_network_paths`
2. `reset_entity_registry`
3. `import_seed_file(paths.seed_path)` (returns row count; `0` if file missing)

**`network create` with `--seed`:** validate external file → `shutil.copy2` to `<root>/seed.json` → shared bootstrap.

**`network create` without `--seed`:** skip copy and bootstrap. On `--force` overwrite of an existing root, **clear** stale `seed.json` and `entities.json` so the network matches empty-seed semantics.

**`refresh_example_network`:** after copy, if `<live_root>/seed.json` exists (because the example shipped it), run shared bootstrap. No CLI `--seed` flag on refresh — detection is automatic from copied files.

## Breaking / behavior notes

- CLI help and README should show `--seed` as optional.
- `create_network()` signature: `seed_path` becomes `str | Path | None = None`; reorder kwargs if needed for clarity (prefer `seed_path=` keyword at call sites).
- `CreateNetworkResult`: add `entities_bootstrapped: int` (0 when no seed).
- Dry-run: validate `--seed` when provided; skip seed validation when omitted.

## Out of scope

- Renaming `SeedRecord` / `seed_records` (separate slice: identity vocabulary rename).
- Renaming `seed.json` filename or `import_seed_file`.
- Non-person seed schemas.
- `export-growth-seed` tooling.

## Verify

```bash
uv run ruff check src tests
LANGCHAIN_TRACING_V2=false uv run pytest -q tests/test_network_create.py tests/test_example_network.py
rg 'required=True.*--seed|--seed.*required=True' src/
```

Manual:

```bash
# Empty create (no seed)
uv run mycelium network create test_empty --root /tmp/test_empty --prompt "CRM for demos" --dry-run

# Refresh still bootstraps crm
./bin/refresh-example-network crm-seeded --root /tmp/crm-test --no-register --yes
# expect: seed.json copied + entities imported + stdout mentions seed bootstrap
```

## Files (expected touch)

- `src/network/create.py`, `src/main.py`
- `src/network/seed_import.py` and/or `src/network/example.py` (shared bootstrap helper)
- `bin/refresh-example-network` (stdout when seed bootstrapped)
- `tests/test_network_create.py`, `tests/test_example_network.py`
- `README.md` (network create examples — optional `--seed`)