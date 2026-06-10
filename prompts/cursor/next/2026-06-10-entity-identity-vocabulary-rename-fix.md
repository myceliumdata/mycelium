# Task: Identity vocabulary rename — fix framework specialists

> **BLOCKING FIX** — Parent slice reviewed **Approved + fix slice**. Move to `in-progress/` before starting.

**Read first:**

- [`prompts/cursor/done/2026-06-10-entity-identity-vocabulary-rename/review.md`](../done/2026-06-10-entity-identity-vocabulary-rename/review.md) (B1)
- [`src/agents/factory/templates/specialist_agent.py.j2`](../../src/agents/factory/templates/specialist_agent.py.j2) (already correct)

**Depends on:** Identity rename slice in working tree (uncommitted). Do not start network-create slice until this is done.

---

## Objective

Close **B1**: committed framework CRM specialists still reference `SeedRecord` / `seed_record`. Regenerate or update so they match the template (`IdentityRecord` / `identity_record`).

---

## Requirements

1. **Regenerate** (preferred) all four modules under `src/agents/specialists/`:
   - `contact_specialist.py`
   - `demographic_specialist.py`
   - `professional_specialist.py`
   - `social_specialist.py`

   Use the same categories/agents/examples as their current headers (or re-run factory render with equivalent metadata). Match slice `2026-06-09-1605` approach.

2. **Verification grep** (must pass):

   ```bash
   rg 'SeedRecord|seed_records|seed_record|schema/seed-record' src/agents/specialists/
   ```

3. **Add smoke test** in `tests/test_specialist_entity_vocab.py` (or `test_entity_rename.py`):

   - Assert no `SeedRecord` / `payload["seed_record"]` in committed `src/agents/specialists/*_specialist.py` source, **or**
   - Import `agents.specialists.demographic_specialist` from framework path and invoke with single-match state (research unavailable) — must not raise `ImportError`.

4. **README.md** (one line): table row `SeedRecord` → `IdentityRecord` (~line 333).

5. Re-run full suite:

   ```bash
   uv run ruff check src tests
   LANGCHAIN_TRACING_V2=false uv run pytest -q
   ```

---

## Out of scope

- `network create` optional seed slice
- `TODO.md`
- Historical `docs/plans/*`
- Admin UI

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- **Do not create `review.md`.**
- In `output.md`, note parent slice ready for commit after Grok re-review.
- **Do not commit** before review.

---

## Suggested commit message

Squash with parent or amend:

```
Fix: regen framework specialists for IdentityRecord rename.
```