# Task: Entity key suggestions — protocol slice (Phase 1)

**Read these first (mandatory):**
- [`docs/plans/entity-protocol-and-registry-program.md`](../../docs/plans/entity-protocol-and-registry-program.md) — full program (Paul approved)
- `prompts/cursor/WORKFLOW.md`
- `docs/plans/entity-key-suggestions-phase1.md` — **locked spec; follow exactly**
- `docs/plans/conversations/2026-06-08-entity-key-negotiation.md` — motivation
- `TODO.md` → **Entity key suggestions** (read-only context)
- `src/agents/seed.py`, `src/agents/supervisor.py`, `src/agents/responses.py`, `src/agents/dispatch.py`, `src/models/state.py`, `src/graphs/core.py` (`_route_after_supervisor`)

**Depends on:** Networks path resolver + `runtime_path` hardening on `main` (done).

---

## Objective

Implement **entity key suggestions** for near-miss lookups (Kalman → suggest Kalmans, **never** return Kalmans’ data). Foundation for agent-to-agent negotiation. **No** registry, **no** `entity_unknown`, **no** silent fuzzy resolve.

---

## Locked decisions (do not reinterpret)

1. **Public `outcome` + `suggestions[]` on `QueryResponse`** — see spec for `EntityKeySuggestion` shape and outcome enum values.
2. **Confirmation:** caller re-queries with `suggestions[].entity_key` — no `confirm_suggestion_id`.
3. **Thresholds:** `SUGGESTION_MIN_SCORE = 0.85`, max 5 suggestions, first-token guard, `SequenceMatcher.ratio` on normalized names.
4. **`entity_key_unresolved` vs `not_found`:** unresolved only when ≥1 suggestion passes threshold; Paul Murphy stays `not_found` until slice 2.

Full detail: `docs/plans/entity-key-suggestions-phase1.md`.

---

## Implementation checklist

### Models (`src/models/state.py`)

- [ ] Add `EntityKeySuggestion` pydantic model.
- [ ] Add `outcome: str | None` and `suggestions: list[EntityKeySuggestion]` to `QueryResponse` (default empty list for suggestions).
- [ ] Update JSON schema / field descriptions for MCP consumers.

### Resolution (`src/agents/seed.py` or `entity_resolution.py`)

- [ ] `resolve_entity_key(entity_key) -> EntityResolution` with kinds `exact | multiple | suggest | none`.
- [ ] Keep `find_by_key()` behavior unchanged for exact matches.
- [ ] Normalization helper (comparison only).
- [ ] Skip suggestion pass for UUID-miss keys.
- [ ] Export from sensible module path.

### Responses (`src/agents/responses.py`)

- [ ] `response_entity_unresolved()` — empty `results`, populated `suggestions`, `outcome="entity_key_unresolved"`, agent-readable `message` (include employer when known).
- [ ] Set public `outcome` on existing builders (`response_found`, `response_not_found`, `response_assembled`, etc.) matching debug `outcome=`.
- [ ] `_make_response` accepts `outcome` and `suggestions`.

### Supervisor (`src/agents/supervisor.py`)

- [ ] Replace direct `find_by_key` with `resolve_entity_key`.
- [ ] On `suggest`: **no classification**, empty `specialists_to_invoke`, stash suggestions on state for assemble.
- [ ] On `exact` / `multiple`: unchanged.

### Graph (`src/agents/dispatch.py`, possibly `src/graphs/core.py`)

- [ ] `assemble_response_node`: if resolution is `suggest`, return `response_entity_unresolved` (not `response_not_found`).
- [ ] Ensure `_route_after_supervisor` does not enter `build_context` when `suggest` (no specialists planned).

### MCP onboarding

- [ ] `build_network_capabilities()` — `policy.entity_key_unresolved` string (retry with suggested `entity_key`).
- [ ] `query_entity` tool docstring — document new response fields.

### Tests (`tests/test_entity_key_suggestions.py`, `@pytest.mark.smoke`)

- [ ] `Andrea Kalman` + `email` → `entity_key_unresolved`, suggests `Andrea Kalmans`, empty `results`, no specialist invoke (use tmp seed or `examples/networks/crm`; mock/disable Tavily if needed).
- [ ] `Andrea Kalmans` + `email` → not unresolved.
- [ ] Random unknown → `not_found`, empty suggestions.
- [ ] `Kevin Zhang` → multiple exact matches (not suggest path).

Use `apply_network_paths(NetworkPaths.from_root(...))` in fixtures per existing network tests.

---

## Scope boundaries

**May modify:** `src/models/`, `src/agents/`, `src/network/introspection.py`, `src/mycelium_mcp/server.py`, `tests/`, `examples/networks/crm/guide.md` (one short agent note only if natural).

**Do not modify:** `TODO.md`, entity registry, `EntityQuery` public shape, classification engine logic, specialist templates, metering/x402.

---

## Verification

```bash
uv run pytest tests/test_entity_key_suggestions.py -m smoke -q
uv run pytest -m smoke -q
uv run ruff check src tests
```

---

## Governance (mandatory)

- **Do not edit `TODO.md`.** Roadmap updates are for Grok + Paul after review.
- In `output.md`, add **"For Grok + Paul"**: mark Entity key suggestions slice done when approved; note any spec deviations.
- Cursor delivers: code, tests, task-scoped docs, and `output.md` only.

---

## Deliverables

Move this file to `prompts/cursor/in-progress/` before starting.

On completion, create `prompts/cursor/done/2026-06-09-1000-entity-key-suggestions-protocol/` with:
- `prompt.md` (this file)
- `output.md` — summary, checklist pass/fail, verification results, **For Grok + Paul**