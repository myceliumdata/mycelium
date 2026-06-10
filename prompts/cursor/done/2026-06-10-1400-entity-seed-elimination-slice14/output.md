# Slice 14 — Seed elimination: bootstrap import

## Summary

`seed.json` is now imported into `entities.json` **only at bootstrap** (`refresh-example-network`, `network create`). Query time still reads seed via `agents.seed` — unchanged until Slices 15–17.

## Changes

| File | Change |
|------|--------|
| `src/network/seed_import.py` | New — `import_seed_file(seed_path)` → `ensure_bound_entity` per row; missing file returns `0`; `ValueError` on bad JSON |
| `src/network/example.py` | After copy, when `live_root/seed.json` exists: `apply_network_paths`, `reset_entity_registry`, `import_seed_file` |
| `src/network/create.py` | After `shutil.copy2` seed: same bootstrap import |
| `tests/test_example_network.py` | CRM refresh → 15 entities; idempotency; missing path → `0` |
| `tests/test_network_create.py` | Happy-path create writes `entities.json` with imported seed row |

## Tests

**23 passed** — smoke on `test_example_network.py` + `test_network_create.py`

```bash
uv run ruff check src/network/seed_import.py src/network/example.py src/network/create.py
uv run pytest tests/test_example_network.py tests/test_network_create.py -m smoke -q
```

## For Grok + Paul

- Mark **Slice 14** done in `TODO.md` under seed-elimination track
- Update `docs/plans/entity-seed-elimination-phase.md` Slice 14 → shipped
- **Slice 15** next: registry-only resolution (remove seed branch from `resolve_entity`)
- Runtime seed (`agents.seed`, `refresh_runtime_from_disk` seed reload) intentionally untouched — out of scope
- Review folder: `prompts/cursor/done/2026-06-10-1400-entity-seed-elimination-slice14/`
- Suggested commit message (after review):

```
Bootstrap seed import into entities.json (Slice 14).

import_seed_file at refresh-example-network and network create;
smoke tests for CRM import and idempotency.
```

- **Did not edit `TODO.md`** (per governance)
