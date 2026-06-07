# Networks Phase 4 — output

## Summary

Moved CRM seed out of the default framework clone into committed **`examples/networks/crm/`** (15-person public-safe subset). Fresh clones have an empty legacy `data/` shim; users bootstrap via **`bin/copy-example-network`**, register, and query.

## Added

| Path | Purpose |
|------|---------|
| `examples/networks/crm/seed.json` | Demo people (Nichanan, Andrea, 2× Kevin Zhang, …) |
| `examples/networks/crm/network.json` | `name: crm`, display metadata |
| `examples/networks/crm/README.md` | Copy/register instructions |
| `examples/networks/crm/prepare_seed.py` | Maintainer transform script |
| `bin/copy-example-network` | Copy example → `network_root`; optional `--register --default` |
| `data/README.md` | Explains legacy shim + bootstrap |
| `tests/test_example_network.py` | 5 smoke tests |

## Removed from `data/`

- `seed.json`, `seed_crm.json`, `raw_data.json`, `seed_crm.json.bak`, `prepare_seed.py`

Full prototype CRM data: `git show prototype:data/seed.json`

## Docs / config updates

- `README.md` — quick start: copy-example → register → query
- `docs/architecture.md` — seed at `<network_root>/seed.json` + example path
- `docs/database-notes.md` — network-relative paths
- `.env.example` — deprecated per-path `MYCELIUM_SEED_PATH` in favor of network selection

## Verification

```bash
uv run pytest -m smoke -q   # 79 passed
uv run ruff check src tests bin/   # clean
```

## Manual fresh-clone flow

```bash
./bin/copy-example-network crm --root ~/mycelium-networks/crm --register --default
uv run mycelium query --person-key "Nichanan Kesonpat"
uv run mycelium query --network-dir examples/networks/crm --person-key "Andrea Kalmans"
```

## Next queue item

`prompts/cursor/next/2026-06-07-1400-networks-integration-testing.md`
