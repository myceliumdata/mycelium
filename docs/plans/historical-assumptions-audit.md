# Historical assumptions audit

**Status:** Phase 1 + Phase 2 complete (June 2026)  
**Author:** Grok + automated grep  
**Source of truth:** `docs/architecture.md`, `docs/onboarding.md`, `README.md`

**Purpose:** Find early-phase decisions and docs that were stale, misleading, or problematic after entity registry, networks, metering, and seed elimination. Phase 1 was inventory; Phase 2 was targeted cleanup slices.

---

## Executive summary

| Area | Verdict |
|------|---------|
| **Runtime `src/`** | Clean: no `agents.seed`, legacy ingest modules, or SQLite `people` API |
| **Tests** | Fixtures use `import_seed_file` / `network_helpers`; smoke guards on removed APIs |
| **Living docs** | Aligned; [`onboarding.md`](../onboarding.md) added for new contributors |
| **`docs/plans/*`** | Historical slice specs — index in [`README.md`](README.md) |
| **`prompts/resets/*`, `prompts/cursor/done/*`** | Historical; do not rewrite |
| **Intentional vocabulary** | `seed.json` = bootstrap fixture filename; CLI status may still label bootstrap row count "Seed" |

**No blocking runtime lies.** Remaining risk is integrator confusion from old slice plans — mitigated by onboarding doc + plans index.

---

## Phase 2 completed (June 2026)

| Priority | Slice | Status |
|----------|-------|--------|
| P1 | TODO + doc hygiene | **Done** — onboarding doc, README/plans links, audit refresh |
| P2 | Plans index | **Done** |
| P3 | State field rename (`IdentityRecord` / `matched_records`) | **Done** (`538867e`) |
| P4 | `network create` optional `--seed` | **Done** |
| P5 | Unwired legacy module cleanup | **Done** — enrich/validator/person_prep removed |
| P6 | SQLite `people` deprecation | **Done** — slim `CoreStorage`; see [`legacy-ingest-and-storage-reference.md`](../legacy-ingest-and-storage-reference.md) |

Handoffs: [`2026-06-10-legacy-ingest-storage-removal`](../../prompts/cursor/done/2026-06-10-legacy-ingest-storage-removal/).

---

## 1. Runtime code (no action required)

Verified absent in `src/` and `tests/`:

- `agents.seed`, `get_seed_data`, `reset_seed_data`, `find_by_key` (seed module)
- `agents.enrich`, `agents.validator`, `agents.person_prep`
- `seed_from_file`, `find_persons`, SQLite `people` DDL

**Current graph vocabulary:**

| Symbol | Location | Notes |
|--------|----------|-------|
| `IdentityRecord` | `models/state.py`, MCP | Renamed from `SeedRecord` (June 2026) |
| `matched_records` | graph state, supervisor | Canonical match list |
| `mycelium://schema/identity-record` | MCP | Schema URI |

**Bootstrap only:** `import_seed_file`, `seed.json`, optional `--seed` on `network create`.

---

## 2. Operator surfaces & TODO wording

Historical admin/CLI labels may still say **"Seed"** for bootstrap fixture row counts (`network status`, admin overview). That is a **display label**, not the removed runtime seed loader. New docs use **entities / registry** for identity.

---

## 3. Living documentation

| Doc | Status |
|-----|--------|
| `docs/onboarding.md` | **New** — contributor entry point |
| `docs/architecture.md` | Current |
| `README.md` | Current |
| `docs/full-code-walkthrough.md` | Current |
| `docs/database-notes.md` | Current (no `people` table) |
| `docs/legacy-ingest-and-storage-reference.md` | Archival only |
| `docs/plans/README.md` | Active vs historical index |

---

## 4. Historical plans (`docs/plans/`)

**Do not bulk-edit.** Stale seed-resolution or `core_data` language is expected in completed slice specs. Use [`README.md`](README.md) **Active backlogs** for work that may still guide implementation.

---

## 5. Resets & Cursor history

| Path | Treatment |
|------|-----------|
| `prompts/resets/*` | Archive |
| `prompts/cursor/done/*` | Never rewrite |

---

## 6. Product assumptions — resolved (June 2026)

| Assumption | Resolution |
|------------|------------|
| Person-shaped seed only | Still true for `--seed` validation; **optional** — `crm-empty` proves bind-only growth |
| SQLite `people` table | **Removed**; identity is `entities.json` only |
| `SeedRecord` naming | **Renamed** to `IdentityRecord` / `matched_records` |
| `core_data` / enrich path | **Removed** from repo; archival doc only |
| Public ingest API | Removed 2025; future internal data addition is greenfield design |
| Website copy | Separate **mycelium-website** repo; queue copy pass after framework pushes |

---

## 7. Exit criteria

- [x] Grep runtime/tests for seed loader removal
- [x] Spot-check living docs vs architecture
- [x] Classify `docs/plans` stale content
- [x] List intentional debt vs bugs (debt cleared in Phase 2)
- [x] Fix `network_metadata` explicit-root nit
- [x] Hands-on `crm-empty` verified
- [x] `docs/plans/README.md` index
- [x] Phase 2 implementation slices completed
- [x] Contributor onboarding doc
- [x] Website copy pass (mycelium-website — `cd7e796`, June 2026)

---

## Website follow-up

Framework changes that may need public copy updates: identity rename, legacy removal, optional `--seed`, 307 tests. Handoff: **mycelium-website** `prompts/cursor/next/2026-06-11-post-cleanup-onboarding-copy-pass.md`.

---

*Next review trigger: after next major framework phase lands (see `TODO.md` Process → website review).*