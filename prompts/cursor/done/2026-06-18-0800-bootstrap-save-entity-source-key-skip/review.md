# Review — 2026-06-18-0800-bootstrap-save-entity-source-key-skip

**Verdict: Approved**

---

## CI

| Step | Result |
|------|--------|
| `./bin/ci-local` (Grok) | **Pass** |
| smoke pytest | **495 passed**, 100 deselected (+1 new test) |
| ruff | clean |
| admin-ui build | ok |

---

## Delivery

Recovery re-run after prior **Not Approved** (empty diff). All exit criteria met on a clean 0800-only working tree (0900 stashed separately).

| # | Criterion | Result |
|---|-----------|--------|
| E1 | `save_entity` skips source-key rebuild; field-index rebuild unchanged | ✅ |
| E2 | `test_save_entity_skips_source_key_index_rebuild` | ✅ |
| E3 | `./bin/ci-local` green | ✅ |
| E4 | Test 8c stub in timing-gates doc | ✅ |
| E5 | Manual gate command documented | ✅ (Paul) |

---

## Diff reviewed (4 files)

| File | Notes |
|------|--------|
| `entity_registry.py` | `save_entity` → `_save(rebuild_source_key_index=False)` + docstring; `add_field_alias` parity (O6). `promote_validated` unchanged (full rebuild OK). |
| `test_entity_store_evolution.py` | Spy test: source-key rebuild skipped, field-index rebuild still called once. |
| `timing-gates.md` | Test 8c pending row added. |
| `next/0800` prompt | Removed (duplicate cleanup). |

Scope clean — no Lahman handler, no 0900 hunks.

---

## Correctness

- Lahman path: `save_entity` (empty `source_keys`) → `set_source_keys` (incremental index) → `commit_deferred_save` (full rebuild at flush). Matches `c96c5e2` + test 7 profile.
- Query-time `write_bind_fields` → `save_entity`: bind-only; `source_keys` unchanged; persisted index remains valid.

---

## Next steps

1. Grok commits (this review).
2. Paul runs **Test 8c**; Grok records timing in doc.
3. Restore **0900** stash; apply env-leak remedial; re-review polish.