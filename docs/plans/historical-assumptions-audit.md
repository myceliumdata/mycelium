# Historical assumptions audit (Phase 1)

**Status:** Phase 1 complete (June 2026)  
**Author:** Grok + automated grep  
**Source of truth:** `docs/architecture.md`, `README.md` (June 2026, post seed-elimination)

**Purpose:** Find early-phase decisions and docs that are stale, misleading, or problematic after entity registry, networks, metering, and seed elimination. Phase 1 is inventory + recommendations; Phase 2 is targeted cleanup slices.

---

## Executive summary

| Area | Verdict |
|------|---------|
| **Runtime `src/`** | Clean: no `agents.seed`, `get_seed_data`, `find_by_key`, or `seed_people_count` |
| **Tests** | Clean: fixtures use `import_seed_file` / `network_helpers`; no runtime seed loader |
| **Living docs** (`architecture.md`, `README.md`, `full-code-walkthrough.md`, `prompts/system/`) | Mostly aligned; minor SQLite/legacy notes intentional |
| **`docs/plans/*`** | Many slice specs describe pre-elimination resolution order; **keep as historical** unless actively referenced |
| **`prompts/resets/*`, `prompts/cursor/done/*`** | Historical by definition; do not rewrite |
| **`TODO.md`** | A few operator lines still say “seed” where “registry” is meant |
| **Intentional debt** | `SeedRecord` / `seed_records` state fields; SQLite `people` table; unwired `core_data` era modules on disk |

**No blocking runtime lies found.** Risk is **operator and integrator confusion** from old plans, TODO wording, and deferred renames.

---

## 1. Runtime code (no action required)

Verified absent in `src/` and `tests/`:

- `agents.seed`, `get_seed_data`, `reset_seed_data`, `find_by_key` (seed module)
- `seed_people_count`

**Intentional seed vocabulary (deferred rename):**

| Symbol | Location | Notes |
|--------|----------|-------|
| `SeedRecord` | `models/state.py` | Pydantic model; name kept for schema stability |
| `seed_records` / `seed_record` | graph state, supervisor, MCP schema resource | LangGraph/MCP compatibility |
| `mycelium://schema/seed-record` | MCP | Schema URI; rename is breaking |

**Unwired legacy on disk (documented, not in graph):**

- `src/agents/person_prep.py`, enrich/validator paths referenced in walkthrough
- `tests/test_core_data_agent.py` — skip-only placeholder

**Fixed this session:**

- `network_metadata(root=...)` no longer lets `MYCELIUM_NETWORK` env override an explicit `--network-dir` root; reads registry match → `network.json` `name` instead.

---

## 2. Operator surfaces & TODO wording

| Item | File | Issue | Recommendation |
|------|------|-------|----------------|
| Admin status line | `TODO.md` L98 | “seed + entities.json” | → “registry (`entities.json`)" |
| Network status bullet | `TODO.md` L49 | “seed, ontology, specialists” | → “entities, ontology, specialists” |
| Multi-match note | `TODO.md` L209 | “seed records” | → “registry rows” |
| Demo slice 39 | `TODO.md` L39 | “✅ Seed (N)” in admin polish | Historical done item; optional footnote |

---

## 3. Living documentation

| Doc | Status | Notes |
|-----|--------|-------|
| `docs/architecture.md` | **Current** | Bootstrap vs registry; query-only API; metering layers |
| `README.md` | **Current** | Post polish; bootstrap/empty-crm/examples |
| `docs/full-code-walkthrough.md` | **Current** | Registry resolution; notes legacy modules |
| `docs/database-notes.md` | **Current** | SQLite legacy called out; entities.json canonical |
| `prompts/system/CORE_PROMPT.md` | **Current** | Bootstrap fixture wording |
| `prompts/system/PROJECT_BRIEF.md` | **Current** | June 2026 blurb |

**Minor intentional legacy mentions:** SQLite `people` table, `SeedRecord` type name in architecture/walkthrough (accurate as implemented).

---

## 4. Historical plans (`docs/plans/`)

**Do not bulk-edit.** These are slice specs and design conversations. Stale content is expected.

Plans with **runtime seed resolution** language (historical only):

- `entity-protocol-and-registry-program.md` — lookup order included seed `find_by_key`
- `entity-registry-bind-phase4.md`, `entity-key-suggestions-phase1.md`
- `entity-uuid4-unification-slice13.md`, `entity-seed-elimination-slice14`–`18.md` (slice specs; phase doc marked **Complete**)
- `seed-data-context-architecture.md` — references `agents/seed.py` timeline
- `agent-factory-phase2.md`, `classification-engine-phase1.md` — pre-redesign supervisor/`core_data` (some have historical notes; good)

**Recommendation:** Add `docs/plans/README.md` (Phase 2) with:

- “Authoritative today: `docs/architecture.md`”
- “Slice plans are point-in-time; completed phases may describe removed code”
- Index of **active** vs **archived** plan families

---

## 5. Resets & Cursor history

| Path | Treatment |
|------|-----------|
| `prompts/resets/2026-06-07_redesign_reset.md` | Archive; describes seed loader and `core_data` removal |
| `prompts/resets/2026-06-05_mvp_current.md` | Archive |
| `prompts/cursor/done/*` | Never rewrite; reviews may reference old counts |

---

## 6. Product assumptions to revisit (design, not bugs)

| Assumption | Then | Now | Question for Paul |
|------------|------|-----|-------------------|
| Person-shaped seed only | v1 `--seed` validates `people[]` | Still true; `network create` requires `--seed` | Priority for generic entity seed / empty `network create`? |
| SQLite `people` table | Core identity store | Legacy; queries use `entities.json` | Remove SQLite people path entirely or keep for migration story? |
| `SeedRecord` naming | Seed-era graph state | Registry rows; name deferred | Schedule breaking rename slice or keep indefinitely? |
| `core_data` as special | Privileged CRM table | Eliminated; supervisor + registry | Delete unwired `person_prep` / enrich docs from walkthrough? |
| Cars / generic domain marketing | Vision | CRM is **example** only | Website updated; framework README already generic networks |

---

## 7. Recommended Phase 2 slices (priority order)

| Priority | Slice | Scope | Est. |
|----------|-------|-------|------|
| P1 | **TODO + doc hygiene** | Fix L49, L98, L209; optional `docs/plans/README.md` | 30 min |
| P2 | **Plans index** | `docs/plans/README.md` — active vs historical, link architecture | 45 min |
| P3 | **State field rename** (optional) | `seed_records` → `matched_records` in public MCP schema / graph export | Large; breaking |
| P4 | **`network create` without `--seed`** | Launch v2; empty-crm proves growth path | Design + implementation |
| P5 | **Unwired legacy module cleanup** | Remove or quarantine `person_prep`, stale enrich paths | Medium |
| P6 | **SQLite people deprecation** | Document-only or remove `storage/core` people seeding paths | Medium |

---

## 8. Phase 1 exit criteria

- [x] Grep runtime/tests for seed loader removal
- [x] Spot-check living docs vs architecture
- [x] Classify `docs/plans` stale content (historical, keep)
- [x] List intentional debt vs bugs
- [x] Fix `network_metadata` explicit-root nit
- [x] Hands-on `empty-crm` verified
- [ ] Phase 2 slices queued in `prompts/cursor/next/` (Paul + Grok)

---

## For Paul

1. Confirm **P1 TODO hygiene** — Grok can apply in one commit.
2. **`docs/plans/README.md`** — worth doing before onboarding another contributor?
3. **`SeedRecord` / `seed_records` rename** — breaking; defer or schedule?
4. **`network create` without `--seed`** — next launch track after empty-crm?

---

*Next review trigger: after next major framework phase lands (see `TODO.md` Process → website review).*