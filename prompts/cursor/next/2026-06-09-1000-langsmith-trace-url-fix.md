# Task: Fix LangSmith trace URLs — auto-resolve org/project, update docs

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- `src/utils/langsmith.py` (`get_langsmith_trace_url`)
- `src/main.py` (`_print_response` — prints URL after JSON)
- `tests/test_langsmith_utils.py`
- `README.md` (LangSmith tracing section)
- `.env.example` (LangSmith vars)

**Context (verified June 2026):** Tracing works and traces upload to LangSmith. The short URL form `https://smith.langchain.com/r/{trace_id}` (used when org/project IDs are unset) returns **“Page not found”** in the current LangSmith UI. The full project-scoped URL works:

`https://smith.langchain.com/o/{org_id}/projects/p/{project_id}/r/{trace_id}`

Org ID comes from the LangSmith project's `tenant_id`; project ID from `read_project(name=LANGCHAIN_PROJECT).id`. Env vars `LANGSMITH_ORG_ID` + `LANGSMITH_PROJECT_ID` also work when set manually.

---

## Problem

CLI prints a broken short link when optional env vars are missing, even though `trace_id` is valid and the trace exists in cloud. README marks org/project IDs as "optional," which is misleading for clickable links.

---

## Objective

1. Make `get_langsmith_trace_url()` produce **working deep links by default** when tracing credentials are available.
2. Update docs so setup expectations match reality.
3. Keep explicit env overrides for users who prefer static IDs.

---

## Proposed approach

### `src/utils/langsmith.py`

Enhance `get_langsmith_trace_url(trace_id: str) -> str`:

1. **Precedence for org/project resolution:**
   - If both `LANGSMITH_ORG_ID` and `LANGSMITH_PROJECT_ID` are set (non-empty after strip) → use them (current behavior).
   - Else attempt **lazy API resolve** (once per process, module-level cache):
     - Requires `LANGCHAIN_API_KEY` or `LANGSMITH_API_KEY`.
     - `project_name = os.getenv("LANGCHAIN_PROJECT", "mycelium").strip()`.
     - `Client().read_project(project_name=project_name)` → `project_id = project.id`, `org_id = project.tenant_id` (or equivalent field LangSmith exposes on the project model).
     - Cache successful resolution; on failure, cache the miss briefly or leave uncached so a later call can retry (implementer choice — avoid hammering API on every query in a tight loop).
   - If API resolve fails or no API key → fall back to short URL `{base}/r/{trace_id}` **but** document in docstring that this may 404 in UI.

2. Add a small internal helper, e.g. `_resolve_langsmith_scope() -> tuple[str, str] | None`, to keep `get_langsmith_trace_url` readable.

3. Do **not** add network calls from MCP on every tool invocation unless cached — first CLI query may hit API once; subsequent calls use cache.

### Tests (`tests/test_langsmith_utils.py`, smoke)

- Existing tests unchanged (env-var path, custom base, empty trace_id).
- New: mock `langsmith.Client.read_project` returning a project with `id` and `tenant_id`; unset org/project env vars; assert full scoped URL.
- New: when API mock raises / no key, assert fallback short URL (current default).
- New: explicit env vars take precedence over API mock (regression).

Use `monkeypatch` + `unittest.mock`; no real LangSmith network in tests.

### Docs

- **`.env.example`:** Clarify that `LANGSMITH_ORG_ID` / `LANGSMITH_PROJECT_ID` are optional because the app can auto-resolve them when `LANGCHAIN_API_KEY` + `LANGCHAIN_PROJECT` are set; note manual override still supported.
- **`README.md` LangSmith section:** Same clarification; mention short `/r/` links may 404; full links work after auto-resolve or manual IDs.
- **`docs/architecture.md`:** One sentence on observability URL behavior if the trace-id bullet exists (minimal edit).

**Out of scope:** MCP server printing trace URLs automatically; changing `PersonResponse` shape; LangSmith tracing enable/disable logic.

---

## Verification

```bash
uv run pytest -m smoke -q tests/test_langsmith_utils.py
uv run ruff check src/utils/langsmith.py tests/test_langsmith_utils.py
```

**Manual (document in `output.md`):** With org/project env vars **unset** but `LANGCHAIN_API_KEY` + `LANGCHAIN_PROJECT=mycelium` set, run:

```bash
uv run mycelium query --person-key "Nichanan Kesonpat" --attributes email
```

Printed URL should use `/o/.../projects/p/.../r/...` and open in browser while logged into LangSmith.

---

## Scope boundaries (strict)

**May modify:**
- `src/utils/langsmith.py`
- `tests/test_langsmith_utils.py`
- `README.md` (LangSmith section only)
- `.env.example` (LangSmith comment block only)
- `docs/architecture.md` (observability bullet only, if needed)

**Out of scope:**
- `src/main.py` logic changes (unless a one-line comment)
- MCP server, graph, tracing capture
- `TODO.md` (Grok updates after review)

---

## Workflow

Per `prompts/cursor/WORKFLOW.md`:

1. Claim this file → `in-progress/` before edits.
2. Implement, test, commit.
3. Deliver `prompts/cursor/done/2026-06-09-1000-langsmith-trace-url-fix/` with `prompt.md`, `output.md`.
4. Remove only your claimed file from `in-progress/`.

---

## Success criteria

- CLI trace URLs open in LangSmith UI without requiring manual `LANGSMITH_ORG_ID` / `LANGSMITH_PROJECT_ID` when API key + project name are configured.
- Env overrides still work.
- Smoke tests green; minimal diff.