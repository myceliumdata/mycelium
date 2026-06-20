# Disable warm-cache intent inference (baseball `ops` gate fix)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md`. **Paul:** run this slice immediately, then re-run `./bin/gate-live baseball --fresh-derive`.

**Objective:** Fix live-gate failure `bb-derive-02` (`ops` ≈ 0.928 expected, got **0.305** = `career_avg` value) by removing unsafe `infer_slug_from_warm_cache` binding on intent-map miss.

**Context (Grok diagnosis, June 2026):**

- Gate runs `bb-derive-01` (`career_avg`) then `bb-derive-02` (`ops`) in one session; storage and `intent_map.json` persist.
- M-polish P1 added `infer_slug_from_warm_cache()` so a 2nd synonym could skip the intent LLM when exactly one mapped slug had warm storage.
- On map miss for `ops`, warm cache sees one mapped slug (`career_batting_average`) with warm storage → incorrectly binds `ops` → `career_batting_average`, persists to `intent_map.json`, and returns cached `career_avg` value.
- Manual isolated `ops` two-step CLI works because `career_avg` was not derived first in that session.

**Correct model (Paul):**

| Case | Behavior |
|------|----------|
| `lookup_intent_slug` **hit** | Use mapped slug; skip intent LLM |
| Map **miss** | Call `resolve_intent_slug()` (intent LLM) → storage read / legacy aliases / codegen |
| Synonym dedup (`batting_average` after `career_avg`) | Intent LLM on miss is OK (`intent_calls` may be 2); storage hit under shared slug avoids 2nd codegen |
| Legacy per-label rows | `_legacy_derive_entry()` (P2) still serves synonyms after intent resolves |

Warm-cache inference on miss is **removed** — it cannot distinguish synonyms from unrelated stats.

**Do not edit `TODO.md`.**

---

## Scope (strict)

You may modify only:

- `examples/networks/baseball/specialists/batting_specialist.py`
- `src/network/intent_map.py`
- `tests/test_intent_map.py`
- `tests/test_baseball_intent_dedup.py`

Do **not** change gate catalogs, `bin/gate-live`, CLI, or MCP. Do **not** reintroduce warm-cache under another name.

Read for context only: `docs/architecture.md`, `prompts/cursor/done/2026-06-20-1500-baseball-warehouse-derive-m-polish/`.

---

## Implementation

### 1 — Remove warm-cache call site (`batting_specialist.py`)

In the derive-on-miss branch (~lines 211–231), when `lookup_intent_slug(requested_key, intent_map)` is `None`:

- **Delete** the `infer_slug_from_warm_cache` block (infer, `save_intent_mapping`, in-memory map update).
- **Delete** the import of `infer_slug_from_warm_cache`.
- Go straight to `resolve_intent_slug(...)` when slug not already known from map hit.

Keep unchanged: slug storage read, `_legacy_derive_entry`, `generate_and_run_derive`, audit lines.

### 2 — Remove framework helper (`intent_map.py`)

- **Delete** `infer_slug_from_warm_cache()` entirely (no remaining callers).
- Keep `lookup_intent_slug`, `save_intent_mapping`, `labels_for_intent_slug`.

### 3 — Tests (`test_intent_map.py`)

- Remove tests that only exercised `infer_slug_from_warm_cache` (single candidate, NA-only, ambiguous, unrelated storage, no candidates).
- Keep `test_intent_map_round_trip`, `test_labels_for_intent_slug`.

### 4 — Tests (`test_baseball_intent_dedup.py`)

| Test | Expected change |
|------|-----------------|
| `test_intent_dedup_career_avg_then_batting_average` | `intent_calls == 2` after both delivers (was 1); `codegen_counter == 1` unchanged |
| `test_legacy_per_label_storage_hit_for_synonym` | Still passes; intent LLM on `batting_average` miss, legacy read hits `career_avg` row |
| `test_warm_cache_ambiguous_still_calls_intent_llm` | **Remove** or replace — warm cache no longer exists |
| `test_unrelated_warm_slug_does_not_skip_intent_llm` | Keep; behavior unchanged via `resolve_intent_slug` |

**Add regression test** (gate scenario):

`test_ops_after_career_avg_does_not_reuse_batting_slug` (name flexible):

1. Seed entity via minimal fixture (same helpers as existing dedup tests).
2. Deliver `career_avg` (mocked intent + codegen as existing tests).
3. Assert `intent_map` has `career_avg` → `career_batting_average`; storage has slug row.
4. Patch intent LLM so `ops` in prompt returns `IntentProposal(intent_slug="career_ops", confidence=0.95)` (or distinct slug ≠ `career_batting_average`).
5. Deliver `ops` in same session (new thread ok if storage shared — match gate: same root, no reset between).
6. Assert:
   - `intent_calls` incremented for `ops` (intent LLM ran on miss).
   - `intent_map["ops"]` is the **ops** slug, not `career_batting_average`.
   - Result value is ops mock value, not `0.500` career_avg.

Use mocked codegen for ops (minimal inline returning distinct value e.g. `0.928`) — no live OpenAI in unit test.

---

## Verification (mandatory)

### CI

```bash
./bin/ci-local
```

### Sync live baseball specialists (gate uses `~/mycelium-networks/baseball`, not examples tree)

Specialists are **not** copied on full refresh skip list; pack install copies them on `--sync-only`:

```bash
./bin/refresh-example-network baseball --sync-only --yes --no-default
```

### Clean poisoned intent map (if prior gate run wrote bad binding)

If `~/mycelium-networks/baseball/intent_map.json` contains `"ops": "career_batting_average"`, remove that mapping (or delete the file) before gate — otherwise map **hit** would still return wrong slug even after code fix.

### Live gate

Requires `OPENAI_API_KEY` and `MYCELIUM_COMPUTATION_CODEGEN_MODEL` in `.env`:

```bash
./bin/gate-live baseball --fresh-derive
```

Record in `output.md`: pass/fail counts; `bb-derive-02` `ops` value vs anchor.

---

## Exit criteria

- [ ] Warm-cache inference removed from pack + framework; no dead imports.
- [ ] Dedup + legacy tests updated; new `ops`-after-`career_avg` regression test passes.
- [ ] `./bin/ci-local` green.
- [ ] `./bin/gate-live baseball --fresh-derive` — **15/15** (or document env blocker).
- [ ] `output.md` notes live-root sync + intent_map cleanup steps for Paul.

---

## Governance (mandatory)

- **Do not edit `TODO.md`.** Roadmap updates are for Grok + Paul after review.
- In `output.md`, add **"For Grok + Paul"**: gate result, whether `intent_calls` regression to 2 for synonym dedup is accepted, manual-check doc note.
- Cursor delivers: code, tests, task-scoped docs, and `output.md` only.

## When finished (mandatory — see WORKFLOW.md §3)

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-20-1950-disable-warm-cache-intent-inference/` with `prompt.md` + `output.md`
3. Remove claimed file from `in-progress/` **and** ensure no duplicate remains in `next/`
4. **Do not commit or push** — tell Paul "slice ready for review"

---

## References

- Failing scenario: `tests/live/catalogs/baseball.yaml` — `bb-derive-01`, `bb-derive-02`
- Introduced by: `prompts/cursor/done/2026-06-20-1500-baseball-warehouse-derive-m-polish/` P1
- Held after this: `prompts/cursor/next/2026-06-20-2000-cli-delivery-id-network-hints.md`