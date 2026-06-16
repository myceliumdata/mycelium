# Review: Specialist minisql_v1 — incremental per-entity writes

**Verdict:** **Approved + polish nits**  
**Reviewer:** Grok  
**Date:** 2026-06-17

---

## CI

| Suite | Result |
|-------|--------|
| `./bin/ci-local` (Grok re-run) | **470 passed**, 97 deselected; ruff clean; admin-ui build ok |

---

## Delivery

| Artifact | Status |
|----------|--------|
| `src/storage/minisql_v1.py` | ✅ `load_entity_record`, `upsert_entity_record`, `delete_entity_record`; shared helpers; schema once per connection |
| `src/agents/specialists/base.py` | ✅ `load_entity`, `save_entity`, `delete_entity` |
| `src/agents/specialists/agent.py` | ✅ Incremental `write_fields` / `read_fields`; per-entity rollback |
| `tests/test_specialist_minisql_incremental.py` | ✅ 4 smoke tests |
| `docs/architecture.md` | ✅ Hot-path upsert documented |
| `docs/manual-checks/...-timing-gates.md` | ✅ Test 6 template |
| `prompt.md` + `output.md` | ✅ |
| Prompt removed from `next/` | ✅ |

---

## Spec compliance

| # | Criterion | Status |
|---|-----------|--------|
| E1 | Single-entity upsert; no table-wide DELETE on hot path | ✅ |
| E2 | Unrelated entities preserved | ✅ `test_incremental_write_preserves_unrelated_entities` |
| E3 | Per-entity rollback in `write_bind_fields_multi` | ✅ incl. `delete_entity` when snapshot `None` |
| E4 | Bulk `save_payload` / migration still work | ✅ `test_bulk_save_payload_still_roundtrips` + existing minisql tests |
| E5 | `./bin/ci-local` green | ✅ |
| E6 | Timing test 6 | Paul manual gate |

Locked I1–I8: Pass.

---

## Diff reviewed

- `src/storage/minisql_v1.py` (full incremental + bulk refactor)
- `src/agents/specialists/base.py` — `load_entity` / `save_entity` / `delete_entity`
- `src/agents/specialists/agent.py` — `write_fields`, `read_fields`, `write_bind_fields_multi`
- `tests/test_specialist_minisql_incremental.py` (full)
- `docs/architecture.md`, `docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md`

---

## Design critique

**Strong:**

- Fixes the real O(n²) bottleneck: hot path is now O(1) entities touched per bind (per-entity field DELETE + re-insert only for that row).
- Clean layering: low-level `minisql_v1` upsert APIs + `SpecialistStorage` façade + `SpecialistAgent` branch on strategy.
- Bulk `save_payload` unchanged semantically for migration/tests; `_write_all_records` shared with bulk path.
- Rollback restores prior entity blob or deletes new entity — correct for partial multi-category failure.
- SQL trace test explicitly rejects unqualified `DELETE FROM field_records` / `entity_records`.

**Nits (non-blocking):**

1. **`architecture.md` L191** — still says entity stores are "follow-up slice"; entity `minisql_v1` shipped in slice 4. Doc stale phrase only.
2. **Per-entity upsert still replaces all fields for that entity** (`DELETE … WHERE entity_id` then re-insert) — correct for versioned blobs; true single-field patch is future work if needed.
3. **`_ensure_schema` on every connection** — cheap (`CREATE IF NOT EXISTS`) but still runs each upsert; acceptable v1.

---

## Nits

See design critique #1–#3. No fix slice required.

---

## For Paul

- **Commit:** `perf(specialist): incremental minisql_v1 per-entity upserts` (below).
- **Timing test 6:** Re-run baseball benchmark with this commit; record `real` in manual-check doc Test 6 row. Expect large drop vs test 5.
- **Test 5:** If a pre-fix run is still in flight, discard or finish for historical comparison only — test 6 is the meaningful post-fix number.
- **Follow-up (optional):** entity registry alias `add_bind_alias` index rebuild skip; entity `save_entities_document` full replace.
- **Push:** local only until you ask.