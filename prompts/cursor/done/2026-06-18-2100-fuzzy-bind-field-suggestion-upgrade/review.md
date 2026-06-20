# Review — fuzzy bind-field suggestion upgrade (2100)

**Verdict:** **Approved + polish nits**

**CI:** `./bin/ci-local` — **598** smoke passed, ruff clean, admin-ui build ok.  
**Fuzzy pytest:** 46 dedicated + clarity overlap; matrix 16 scorer + 15 step-1 rows (all green).  
**Live gate unblock:** `crm-negative-01` (`654 Ventures` → `645 Ventures`) now matches scorer behavior.

---

## Why this review was late

Cursor landed fuzzy work in the **same uncommitted working tree** as later slices (M-track polish, live gate). We reviewed polish and live gate first because those were the active queue items; fuzzy sat in `done/` without `review.md` and was never isolated in its own commit. Process fix: treat every `done/` folder missing `review.md` as pending regardless of what else is in the tree.

---

## Delivery

| Check | Result |
|-------|--------|
| `output.md` matches implementation | Pass |
| Prompt in `done/` | Pass |
| No duplicate in `next/` | Pass |
| Matrix E7 (all rows green) | Pass — 30 matrix + 27 clarity-related in fuzzy run |
| `TODO.md` edited by Cursor | Pass — not touched (Grok/Paul mark shipped separately) |

---

## Spec compliance (E1–E7)

| # | Criterion | Result |
|---|-----------|--------|
| E1 | `Tie Cobb` → `lookup_suggested` / `Ty Cobb` | Pass — unit + `test_tie_cobb_partial_player_lookup_suggested` |
| E2 | CRM fuzzy regressions | Pass — Andrea Kalman, 654 Ventures, clarity tests |
| E3 | `645` → `645 Ventures`; Dodgers not fuzzy | Pass — prefix rule + matrix rejects `dodgers`/`brooklyn dodgers` |
| E4 | `John Cobb` / `Ty Cobb` not suggested | Pass — scorer + matrix |
| E5 | `fuzzy-lookup-policy.md` updated | Pass — operator table + composite signals |
| E6 | `./bin/ci-local` green | Pass — 591 smoke |
| E7 | Matrix fully green | Pass |

---

## Diff reviewed

| Area | Files |
|------|--------|
| Scorer | `src/agents/entity_resolution.py` — Levenshtein, composite signals, OR-rules, unified reason |
| Protocol | `src/models/state.py`, `src/agents/responses.py` |
| Tests | `test_fuzzy_bind_field_suggestions.py`, `test_fuzzy_bind_field_suggestion_matrix.py`, clarity + MCP public |
| Smoke | `bin/smoke-crm-e2e` — accepts new + legacy reason |
| Docs | `fuzzy-lookup-policy.md`, `full-code-walkthrough.md`, `baseball-example-program.md`, `query-record-type-router.md` |

---

## Design notes

- **Locked design honored:** suggest-only; stdlib-only; prefix shorthand at 0.88; last-token anchor with lev ≤ 2; CRM first-token gate removed.
- **Public API** `fuzzy_bind_field_similarity()` + matrix gives durable contract for future scorer tweaks.
- **Backward compat:** `responses.py` and smoke accept legacy `bind_field_fuzzy_match` in message shaping.

---

## Polish nits — remediated (Grok follow-up `d0825bc+`)

| # | Item | Fix |
|---|------|-----|
| N1 | Dead `_DEFAULT_ONTOLOGY_MODEL` in `create.py` | Left in place (harmless; LLM env slice owns semantics) |
| N2 | Stale matrix docstring | Updated — shipped regression gate wording |
| N3 | Manual gate doc reason strings | Errata + tables + 0c checks → `fuzzy_bind_field_match` |
| N4 | Test coverage gaps | Reason asserts in matrix; boundary + ranker tests; fuzzy files in `smoke-crm-e2e --with-pytest` |
| N5 | **Follow-up** (deferred): indexed pre-filter for 24k-player scan; phonetic layer |

---

## For Paul

**Suggested commit:**

```
feat(resolve): composite fuzzy bind-field suggestions

Multi-signal typo scoring with last-token anchor and first-token prefix
shorthand; Tie Cobb → Ty Cobb; 645 → 645 Ventures.
```

- Hand-retest anchors from `output.md` when convenient.
- `TODO.md` already has fuzzy item `[x]` in working copy; mark **live gate** `[x]` separately after operator smoke.
- Enables live gate `./bin/gate-live crm --phase negative` on deployed CRM root.