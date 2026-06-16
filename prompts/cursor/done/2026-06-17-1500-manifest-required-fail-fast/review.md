# Review — 2026-06-17-1500-manifest-required-fail-fast

**Verdict: Approved + polish nits**

Paul’s four checkpoints are addressed in **§ Paul’s checklist** below.

---

## CI

| Step | Result |
|------|--------|
| `uv sync --all-extras` | Pass |
| `admin-ui` build | Pass |
| `ruff` | Pass |
| smoke pytest | **433 passed**, 93 deselected |

```bash
./bin/ci-local
# CI local: all steps passed.
```

**Before / after (Grok):**

| Point | Slice 1400 (`1b1029e`) | Slice 1500 (this diff) |
|-------|------------------------|-------------------------|
| Smoke count | 429 passed | **433 passed** (+4) |
| CRM capstones | Green | Green (included in 433) |
| Legacy shim tests | `test_legacy_flat_mvr_*`, `test_legacy_entities_json_read_fallback` | **Removed**; replaced with fail-fast + `test_entity_store_uses_grain_path_only` |

---

## Delivery

`output.md` matches working tree. Implementation + test fixture sweep delivered; not docs-only.

---

## Diff reviewed

33 files changed since `1b1029e` (full read of `src/network/mvr.py`, `paths.py`, `metering_policy.py`, `entity_registry.py`, `create.py`, `tests/network_helpers.py`, `tests/test_multi_mvr_entity_stores.py`, example manifests, primary docs).

---

## Paul’s checklist

### (a) All CRM examples on new MVR definition

**Pass.** All three CRM committed examples declare explicit multi-grain MVR + metering:

| Network | `default_grain` | `grains.person` | `metering` |
|---------|-----------------|-----------------|------------|
| `crm` | `person` | `name`, `employer` | yes |
| `empty-crm` | `person` | `name`, `employer` | yes |
| `crm-metering` | `person` | `name`, `employer` | yes (`enabled: true`) |

No flat root-level `mvr.bind_fields` in any example manifest.

### (b) Tested before and after

**Pass.** Grok ran `./bin/ci-local` at **1400 review** (429 smoke) and again for **this slice** (433 smoke). CRM regression tests remain in the suite:

- `test_refresh_crm_imports_seed_into_entities` → 15 entities at `entities/person.json`
- `test_run_network_bootstrap_crm_seed` → 15 entities
- Example capstones, MVR, metering, graph smoke — all green

New fail-fast coverage: missing `network.json` / `mvr` / `metering` / `default_grain`, flat `bind_fields` rejected, root `entities.json` not read when grain file absent.

### (c) No code supporting old scheme

**Pass** for runtime behavior. Removed from `src/`:

- `_crm_default_config()` / `_crm_default_mvr()`
- `_crm_default_metering()` silent fallback
- `resolve_entity_store_path()` and read/write path split
- Flat `mvr.bind_fields` parsing (now **raises**)
- `_unlink_entity_stores` root `entities.json` cleanup

`grep` over `src/`: no `_crm_default`, no `resolve_entity_store`. Only rejection message for flat `bind_fields` remains (intentional).

**Residual prose only (not functional):** docstrings/comments still say `entities.json` generically in `main.py` help, `attribute_write.py`, `introspection.py`, `storage/core.py`, etc. — see nits.

`_provisional_paths().entities_path = root / "entities.json"` is a pre-manifest bootstrap placeholder only; not used as canonical store once manifest loads.

### (d) Documents updated

**Pass** for primary operator docs:

| Doc | Updated |
|-----|---------|
| `docs/architecture.md` | Required `mvr.grains` / `default_grain`; per-grain paths; no fallback language in storage § |
| `docs/onboarding.md` | `entities/<grain>.json`; explicit manifest required |
| `README.md` | `entities/<grain>.json`, `entities/person.json` for CRM |
| `docs/database-notes.md` | Refresh imports to `entities/person.json` |

Historical `docs/plans/*` and archival docs may still mention old flat MVR — out of scope per prompt.

---

## Spec compliance

| # | Criterion | Result |
|---|-----------|--------|
| E1 | `_crm_default_*` deleted | Pass |
| E2 | Flat `bind_fields` / missing sections → `ValueError` | Pass |
| E3 | `default_grain` required (single + multi grain) | Pass |
| E4 | No `resolve_entity_store_path` fallback | Pass |
| E5 | `network create` writes `mvr` + `metering` | Pass |
| E6 | CRM 15 entities, `entities/person.json` | Pass |
| E7 | Docs/README/onboarding updated | Pass |
| E8 | `./bin/ci-local` green | Pass |

---

## Design critique

**Strong:** Single canonical path via `entity_store_path()`; manifest validation centralized in `_load_manifest_dict`; `copy_crm_network_manifest()` gives tests one CRM-shaped fixture; `network create` now self-contained.

**Sub-optimal (non-blocking):** Scattered `entities.json` strings in comments/help — cosmetic drift from grain paths.

---

## Nits

| ID | Item | Action |
|----|------|--------|
| N1 | `src/main.py` `--seed` help still says `entities.json` | Doc sweep: `entities/<grain>.json` |
| N2 | `docs/architecture.md` framework write path bullet still says “syncs `entities.json` cache” | Say per-grain entity store |
| N3 | `write_bind_fields` / `reg._mvr` (1400 deferred) | Grain query orchestrator slice — tracked in `TODO.md` |

---

## For Paul

- **Commit:** Grok committing locally.
- **Push:** When you ask.
- **Live CRM:** `./bin/refresh-example-network crm --yes` if root still has only legacy `entities.json`.
- **Next:** `LahmanSeedHandler` slice.