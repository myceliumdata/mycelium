# Output: Clean derivative dataset references

## Queue scan

| `prompts/next/` before claim | Action |
|------------------------------|--------|
| `2025-06-01-1700-clean-derivative-references.md` | **Claimed** (only file) |

Moved to `prompts/in-progress/` before implementation.

## What changed and why

Aligned models and dependent code with `docs/phase-1-direction.md`:

### Models (`src/models/state.py`)

| Removed / replaced | Replacement |
|--------------------|-------------|
| `DerivativeDatasetRef` | — (no central derivative registry) |
| `derivative_pending` status | `specialist_required` |
| `PersonResponse.derivative` | `deferred_attributes: list[str]` |
| `MyceliumGraphState.derivative` | — |
| `DERIVATIVE_ONLY_ATTRIBUTES` | — |
| `attributes_requiring_derivative()` | `non_core_attributes()` |
| `Person.email`, `phone`, `title`, `extra` | — (core is `id`, `name`, `employer` only) |
| `MINIMUM_VIABLE_FIELDS` included `email` | `["name", "employer"]` |

### Call sites (minimal, required for consistency)

- **Orchestrator** — logs non-core attribute requests; returns `specialist_required` instead of creating derivative dataset rows.
- **Enrich** — core upsert only; no derivative record stubs.
- **Validator** — validates `name` and `employer` only.
- **Storage** — `people` table simplified to `id`, `name`, `employer`; derivative tables/methods removed.
- **MCP** — `list_derivative_datasets` → `list_specialist_routing` (stub JSON).
- **CLI / tests / seed** — updated for minimal `Person` and new response shape.

## Remaining concepts (justified)

- **`specialist_required`** + **`deferred_attributes`** — placeholder until real specialist-agent routing exists; no pre-defined dataset types.
- **`non_core_attributes()`** — classifies requested fields outside core; does not define storage for them.
- **`person_key` lookup** — still resolves by id or name via `CoreStorage` (Phase 1 concession; full identity resolution deferred to specialists per direction doc).

## Files modified

- `src/models/state.py`, `src/models/__init__.py`
- `src/agents/orchestrator.py`, `src/agents/enrich.py`, `src/agents/validator.py`
- `src/storage/core.py`, `src/storage/__init__.py`
- `src/mcp/server.py`, `src/main.py`
- `tests/test_core_graph.py`
- `data/seed_crm.json`
- `TODO.md`

## Tests

`uv run pytest` — 4 passed  
`uv run ruff check src tests` — clean

## `TODO.md`

Updated catch-up items for derivative models, storage, statuses, Person minimalism, and tests (marked complete with reference to this prompt).

## Open questions / follow-up prompts

1. **Rename orchestrator → supervisor** (still on TODO).
2. **Supervisor as pure router** — no direct `CoreStorage` lookups long term.
3. **README / MCP docs** — still mention derivative datasets in places; doc-only cleanup prompt.
4. **Existing `data/mycelium.db`** — may retain old columns if created before schema change; delete DB or migrate if needed locally.

## Git

One commit created for this task (see git log).

## In-progress cleanup

Removed only `prompts/in-progress/2025-06-01-1700-clean-derivative-references.md` (this task).
