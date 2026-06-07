# Networks categories sample + alignment — output

## Checklist

### A. `categories.json` policy (runtime only)

| # | Item | Status |
|---|------|--------|
| 1 | Remove runtime artifacts from `examples/networks/crm/` (seed + network.json only) | **PASS** |
| 2 | Add `docs/examples/sample-categories.json` | **PASS** |
| 3 | Add `docs/examples/README.md` | **PASS** |
| 4 | Update CRM/data/README/architecture docs — link sample; no committed categories | **PASS** |
| 5 | `copy-example-network` skips `categories.json` | **PASS** |
| 6 | `.gitignore` consolidated (`examples/networks/**/…`; sample not ignored) | **PASS** |
| 7 | Tests: layout/copy assert no categories; sample JSON smoke test | **PASS** |

### B. Polish-review nits

| # | Item | Status |
|---|------|--------|
| 8 | `mycelium seed` — `--network-dir` and `--network` flags | **PASS** |
| 9 | `--seed-path` help text updated | **PASS** |
| 10 | `networks-terminology.md` status line (Phases 1–4 delivered) | **PASS** |
| 11 | README Status — polish + ready for integration testing | **PASS** |

**Hygiene:** Session autouse fixture in `tests/conftest.py` cleans example dir before/after smoke runs.

## Key files

- `docs/examples/sample-categories.json` — six categories + `attribute_map` (fixed `last_updated`)
- `docs/examples/README.md`
- `tests/test_categories_sample.py` — 2 smoke tests
- `tests/conftest.py` — `clean_example_crm_runtime_artifacts()`
- `src/main.py` — seed network flags
- `.gitignore` — single `examples/networks/**/` runtime block

## Verification

```bash
uv run pytest -m smoke -q   # 87 passed
uv run ruff check src tests bin/   # clean
ls examples/networks/crm/   # README.md, network.json, prepare_seed.py, seed.json only
```

## Next queue item

`prompts/cursor/next/2026-06-09-1400-networks-integration-testing.md`
