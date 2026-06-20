# Review — baseball warehouse derive M-track polish

**Verdict:** **Approved** (nits remediated in follow-up `2be1b0e+`)

**CI:** `./bin/ci-local` — **591** smoke passed, ruff clean, admin-ui build ok.  
**Baseball E2E:** `./bin/smoke-baseball-e2e` — **14** scenarios passed (`intent_dedup_mocked` ok).  
**Slice pytest:** 11 intent-map + dedup; 16 with normalization/bio suite.

---

## Delivery

| Check | Result |
|-------|--------|
| `output.md` matches implementation | Pass — P1–P4 as claimed |
| Prompt removed from `next/` | Pass — moved to `done/` |
| Scope creep in working tree | **Warn** — see Commit hygiene below |
| Accidental `next/` wipe | **Fixed by Grok** — restored `2026-06-20-1600-live-gate-baseball-crm.md` |

---

## Spec compliance

| # | Requirement | Result |
|---|-------------|--------|
| **P1** | Skip intent LLM on 2nd synonym when one warm mapped slug | Pass — `infer_slug_from_warm_cache()` + persist; `intent_calls` 2→1 |
| **P2** | Legacy read across all labels for intent slug | Pass — `labels_for_intent_slug()` + `_legacy_derive_entry()`; `test_legacy_per_label_storage_hit_for_synonym` |
| **P3** | `intent_dedup_mocked` smoke scenario | Pass — 14 scenarios; one codegen, provenance `intent_slug` |
| **P4** | Bio missing-month test strict `N/A` | Pass — already strict; no change (noted in `output.md`) |
| Docs | M4b gate doc P1/P2 cache-clear note | Pass |

---

## Diff reviewed

| Area | Files |
|------|--------|
| Framework helpers | `src/network/intent_map.py` — `infer_slug_from_warm_cache`, `labels_for_intent_slug` |
| Pack derive path | `examples/networks/baseball/specialists/batting_specialist.py` |
| Tests | `tests/test_baseball_intent_dedup.py`, `tests/test_intent_map.py` |
| Smoke | `bin/smoke-baseball-e2e` |
| Docs | `docs/manual-checks/2026-06-19-baseball-m4b-intent-normalization-gate.md` |
| Subagent | `/review` on polish scope — no blocking bugs |

---

## Design notes

- P1 wiring is correct: warm inference only when `lookup_intent_slug` is missing; persists mapping before skipping LLM; ambiguous multi-slug case covered by `test_warm_cache_ambiguous_still_calls_intent_llm`.
- P2 closes M4b gate caveat: pre-M4b per-label rows readable without migration.
- M4b review nits P2 (smoke dedup) and P3 (intent LLM skip) are closed by this slice.

---

## Polish nits — remediated (Grok follow-up)

| # | Item | Fix |
|---|------|-----|
| N1 | Unrelated single cached slug | `infer_slug_from_warm_cache` requires single mapped slug value; `test_unrelated_warm_slug_does_not_skip_intent_llm` |
| N2 | NA-only warm slug | `is_cached` predicate includes `field_is_na`; `test_infer_slug_from_warm_cache_na_only_slug` |
| N3 | Missing unit tests | `labels_for_intent_slug`, zero-candidate, unrelated-storage unit tests |
| N4 | Legacy key priority | `_legacy_derive_entry`: requested → slug → sorted aliases |
| N5 | Pytest smoke gap | `test_baseball_intent_dedup.py` in `BASEBALL_PYTEST_FILES` |
| N6 | Smoke map assertion | `intent_dedup_mocked` checks both `career_avg` + `batting_average` mappings |

---

## Commit hygiene (Paul / Grok before commit)

Working tree also contains **unrelated** Cursor WIP (fuzzy bind-field upgrade: `entity_resolution.py`, fuzzy tests/docs, etc.). **Do not** one-shot commit the full working tree.

**Polish-only paths:**

- `src/network/intent_map.py`
- `examples/networks/baseball/specialists/batting_specialist.py`
- `tests/test_baseball_intent_dedup.py`
- `tests/test_intent_map.py`
- `bin/smoke-baseball-e2e`
- `docs/manual-checks/2026-06-19-baseball-m4b-intent-normalization-gate.md`
- `prompts/cursor/done/2026-06-20-1500-baseball-warehouse-derive-m-polish/`

**Exclude:** `examples/networks/baseball/checkpoints.sqlite` (never commit), fuzzy slice files, `TODO.md` unless intentional.

---

## For Paul

**Suggested commit:**

```
polish(baseball): M-track derive intent cache + legacy alias reads
```

- M4b manual gate remains **CLEAR**; routine synonym delivers no longer need cache clear between `career_avg` / `batting_average`.
- **Next in queue:** `prompts/cursor/next/2026-06-20-1600-live-gate-baseball-crm.md` (restored).
- **Also pending review:** `prompts/cursor/done/2026-06-18-2100-fuzzy-bind-field-suggestion-upgrade/` (separate uncommitted WIP).
- Push when ready (local only until you choose).