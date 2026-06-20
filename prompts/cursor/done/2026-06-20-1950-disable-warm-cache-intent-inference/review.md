# Review — disable warm-cache intent inference (baseball `ops` gate fix)

**Verdict:** **Approved**

**CI:** `./bin/ci-local` — **600** smoke passed, ruff clean, admin-ui build ok (Grok, 2026-06-20).  
**Slice pytest:** `tests/test_baseball_intent_dedup.py` + `tests/test_intent_map.py` — **6** passed.  
**Live gate:** Cursor reported **15/15** with `./bin/gate-live baseball --fresh-derive`; `bb-derive-02` `ops` ≈ **0.928** (was **0.305**). Grok did not re-run live gate (API cost); Paul should confirm once if not already.

---

## Delivery

| Check | Result |
|-------|--------|
| `output.md` matches implementation | Pass — all four scoped files changed as claimed |
| Prompt in `done/` with `prompt.md` + `output.md` | Pass |
| No duplicate in `next/` / `in-progress/` | Pass |
| Scope creep | Pass — only the four paths listed in the prompt |
| `TODO.md` untouched | Pass |

---

## Spec compliance

| # | Exit criterion | Result |
|---|----------------|--------|
| 1 | Warm-cache removed from pack + framework; no dead imports | Pass |
| 2 | Dedup + legacy tests updated; `test_ops_after_career_avg_does_not_reuse_batting_slug` | Pass |
| 3 | `./bin/ci-local` green | Pass — 600 smoke |
| 4 | `./bin/gate-live baseball --fresh-derive` 15/15 | Pass per Cursor `output.md` |
| 5 | `output.md` documents live sync + intent_map cleanup | Pass |

---

## Diff reviewed

| File | Grok read |
|------|-----------|
| `examples/networks/baseball/specialists/batting_specialist.py` | Full derive branch + imports |
| `src/network/intent_map.py` | Full file |
| `tests/test_intent_map.py` | Full file |
| `tests/test_baseball_intent_dedup.py` | Full file |
| `prompts/cursor/done/2026-06-20-1950-disable-warm-cache-intent-inference/output.md` | Claims vs diff |

`/review` subagent: not used (small, focused diff).

---

## Legacy / dual-path

| Path | Unchanged? |
|------|------------|
| Map **hit** → skip intent LLM | Yes — `lookup_intent_slug` then slug storage read |
| Map **miss** → `resolve_intent_slug` + `save_intent_mapping` inside normalization | Yes |
| P2 `_legacy_derive_entry` synonym read | Yes — `test_legacy_per_label_storage_hit_for_synonym` still passes |
| Codegen dedup under shared slug | Yes — `codegen_counter == 1` on `career_avg` + `batting_average` |
| M-polish P1 warm-cache skip (`intent_calls` 1) | **Reverted** — intentional; `intent_calls == 2` accepted |

---

## Tests

| Test | Role |
|------|------|
| `test_ops_after_career_avg_does_not_reuse_batting_slug` | Gate regression — `ops` distinct slug + value after `career_avg` |
| `test_intent_dedup_career_avg_then_batting_average` | Synonym dedup; `intent_calls` 2, codegen 1 |
| `test_legacy_per_label_storage_hit_for_synonym` | P2 legacy row under `career_avg` |
| `test_unrelated_warm_slug_does_not_skip_intent_llm` | Unrelated cached slug does not short-circuit intent |
| `test_intent_map_round_trip` / `test_labels_for_intent_slug` | Framework helpers retained |

Gap: no live-gate pytest for `bb-derive-02` sequence (acceptable — covered by gate catalog + unit regression).

---

## Design critique

**Strong**

- Correct root-cause fix: warm-cache on map miss cannot tell synonyms from unrelated stats when only one mapped slug exists (`career_avg` → `career_batting_average` before `ops`).
- Derive branch is simpler: `lookup_intent_slug` → `resolve_intent_slug` on miss; persistence stays in `resolve_intent_slug`.
- Regression test mirrors gate order (`career_avg` then `ops`) with distinct mock slug/value.
- Intent mock matchers tightened to `Requested attribute label: …` — avoids accidental substring matches in prompts.

**Accepted trade-off**

- M-polish P1 optimization removed: second synonym pays one intent LLM call; codegen still deduped via slug storage. Aligns with Paul’s model (LLM on map miss only).

**Historical note**

- M-polish review (`2026-06-20-1500`) P1/N1 claimed unrelated-slug safety; gate proved the single-mapped-slug case was still unsafe. This slice supersedes that behavior.

---

## Nits

| # | Severity | Item |
|---|----------|------|
| N1 | Non-blocking | `test_unrelated_warm_slug_does_not_skip_intent_llm` name still says “warm_slug” though warm-cache is gone — rename in a future polish pass |
| N2 | Non-blocking | Manual gate doc (`2026-06-20-live-gate-program.md`) not updated by slice — Grok/Paul can add baseball 15/15 note when afternoon sweep is recorded |

No polish backlog row required (fix slice, not program polish).

---

## Commit hygiene

Working tree also contains **unrelated** WIP (live-gate auto-refresh, `crm-metering` catalog, CLI hints in `next/`). **Do not** one-shot commit the full tree.

**This slice only:**

- `examples/networks/baseball/specialists/batting_specialist.py`
- `src/network/intent_map.py`
- `tests/test_baseball_intent_dedup.py`
- `tests/test_intent_map.py`
- `prompts/cursor/done/2026-06-20-1950-disable-warm-cache-intent-inference/`

---

## For Paul

- **Commit message:** `fix(baseball): remove warm-cache intent inference on map miss`
- **Push:** local only until you ask
- **Next slice:** `prompts/cursor/next/2026-06-20-2000-cli-delivery-id-network-hints.md` (was on hold for this fix)
- **Re-test** (if confirming after commit): sync specialists + gate — see review conversation or `output.md` verification section