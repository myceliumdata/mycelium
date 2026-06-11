# Review: Phase 2 legacy ingest and SQLite people removal

**Verdict: Approved**

**Reviewer:** Grok (June 2026)  
**Scope:** Uncommitted working tree in `prompts/cursor/done/2026-06-10-legacy-ingest-storage-removal/`

---

## Summary

Clean, well-scoped single slice. All four legacy modules deleted, `CoreStorage` reduced to path bootstrap, call sites updated, archival doc written, living docs aligned. Active graph validation (`validate_entity`, `validation_passed` fields, `import_seed_file`) untouched. **307 tests pass**, ruff clean. Net −375 lines — appropriate for a deletion slice.

---

## What looks good

| Area | Assessment |
|------|------------|
| **Deletions** | `enrich.py`, `validator.py`, `person_prep.py`, `test_core_data_agent.py` gone; no `src/` imports remain |
| **`CoreStorage`** | Minimal singleton: mkdir parent, open empty SQLite, no `people` DDL or CRUD |
| **Call sites** | MCP + admin bootstrap updated; `main.py` already called `get_storage()` without seed kwargs — no change needed |
| **Archival doc** | `docs/legacy-ingest-and-storage-reference.md` — concise, correct timeline, explicit “do not restore” |
| **Living docs** | `architecture.md`, `database-notes.md`, `full-code-walkthrough.md`, `docs/plans/README.md` updated |
| **Guards** | `tests/test_legacy_ingest_removed.py` smoke tests prevent regression |
| **Preserved** | `entity_validation.py`, graph validation fields, `seed.json` / `import_seed_file`, network bootstrap |

**Verification (re-run):** ruff clean; `rg` on removed symbols — no matches in `src/`; pytest **307 passed** in ~31s.

---

## Non-blocking (Grok on commit)

| Item | Note |
|------|------|
| **Plan status** | `docs/plans/legacy-ingest-storage-removal.md` header still says “Queued” — mark Done on commit |
| **`TODO.md`** | Line 14: mark Phase 2 complete; link archival doc |
| **`historical-assumptions-audit.md`** | Executive summary still lists P5/P6 debt as open — optional one-line footnote after commit (out of slice scope) |
| **`output.md` stale line** | “May be combined with staged CI framework-specialists slice” — ignore; unrelated prior context |

---

## Exit criteria (historical-assumptions audit P5/P6)

- [x] Unwired `enrich` / `validator` / `person_prep` removed from repo
- [x] SQLite `people` identity API removed from `CoreStorage`
- [x] Canonical identity remains `entities.json` + registry/bootstrap
- [x] Archival reference doc for future first-principles redesign
- [x] Full test suite green

---

## Commit

Proceed with suggested message from `prompt.md`:

```
Remove legacy ingest modules and SQLite people identity layer.

Delete unwired enrich/validator/person_prep; slim CoreStorage;
add docs/legacy-ingest-and-storage-reference.md for future redesign.
```