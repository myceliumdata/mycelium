# Output — DefaultSeedHandler generic rows[] and seed-bootstrap doc

## Summary

Made `DefaultSeedHandler` grain- and MVR-neutral: seed files use top-level `rows[]`, bootstrap target grain comes from `bootstrap.seed_grain` or `mvr.default_grain`, and `docs/seed-bootstrap.md` documents the three bootstrap patterns (None / JSON→MVR / Custom). CRM example updated; `./bin/ci-local` green at **478** smoke tests.

## Files changed (high level)

| Area | Change |
|------|--------|
| `bootstrap/config.py` | `BootstrapConfig.seed_grain`; `resolve_bootstrap_grain()` |
| `bootstrap/handlers/default_seed.py` | `load_seed_rows`, `rows[]` validation, env/parent inference for `import_seed_rows` |
| `seed_import.py` | `load_seed_rows` re-export; structural `count_seed_rows`; `__all__` |
| `create.py` | `validate_seed_file` → `rows[]` objects only |
| `introspection.py`, `main.py` | Copy: `rows[]` not `people[]` |
| `examples/networks/crm/` | `seed.json` → `rows`; `prepare_seed.py`; `network.json` `"seed_grain": "person"` |
| `examples/networks/crm-metering/seed.json` | Converted to `rows` |
| `docs/seed-bootstrap.md` | **New** — three bootstrap types, manifest fields, handler resolution |
| `docs/architecture.md`, `docs/onboarding.md` | Seed section + cross-links |
| Tests (13+ files) | Fixtures `people` → `rows`; `test_bootstrap_seed_grain_*`; renamed load tests |

## Breaking changes (for colleagues)

| Surface | Before | After |
|---------|--------|-------|
| `seed.json` top-level key | `people[]` | `rows[]` (legacy key rejected) |
| Loader API | `load_seed_people`, `_load_seed_people` | `load_seed_rows` only |
| Grain selection | `resolve_seed_grain()` preferred `"person"` | `bootstrap.seed_grain` or `mvr.default_grain` |
| Error messages | `Seed people[i]` | `Seed rows[i]`, `'rows' array` |
| `import_seed_rows` / `load_seed_rows` | Implicit person grain | Requires `paths`, `grain`, or `bind_fields`; infers from `MYCELIUM_NETWORK_ROOT` or `seed_path` parent when env applied |
| CRM `network.json` | (implicit) | Optional explicit `"seed_grain": "person"` in bootstrap block |

**External seed files and scripts** using `people[]` must rename to `rows[]` and set `bootstrap.seed_grain` when default grain differs from seed row shape.

## Exit criteria

| # | Status |
|---|--------|
| E1 | No `people` key expectations in `default_seed.py`; no `load_seed_people` in `src/` or `tests/` |
| E2 | CRM `seed.json` uses `rows`; bootstrap imports 15 entities |
| E3 | `docs/seed-bootstrap.md` documents None / JSON→MVR / Custom with examples |
| E4 | `bootstrap.seed_grain` honored; `default_mvr_grain` when omitted — tested |
| E5 | `./bin/ci-local` green — **478** smoke tests |
| E6 | Breaking changes listed above |

## For Grok + Paul

- Mark TODO **“Non-person seed schemas”** done after review.
- `examples/networks/crm/prepare_seed.py` still reads legacy `people` from upstream CSV-derived source when building — output is `rows`; optional follow-up to rename source key if upstream changes.
- Queue `prompts/cursor/next/` is empty; no further slices queued at completion.

**Suggested commit message:**

```
refactor(bootstrap): generic DefaultSeedHandler rows[] and seed doc

Replace people[] with rows[]; bootstrap grain from manifest seed_grain
or default_grain; add docs/seed-bootstrap.md for three bootstrap patterns.
```
