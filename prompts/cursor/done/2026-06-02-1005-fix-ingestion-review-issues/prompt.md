# Task: Address Review Feedback on Ingestion Handshake (Post-1000)

**Created:** 2026-06-02

**Objective:** Fix the minor issues identified in the review of the ingestion handshake redesign (task `2026-06-02-1000-redesign-ingestion-handshake`).

**References:**
- Review of task 1000 (see `prompts/cursor/done/2026-06-02-1000-redesign-ingestion-handshake/review.md` once written, or the review discussion)
- Current implementation in `src/agents/enrich.py`, `src/agents/supervisor.py`, and `docs/architecture.md`

---

## Issues to Address

The following items were flagged during review of the ingestion handshake work:

1. **Misleading docstrings in `enrich.py`**
   - The module docstring says: `"""Enrich agent: ingests minimum viable core person data."""`
   - The function docstring says: `"""Persist provided core person data."""`
   - These are now inaccurate. The enrich agent only *prepares* the record; it no longer persists anything (persistence happens later in the supervisor after validation).

2. **Polish the "Core Ingestion Handshake" section in `docs/architecture.md`**
   - The new section added during task 1000 is accurate but thin.
   - The table could be clearer.
   - The overall description could better explain the flow and the role of `message` vs `debug`.

3. **Review the tone of missing-person guidance**
   - The function `_ingest_guidance_message` (and the message shown when a person is not found) now leans very heavily into telling the caller how to ingest.
   - Review whether the current wording is the right balance between helpful guidance and keeping lookup responses reasonably neutral.
   - Propose and implement any tone adjustments if needed.

---

## Scope Boundaries (Strict)

**You may modify:**
- `src/agents/enrich.py` (docstrings only)
- `docs/architecture.md` (polish the existing ingestion section)
- `src/agents/supervisor.py` (only the `_ingest_guidance_message` function and its usage, if tone changes are agreed)

**You must NOT:**
- Change any runtime behavior or logic.
- Touch the dead-code cleanup work (that is handled in the separate `2026-06-02-1010` task).
- Redesign the ingestion flow.
- Modify `MyceliumGraphState` or add new features.

If you believe any of the above issues require larger changes, document them clearly and stop.

---

## Step-by-Step Instructions

1. **Claim the task**
   - Move this file from `prompts/cursor/next/` to `prompts/cursor/in-progress/`.

2. **Fix the docstrings in `enrich.py`**
   - Update the module and function docstrings to accurately reflect that the agent *prepares* a person record for later validation and persistence.
   - Suggested direction: Use language like "Prepare" or "Enrich/prepare" rather than "ingest" or "persist".

3. **Polish the architecture documentation**
   - Improve the "Core Ingestion Handshake (Phase 1)" section in `docs/architecture.md`.
   - Make the table clearer if possible.
   - Add a short paragraph explaining how the minimalist response model (`results` / `message` / `debug`) is used for ingestion outcomes.
   - Keep the tone consistent with the rest of the document.

4. **Review and adjust (if needed) the missing-person guidance message**
   - Look at `_ingest_guidance_message` in `src/agents/supervisor.py`.
   - Evaluate the current tone.
   - If the tone feels too strongly ingestion-focused for a general lookup response, propose and implement a milder version.
   - If you believe the current tone is appropriate, document that decision clearly in your `output.md`.

5. **Verify**
   - Run `uv run pytest`
   - Run `uv run ruff check src docs`
   - Manually spot-check the CLI for missing-person and ingest scenarios to confirm messaging feels reasonable.

6. **Deliver artifacts**
   - Create the done folder under `prompts/cursor/done/`.
   - Include `prompt.md`, `output.md`, and any relevant notes.
   - Remove only this file from `in-progress/`.

---

## Success Criteria

- [ ] Docstrings in `enrich.py` no longer claim the agent "ingests" or "persists" data.
- [ ] The "Core Ingestion Handshake" section in `docs/architecture.md` is clearer and better written.
- [ ] The missing-person guidance message has been explicitly reviewed; either left as-is with justification or improved.
- [ ] No behavior changes were introduced.
- [ ] Tests and linting remain clean.

---

**This is a narrow, review-follow-up task.** Keep changes small and focused on the three issues above. Do not expand into broader cleanup or redesign work.