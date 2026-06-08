# Task: MCP slice 4 — onboarding polish (nits from slices 1–3)

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- `TODO.md` — **MCP onboarding polish (slice 4)**
- `prompts/cursor/done/2026-06-08-1300-mcp-slice1-entity-rename/review.md` (nits)
- `prompts/cursor/done/2026-06-08-1500-mcp-slice3-query-messages/review.md` (nits)

**Depends on:** MCP slices 1–3 committed; Paul MCP live verify **done** (June 2026).

---

## Workflow (mandatory)

1. Claim: move from `prompts/cursor/next/` to `prompts/cursor/in-progress/` before edits.
2. Deliver `prompts/cursor/done/2026-06-08-1600-mcp-slice4-polish/` with `prompt.md`, `output.md`.
3. Smoke by default; no new features — polish and regression guards only.

---

## Objective

Close **non-blocking nits** from MCP onboarding slices 1–3. No new MCP tools, no message-bucket logic changes, no fuzzy matching (separate TODO).

---

## Work items (from `TODO.md`)

### 1. Stale vocabulary sweep

- Grep repo for public-facing `PersonQuery`, `person_key`, `query_person`, `PersonResponse`, `list_specialist_routing` in docs, `TODO.md`, comments, tests.
- Update or remove stale references; keep historical `prompts/cursor/done/` unchanged unless a live doc links to them incorrectly.
- **Thread checkpoint TODO** — already marked done; ensure wording uses `EntityQuery` / `QueryResponse`.

### 2. `test_langsmith_utils` env flake

- Stabilize `test_custom_ui_base` (skip when env unset, or mock) **or** document as optional full-only in `pyproject.toml` / test module docstring.
- Goal: full smoke suite green without special env.

### 3. Test hardening (slice 3 nits)

- `tests/test_specialist_research_integration.py::test_run_query_email_na_in_same_response_when_research_mocked` — add **positive** assert: message contains `not found for this record` (or approved unavailable copy).
- Same file or sibling — when mocked research returns email value, assert `found=['email']` (or equivalent) in `debug` and email value **not** in `message`.

### 4. Specialist message alignment (optional but preferred)

- `src/agents/factory/templates/specialist_agent.py.j2` and framework `src/agents/specialists/*_specialist.py` still `model_copy` legacy messages (`not currently available`, `(via contact_specialist)`).
- **Graph `assemble_response` is authoritative** for CLI/MCP — align specialist-internal copy with `build_query_message` patterns **or** remove overrides and rely on `response_non_core` / `response_found` only.
- Update `tests/test_agent_factory.py` if template string assertions change.

### 5. CRM example `specialists/` directory

- **Decision (document in `output.md`):** commit `examples/networks/crm/specialists/contact_specialist.py` as reference **or** leave gitignored and document that refresh skips `specialists/`.
- If committing: ensure no `__pycache__`, no runtime artifacts; update `examples/networks/crm/README.md` if needed.

### 6. Scrub CRM example runtime artifacts

- Remove committed stray files under `examples/networks/crm/` if present (`agent_registry.json`, `categories.json`, `agents/`, `checkpoints.sqlite`, etc.) — example dir should be copy-source only.
- Confirm `.gitignore` covers network runtime paths.

### 7. Small API nits (only if trivial)

- `find_by_key(person_key: str)` → rename param to `entity_key` (internal only; call sites in same PR).
- `_neutral_json_schema` — deepen descriptions if any “person” leaks remain in MCP schema resources.
- Regenerate or gitignore stale `src/mycelium.egg-info/PKG-INFO` if it still lists `query_person`.

---

## Scope boundaries (strict)

**May modify:**
- `TODO.md`, `README.md`, `docs/*` (stale vocab only)
- `tests/test_langsmith_utils.py`, `tests/test_specialist_research_integration.py`, `tests/test_agent_factory.py`
- `src/agents/factory/templates/specialist_agent.py.j2`, `src/agents/specialists/*_specialist.py` (if doing item 4)
- `examples/networks/crm/`, `.gitignore`
- `src/agents/seed.py`, `src/mycelium_mcp/server.py` (param rename / schema descriptions only)

**Out of scope:**
- Fuzzy matching, per-record multi-match messages, new MCP tools
- `build_query_message` bucket logic changes
- Admin daemon / demo slice 3–4

---

## Tests (smoke — required)

```bash
uv run pytest -m smoke -q
uv run ruff check src tests
```

All smoke tests should pass without `LANGCHAIN_TRACING_V2` or LangSmith UI env vars.

---

## TODO.md

- Mark **MCP onboarding polish (slice 4)** done.
- Mark **MCP onboarding for visiting agents** fully closed (including Paul MCP verify).
- Leave **Fuzzy entity_key matching** and other deferred items open.

---

## Success criteria

- No stale public `person_key` / `query_person` in live docs or `TODO.md` open items.
- Smoke suite green (langsmith flake resolved or documented away).
- Slice 3 test nits addressed.
- CRM example dir clean; `specialists/` decision recorded.
- Specialist template alignment done or explicitly deferred with reason in `output.md`.