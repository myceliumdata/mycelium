# Baseball M1b polish — batting specialist nits

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting). **After M1c** (`2026-06-19-1100`) is merged or in tree — do not block M1c on this slice.

**Priority:** Polish only — no new attributes, no framework contract changes.

**Source:** Grok review [`prompts/cursor/done/2026-06-19-1000-baseball-batting-specialist-m1b/review.md`](../done/2026-06-19-1000-baseball-batting-specialist-m1b/review.md) nits P1–P3.

**Principles:**

- **Behavior unchanged** — `career_hr==3`, provenance keys, smoke/E2E gates stay green.
- **Pack + minimal framework touch** — prefer fixing `batting_specialist.py`; extend `SpecialistAgent` only if P2 needs a shared helper.
- **Do not edit `TODO.md`.**

---

## Objective

Clean up three non-blocking issues from M1b without changing the public query contract.

---

## P1 — Align provenance `computation.inline` with executed code

**File:** `examples/networks/baseball/specialists/batting_specialist.py`

**Problem:** `CAREER_HR_COMPUTATION_INLINE` (stored in provenance) differs from `_compute_career_hr` (actual SQL: quoted identifiers, `CAST`, `query_warehouse`).

**Fix (pick one, prefer A):**

- **A (preferred):** Single source of truth — extract one function/module body used for both compute and provenance `inline` (e.g. shared string constant built from the function’s `inspect.getsource`, or one helper `def career_hr(...)` called by both paths).
- **B:** Make `_compute_career_hr` match the locked inline SQL verbatim (no drift).

**Acceptance:** After deliver, `version["computation"]["inline"]` describes the same logic as the code path that produced the value (reviewer can diff mentally or add a one-line test asserting inline contains `SUM` and `playerID`).

---

## P2 — `_mark_na` storage path consistency

**File:** `examples/networks/baseball/specialists/batting_specialist.py` (and `bio_specialist.py` if M1c landed with same pattern)

**Problem:** `_mark_na` uses full `storage.load()` / `save()` while `write_computed_field` uses incremental `load_entity` / `save_entity` on `minisql_v1`.

**Fix:**

- Use the same incremental vs bulk branch as `SpecialistAgent.write_fields` / `write_computed_field` for `_mark_na`.
- **Or** add a small protected helper on `SpecialistAgent` (e.g. `_append_version_for_entity`) used by `write_computed_field` and callable from pack specialists for `na` versions — only if it reduces duplication without scope creep.

**Acceptance:** With `minisql_v1` forced in a test (or threshold crossed), `_mark_na` does not call full-table `save_payload`; existing batting tests still pass.

---

## P3 — Simplify overall-status branching

**File:** `examples/networks/baseball/specialists/batting_specialist.py` — `_evaluate_batting_fields`

**Problem:** Dead/redundant branch: inside `if found_attrs and not pending`, the sub-condition `na_attrs and not found_attrs` is unreachable.

**Fix:** Straighten status selection (`found` / `mixed` / `na` / `pending`) without changing outcomes for current tests.

**Acceptance:** Same `overall_status` for fixture paths; optional unit test on status helper if extracted.

---

## Verification

```bash
./bin/ci-local
uv run pytest tests/test_baseball_batting_specialist.py -q
./bin/smoke-baseball-e2e
```

If M1c shipped in tree, also:

```bash
uv run pytest tests/test_baseball_bio_specialist.py -q
```

---

## Non-goals

- New attrs, provenance schema changes, dataset manifest.
- Refactoring factory template or CRM specialists.
- `TODO.md` edits.

---

## For Grok + Paul (output.md)

- Note P1–P3 resolved.
- No roadmap update required.

**Suggested commit message:**

```
polish(baseball): align batting specialist provenance and storage paths (M1b nits)
```