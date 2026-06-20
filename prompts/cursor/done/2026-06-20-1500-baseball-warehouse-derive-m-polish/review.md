# Review — baseball warehouse derive M-track polish

**Verdict:** **Approved + polish nits**

**CI:** `./bin/ci-local` — **582** smoke passed, ruff clean, admin-ui build ok.  
**Baseball E2E:** `./bin/smoke-baseball-e2e` — **14** scenarios passed (`intent_dedup_mocked` ok).  
**Slice pytest:** 15 passed (`test_baseball_intent_dedup`, `test_intent_normalization`, `test_intent_map`, `test_baseball_bio_specialist`).

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

## Polish nits (non-blocking)

| # | Item |
|---|------|
| N1 | **Single unrelated cached slug** — if exactly one *other* mapped slug has storage (e.g. only `career_ops` cached) and client asks `batting_average`, warm inference could bind to wrong slug. Spec-allowed v1; add regression test or document assumption if this becomes realistic. |
| N2 | Warm cache ignores `field_is_na` — NA-only slug still pays one intent LLM call before slug-row NA hit. |
| N3 | `labels_for_intent_slug` / zero-candidate warm-cache paths lack direct unit tests (covered indirectly). |
| N4 | `_legacy_derive_entry` tie-break is sorted key order — consider requested-key-first priority. |
| N5 | `BASEBALL_PYTEST_FILES` omits `tests/test_baseball_intent_dedup.py` — `--with-pytest` skips dedup smoke tests. |
| N6 | Smoke `intent_dedup_mocked` could assert both `intent_map.json` mappings (pytest already does). |

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