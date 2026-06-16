# Review — 2026-06-17-1400-multi-mvr-entity-stores

**Verdict: Approved + polish nits**

---

## CI

| Step | Result |
|------|--------|
| `uv sync --all-extras` | Pass |
| `admin-ui` build | Pass |
| `ruff` | Pass |
| smoke pytest | **429 passed**, 93 deselected |

```bash
./bin/ci-local
# CI local: all steps passed.
```

---

## Delivery

`output.md` matches the working tree: implementation files present, `tests/test_multi_mvr_entity_stores.py` added (9 tests), example manifests and docs updated. No tests-only delivery.

---

## Diff reviewed

All 23 changed paths + untracked `tests/test_multi_mvr_entity_stores.py` read.

| File | Notes |
|------|--------|
| `src/network/mvr.py` | `NetworkMvrConfig`, `GrainMvrPolicy`, loaders, legacy flat parse |
| `src/network/paths.py` | `entity_store_path`, `resolve_entity_store_path`, default `entities_path` |
| `src/agents/entity_registry.py` | Per-grain cache, read/write path split, threaded `_mvr` |
| `src/network/bootstrap/handlers/default_seed.py` | `resolve_seed_grain`, `entities_by_grain` |
| `src/network/bootstrap/context.py` | `entities_by_grain` field |
| `src/agents/attribute_write.py` | `ensure_entity_bind_fields` uses `reg._mvr` |
| `src/network/create.py` | `_unlink_entity_stores` for all grain files |
| `src/network/example.py` | Skip `entities/` on copy |
| `src/network/introspection.py` | `load_mvr_config().summary()` in policy |
| Example `network.json` ×4 | Explicit grains; baseball two-grain |
| `docs/architecture.md`, `docs/onboarding.md` | Multi-grain layout documented |
| Test updates + `test_multi_mvr_entity_stores.py` | Capstones, grain paths, isolation |

`/review` subagent not used (diff moderate size; full read completed).

---

## Spec compliance

| # | Criterion | Result |
|---|-----------|--------|
| E1 | `mvr.grains` + `default_grain` parse; legacy flat → `person` | Pass |
| E2 | Per-grain `entities/<grain>.json`; isolated registries | Pass |
| E3 | `load_mvr()` / `get_entity_registry()` no-arg = default grain; query unchanged | Pass |
| E4 | CRM refresh → 15 entities in person grain; empty-crm → 0 | Pass (capstone tests updated) |
| E5 | Legacy root `entities.json` readable when grain file absent | Pass |
| E6 | Baseball `player` + `team` grains, no data | Pass |
| E7 | `describe_network` multi-grain MVR | Pass |
| E8 | Docs updated | Pass |
| E9 | `./bin/ci-local` green | Pass |

Non-goals respected: no Lahman handler, no `target_resolve`/supervisor grain selection, no multi-alias index.

---

## Legacy / dual-path

Slice intentionally ships legacy flat `mvr.bind_fields` and root `entities.json` read fallback per prompt (G4, G9). Paul queued **1500-manifest-required-fail-fast** to remove these next.

---

## Tests

- New `test_multi_mvr_entity_stores.py` covers parse, paths, legacy fallback, per-grain isolation, bootstrap zero for baseball, reset-all-grains.
- Capstone and bootstrap tests updated for `entities/person.json` / `NetworkPaths.entities_path`.
- Gap: no test that `describe_network` policy `mvr` block includes `entities_file` per grain (minor).

---

## Design critique

**Strong**

- Clean separation: `GrainMvrPolicy` carries `entities_file`; config loader is single entry point.
- Per-grain singleton cache with `reset_entity_registry()` clearing all grains — bootstrap-safe.
- `resolve_seed_grain()` prefers `person` then `default_grain` — sensible for CRM seed shape.
- `ensure_entity_bind_fields` uses registry's `_mvr` — correct for grain-aware writes on bind path.
- Committed examples fully explicit; baseball manifest ready for Lahman handler.

**Sub-optimal (non-blocking)**

1. **`write_bind_fields`** still calls `load_mvr()` (default grain) even when `registry=` is passed. Bind path is OK today (default grain only); grain-aware query will need `reg._mvr` parity with `ensure_entity_bind_fields`.
2. **`_default_entity_store_path`** swallows all exceptions and falls back to `entities/person.json` — can mask bad manifests. Slice **1500** removes this.
3. **`network create`** manifest still omits `mvr` block — created networks rely on silent CRM defaults until **1500**.
4. Module docstring on `entity_registry.py` still says root `entities.json`.

---

## Nits

| ID | Severity | Item | Follow-up |
|----|----------|------|-----------|
| N1 | Non-blocking | `write_bind_fields` should use passed registry's MVR policy | Grain query slice or 1500+ |
| N2 | Non-blocking | `entity_registry.py` module docstring outdated | 1500 doc sweep |
| N3 | Non-blocking | `_default_entity_store_path` broad `except` | 1500 removes fallback |

Program polish backlog: n/a (not MVR redesign program slice).

---

## For Paul

- **Commit:** Grok committing locally after this review (message below).
- **Push:** Not until you ask (mid-program local commits).
- **Next:** Run Cursor on **1500-manifest-required-fail-fast** (already in `next/`) to drop legacy shims and require explicit manifest sections.
- **Live roots:** One-time `./bin/refresh-example-network crm --yes` after 1500 lands if you still have root-only `entities.json`.

**Suggested commit message:**

```
feat(network): multi-MVR entity stores per grain

Declare mvr.grains in network.json; per-grain entities/<grain>.json
stores; load_mvr/get_entity_registry default-grain compat; bootstrap
resets all grains. Query path unchanged (default grain only).
```