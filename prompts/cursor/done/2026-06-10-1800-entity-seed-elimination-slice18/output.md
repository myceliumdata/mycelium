# Slice 18 — Seed elimination: admin UI + docs + phase exit

## Summary

Operator surfaces now show **Entities** (`registry_entity_count`) only. Removed `seed_people_count` from status API, CLI demo format, admin UI types, and tests. Updated README and architecture for bootstrap-only seed. **Full pytest green** — phase exit gate passed.

## Changes

| File | Change |
|------|--------|
| `admin-ui/src/App.tsx` | Single **Entities** line (removed Seed + separate Registry) |
| `admin-ui/src/types.ts` | Removed `seed_people_count` from `StatusResponse` |
| `src/network/introspection.py` | Dropped `seed_people_count` field; demo/verbose show `Entities:` |
| `tests/test_admin_daemon.py` | Assert `registry_entity_count`; entities.json hot-reload unchanged |
| `tests/test_network_status.py` | `registry_entity_count` assertions; demo text `Entities: ✅ (N)` |
| `tests/test_network_polish.py` | Added `test_empty_network_without_seed_initializes_storage` |
| `tests/test_network_integration.py` | `_activate_network` imports seed → entities for full-suite queries |
| `README.md` | Status curl examples + bootstrap note; MCP reload wording |
| `docs/architecture.md` | Seed bootstrap + registry resolution (no `agents.seed`) |

**Out-of-scope touch (required for full pytest):** `tests/test_network_integration.py` — integration tests needed seed→entities bootstrap after Slice 17 registry-only resolution.

**Not rebuilt:** `admin-ui/dist/` — SPA source updated; rebuild with `npm run build` in `admin-ui/` if committed dist must match.

## Verification

```bash
uv run ruff check src tests   # All checks passed
uv run pytest -q              # 298 passed in 36.60s
```

No `seed_people_count` in `src/`, `tests/`, or `admin-ui/src/`.

## Phase exit criteria (`entity-seed-elimination-phase.md`)

| Criterion | Status |
|-----------|--------|
| No `agents.seed` imports in `src/` | **Pass** (Slice 17) |
| `refresh-example-network crm` populates `entities.json` | **Pass** (Slice 14; integration test) |
| Empty network (no seed.json) works | **Pass** (`test_empty_network_without_seed_initializes_storage`) |
| Full `pytest` green | **Pass** — 298 passed |
| Admin UI shows entities, not seed | **Pass** |

Grok + Paul: apply checkboxes in `docs/plans/entity-seed-elimination-phase.md`.

## For Grok + Paul

- Mark **Slices 14–18** done in `TODO.md` (seed elimination phase complete)
- **API breaking change:** `seed_people_count` removed from `/status` and `mycelium network status --json`; clients use `registry_entity_count`
- Rebuild admin SPA dist if you ship committed `admin-ui/dist/`
- Optional follow-up: `prompts/cursor/next/2026-06-10-1815-entity-seed-elimination-polish.md` (CLI help strings, `docs/full-code-walkthrough.md`)
- Suggested commit message (after review):

```
Seed elimination phase exit: entities-only operator surfaces (Slice 18).

Remove seed_people_count from status API and admin UI; docs/README
bootstrap-only seed; full pytest 298 green.
```

- **Did not edit `TODO.md`** (per governance)
