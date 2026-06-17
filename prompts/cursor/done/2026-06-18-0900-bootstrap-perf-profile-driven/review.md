# Review: Bootstrap perf — profile-driven alias index fix

**Verdict:** **Approved**  
**Reviewer:** Grok  
**Date:** 2026-06-18

---

## CI

| Suite | Result |
|-------|--------|
| `./bin/ci-local` (Grok re-run) | **472 passed**, 97 deselected; ruff clean; admin-ui build ok |

---

## Delivery

| Artifact | Status |
|----------|--------|
| `src/agents/entity_registry.py` | ✅ `_save(rebuild_field_indexes=...)`; `add_bind_alias` skips rebuild |
| `tests/test_entity_store_evolution.py` | ✅ Spy tests for alias skip + new-entity rebuild |
| `prompt.md` + `output.md` | ✅ |
| Prompt removed from `next/` | ✅ |
| `in-progress/` clean | ✅ |
| `TODO.md` untouched | ✅ |

---

## Spec compliance

| # | Criterion | Status |
|---|-----------|--------|
| E1 | Profile results in prompt; implementation matches O1 | ✅ |
| E2 | Alias path avoids full field-index rebuild | ✅ `test_add_bind_alias_skips_field_index_rebuild` |
| E3 | Lahman multi-team test green | ✅ `test_lahman_seed_handler_multi_team_same_player_id` (smoke) |
| E4 | `./bin/ci-local` green | ✅ |
| E5 | Paul timing re-run | Manual gate — Test 7 pending |

Locked O1–O5: Pass. No batch loader, no specialist changes.

---

## Diff reviewed

- `src/agents/entity_registry.py` — `_save`, `add_bind_alias` (full diff)
- `tests/test_entity_store_evolution.py` — two new smoke tests (full diff)

---

## Design critique

**Strong:**

- Minimal, profile-aligned fix: one optional flag on `_save`, alias path calls `_save(rebuild_field_indexes=False)` instead of `save_entity`.
- Correctness argument is sound: field indexes are derived from `entity.bind_values`; alias attach only extends `bind_index`. `commit_deferred_save` still does one rebuild at grain flush.
- Non-deferred `add_bind_alias` still persists `bind_index` via `_save` without redundant rebuild — correct if alias API is used outside bootstrap later.
- Tests use spy on `_rebuild_field_indexes` plus `lookup_by_bind_values` / `lookup_by_field` — covers the two lookup surfaces.

**Nits (non-blocking):**

1. **~24k new-player rebuilds remain** — expected; profile showed specialist path already cheap. Incremental field-index update is a follow-up only if Test 7 still too slow.
2. **Warm re-bootstrap duplicate `ensure_entity_bind_fields`** still rebuilds via `write_bind_fields` → `save_entity` — out of scope; separate dopey path if re-bootstrap becomes common.

---

## Nits

See design critique #1–#2. No fix slice required.

---

## For Paul

- **Commit:** `perf(bootstrap): skip field-index rebuild on alias-only bind attach` (Grok committed locally after this review).
- **Test 7:** Fresh `--root`; same `time -p` command as Test 6. Expect meaningful drop from skipping ~33k full index scans (roughly half of deferred rebuilds on fresh bootstrap).
- **Push:** Local only until you ask.