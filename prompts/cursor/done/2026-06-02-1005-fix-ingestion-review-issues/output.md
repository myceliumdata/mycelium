# Output: Fix ingestion review issues (1005)

## Summary

Addressed three review follow-ups from task 1000: accurate enrich docstrings, expanded architecture documentation, and milder missing-person guidance tone. No graph, storage, or routing logic changed.

## 1. `enrich.py` docstrings

| Before | After |
|--------|-------|
| Module: "ingests minimum viable core person data" | "prepares core person records for validation and persistence" |
| Function: "Persist provided core person data" | "Prepare provided core person data (assign id if needed) for the validator" |

Runtime audit/error strings unchanged (out of scope).

## 2. `docs/architecture.md` — Core Ingestion Handshake

- Added intro on shared `PersonQuery` shape
- Replaced thin table with **Intent / What the caller sends / Graph path / What comes back**
- Clarified enrich prepare vs supervisor persist
- New **Response fields** subsection explaining `results` / `message` / `debug` for ingestion outcomes

## 3. Missing-person guidance tone

**Decision:** Softened wording — lookup-first, ingest as optional next step.

**Before:**
> No core record found for 'X'. To add this person, submit minimum viable core fields (name, employer) via submit_person_data or the CLI ingest command (provided_data on the query).

**After:**
> No core record found for 'X'. This lookup did not match anyone in core storage. If you need to add a new person, include name, employer in provided_data (MCP submit_person_data or CLI ingest).

Rationale: A missing lookup is not always an ingest intent; the new text states the miss neutrally then offers ingest path briefly. Ingest details remain in `debug` (`outcome=ingest_required`, `required_fields`).

## Files modified

- `src/agents/enrich.py` (docstrings)
- `src/agents/supervisor.py` (`_ingest_guidance_message` text only)
- `docs/architecture.md` (ingestion section)
- `tests/test_core_graph.py` (assertions aligned with new missing-person message)

## Verification

- `uv run pytest` — 6 passed
- `uv run ruff check src tests` — clean

## In-progress cleanup

Removed only `prompts/cursor/in-progress/2026-06-02-1005-fix-ingestion-review-issues.md`.
