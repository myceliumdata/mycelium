# Review: 2026-06-09-1500-seed-json-loader-reprocess

## Status

Reprocessed successfully after the backout that destroyed the original redesign slice artifacts. The delivered work matches the specification in `prompts/resets/2026-06-07_redesign_reset.md` (the 1500 bullet under "Completed & Reviewed Slices" and the detailed "How seed.json Is Generated" section, Step 2).

This slice establishes `data/seed.json` as the canonical, static, read-only origin for person records in the seed-data-context redesign model. It is infrastructure for subsequent slices (state model, elimination of core specialist, context passing, etc.).

## What Cursor Delivered (verified against output.md, prompt, code, and data)

- **`data/seed.json`**: Exact copy of the `"people"` array from `data/seed_crm.json` (457 records). Includes the legacy `"id"` fields (e.g. "person-0001"). Confirmed by direct JSON list comparison (`crm["people"] == seed["people"]`).

- **`src/agents/seed.py`** (new file): 
  - `SeedData` dataclass with `people` list and `by_person_id` index.
  - `get_seed_data()` / `reset_seed_data()` singletons (pattern consistent with classification, storage, registry, etc.).
  - `MYCELIUM_SEED_PATH` env override (falls back to `data/seed.json`).
  - `_assign_person_id`: uuid5 using `NAMESPACE_DNS` + prefix `"mycelium-seed-v1:"` + (legacy `id` or fallback `name|employer`).
  - `_enrich_person`: adds `person_id` (always) and `seed_id` (when legacy id present). Does **not** mutate the on-disk JSON.
  - `find_by_key(person_key)`: supports exact seed id match (0 or 1) or case-insensitive name match (0..N for ambiguity).
  - `reload_from_path` for loading.
  - Module docstring and TODO referencing future phases (richer IDs, provenance, peer retrieval — aligns with redesign target model).

- **`src/storage/core.py`**: 
  - `auto_seed` default changed from `True` to `False`.
  - Docstring updated to explain that people/CRM seeding is now handled by `agents.seed` (direct JSON); this module is for checkpoints/history only in this phase. `seed_from_file` path remains for explicit/test use.

- **`tests/conftest.py`**: Added `reset_seed_data` to the session `_final_cleanup` list (after `reset_storage`).

- **`tests/test_core_graph.py`** (`temp_storage` fixture):
  - Calls `reset_seed_data()` on setup and teardown.
  - Creates a temporary `seed.json` (with legacy "id" for the test person).
  - Sets `MYCELIUM_SEED_PATH`.
  - Explicitly calls `storage.seed_from_file(seed)` (for the SQLite people table used by core lookups in tests).
  - Then `reset_seed_data(); _ = get_seed_data()` to warm the loader.
  - Other envs for registry/specialists/etc. also set (for compatibility with agent-factory).

## Verification (re-executed during this review)

- `uv run pytest -m smoke -q`: 28 passed, 9 deselected.
- `uv run pytest -m full -q -k "query_existing_person or query_missing_person or query_non_core_attributes"`: 3 passed.
- Manual loader checks (via `uv run python`):
  - Count: 457
  - `person_id` present on records, `seed_id` for legacy ids.
  - Idempotent across calls.
  - `find_by_key("Nichanan Kesonpat")`: 1 match.
  - Env isolation (`MYCELIUM_SEED_PATH` override): loads correct count.
  - Exact `people` list match between `seed.json` and `seed_crm.json["people"]`.
- `uv run ruff check` on touched files: clean.
- Data inspection: `data/seed.json` is a faithful copy; no extra keys or reordering.

All commands and results align with (or exceed) what was recorded in the delivered `output.md`.

## Scope Adherence

Strictly limited to 1500 work only, as required by the reprocess prompt and the redesign_reset.md:
- No state model changes (`matched_persons`, `context`, etc. — those are 1510+).
- No supervisor, dispatch, graph, responses, or specialist template changes.
- No elimination of core_data or CORE_PERSON_FIELDS.
- No updates to docs beyond what the slice touched (the reprocess output notes "Ready for next slice").
- Test seed data in fixtures still uses legacy "id" format (appropriate, since 1720 is later).

The reprocess prompt itself correctly scoped the work and required reading the full redesign_reset.md + WORKFLOW etc. first.

## Observations and Notes

- **Positive**: Clean, minimal implementation. Follows established singleton + env + reset patterns from Phase 1 (classification, storage, agent-factory). The `person_id` generation is stable/idempotent as required for the redesign model (specialist data will later override seed). The loader does not touch the on-disk seed.json (user policy: "seed.json is the committed static read-only origin. User replaces the entire file manually").

- **Legacy "id" still present**: Expected. `data/seed.json` and `seed_crm.json` retain the `person-XXXX` ids from the 2026-06-01-1730 processing of raw_data. The 1720 slice (still in next/ as of this review) is the one that will introduce `data/prepare_seed.py` to strip them and make results "id" be the UUID.

- **Test fixture note**: The fixture still seeds the SQLite table explicitly via `storage.seed_from_file` (for the core lookup path that tests exercise). This is correct for the post-1500 but pre-full-redesign state. Later slices (1530+) will change this.

- **Missing referenced doc**: The reprocess prompt references `docs/plans/seed-data-context-architecture.md`, which does not exist on disk (only the three original plans in `docs/plans/`). All details were successfully pulled from the redesign_reset.md instead. Minor documentation debt.

- **Current overall system state (for context)**: Seed loader is live and working. However, `src/agents/supervisor.py`, `src/graphs/core.py`, etc. still reflect the Phase 1 + agent-factory state (core_data_agent routing, classifications, etc.). The full seed-data-context model (context builder, no core specialist, specialists receiving seed + union context, 3 scenarios, etc.) is the target of the remaining reprocess prompts (1510–1720).

- **Git state**: Changes from this slice remain uncommitted in the working tree (`??` for `data/seed.json` and `src/agents/seed.py`; `M` for the modified test/storage files). This is consistent with how previous Cursor slices delivered artifacts.

## Comparison to Spec in `prompts/resets/2026-06-07_redesign_reset.md`

Fully matches:
- The 1500 summary bullet.
- "Step 2 (redesign, Cursor 1500)" in the seed generation history section.
- Policy notes about seed.json being user-managed origin and reset-mycelium ignoring it.
- The TODOs and future-phase comments in the delivered `seed.py` align with the broader redesign vision described throughout the reset (peer retrieval, richer ID strategies, specialist overrides of seed, etc.).

The manual verification matrix in the original/reprocess prompt was executed and passes.

## Verdict / Readiness

Solid, faithful reprocess of the slice. The artifacts (code + data + tests + output) are correct and reviewable. The minimal placeholder review that was previously present has been replaced by this substantive review.

**Ready for the next reprocess slice** (`2026-06-09-1510-state-model-context-reprocess.md` in `next/`).

No blocking issues found. Minor note on the missing plan doc reference (non-blocking for this slice).

(End of review. This replaces the prior placeholder.)
