# Task: Seed elimination — Slice 18 (admin UI + docs + phase exit)

> **READY** — Move to `in-progress/` before starting. **Run after Slice 17 is reviewed.**

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/entity-seed-elimination-slice18.md`](../../docs/plans/entity-seed-elimination-slice18.md) — **locked spec**
- [`docs/plans/entity-seed-elimination-phase.md`](../../docs/plans/entity-seed-elimination-phase.md) — exit criteria

**Depends on:** Slice 17 (seed module deleted, smoke green).

---

## Objective

Remove Seed from operator surfaces. **`registry_entity_count`** is the canonical entity count. **Full pytest green** — mandatory sign-off for this phase.

---

## Implement

### 1 — Admin UI

- `admin-ui/src/App.tsx`: remove Seed line; show **Entities** from `registry_entity_count` (single line, not Seed + Registry).
- `admin-ui/src/types.ts`: remove `seed_people_count`.

### 2 — API / status tests

- `tests/test_admin_daemon.py`, `tests/test_network_status.py`:
  - Assert `registry_entity_count` (not `seed_people_count`)
  - Demo CLI text: `Entities: ✅ (N)`
  - Hot-reload test: **`entities.json`** change visible on next `/status` (not `seed.json` edit)

### 3 — `tests/test_network_polish.py`

Replace `test_missing_seed_raises_file_not_found` — seed is **optional** at runtime; empty network without `seed.json` should not error on storage init.

### 4 — Docs

- `README.md` — status curl examples use `registry_entity_count`; bootstrap note (refresh imports seed when present).
- `docs/architecture.md` — seed section: fixture + bootstrap import, registry at query time.
- `docs/plans/entity-seed-elimination-phase.md` — check exit criteria in `output.md` (Grok + Paul apply checkboxes).

### 5 — Phase exit (mandatory)

```bash
uv run ruff check src tests
uv run pytest -q
```

**All tests must pass.** This is the sign-off gate for the seed elimination phase.

---

## Scope boundaries (strict)

**May modify:**
- `admin-ui/src/App.tsx`
- `admin-ui/src/types.ts`
- `tests/test_admin_daemon.py`
- `tests/test_network_status.py`
- `tests/test_network_polish.py`
- `README.md`
- `docs/architecture.md`
- `docs/plans/entity-seed-elimination-phase.md` (exit criteria notes only)

**Out of scope:**
- `TODO.md`
- Historical `prompts/cursor/done/` files
- Rebuilding committed `admin-ui/dist/` unless project convention requires it (note in output)

---

## Governance (mandatory)

- **Do not edit `TODO.md`.** Roadmap updates are for Grok + Paul after review.
- In `output.md`, add **"For Grok + Paul"**: recommend marking Slices 14–18 done; note API field removal (`seed_people_count`); paste full pytest summary.
- **No commit or push before review.** Leave changes in the working tree only.

### Stay in your lane (Cursor)

You are the **implementer**, not the reviewer or planner. Slice 14 incorrectly drafted `review.md` as Grok — do **not** repeat that.

- **Deliver only:** code, tests, in-scope docs, `prompt.md` + `output.md` under `prompts/cursor/done/<this-task>/`.
- **Do not create** `review.md` — review and phase sign-off are **Grok + Paul only** (`prompts/cursor/WORKFLOW.md` §4).
- **Do not** edit `TODO.md` or check exit-criteria boxes in `entity-seed-elimination-phase.md` — report pass/fail in `output.md` for Grok + Paul to apply.
- **Do not** queue follow-up slices, rewrite the phase plan, or edit historical `prompts/cursor/done/` folders.
- If full pytest fails: fix within scope or **stop** and document blockers in `output.md`; do not collapse remaining slices into this diff.

---

## Deliverables

`prompts/cursor/done/2026-06-10-1800-entity-seed-elimination-slice18/` with `prompt.md` and `output.md` **only** (no `review.md`).

Include full pytest result summary in `output.md`.