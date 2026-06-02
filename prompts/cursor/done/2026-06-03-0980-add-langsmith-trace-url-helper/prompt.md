# Task: Add Optional Helper to Construct LangSmith Trace URL

**Created:** 2026-06-03

**Objective:** Add a small, optional helper function that takes a `trace_id` and returns the full LangSmith trace URL. This makes it easy for developers and external agents to jump directly to the trace from a `PersonResponse`.

**References:**
- Previous tasks in the 09xx series (especially the addition of `trace_id` to `PersonResponse`)
- LangSmith trace URL format

---

## Scope (Strict)

**In scope:**
- Create a small, well-named helper function (suggested location: a new small file like `src/utils/langsmith.py` or inside an existing utility module).
- The function should accept a `trace_id: str` and return the full LangSmith URL as a string.
- Make the function easy to discover and use (good name + docstring).
- Optionally expose it in a convenient place (e.g., re-export from `src/utils/__init__.py` if a utils package exists, or from the responses module).

**Out of scope:**
- Automatically including the URL in every `PersonResponse` (the UUID in `trace_id` is sufficient per design).
- Adding CLI flags or MCP tools for the URL.
- Major refactoring or new modules beyond a small helper.

---

## Step-by-Step Instructions

1. **Claim the task**
   - Move this file to `prompts/cursor/in-progress/`.

2. **Determine the correct URL format**
   - Use the standard LangSmith trace URL pattern: `https://smith.langchain.com/o/{org_id}/projects/p/{project_id}/r/{trace_id}`
   - Note that a simpler form (`https://smith.langchain.com/r/{trace_id}`) often works and redirects correctly. Decide on the most robust default and document it.

3. **Implement the helper**
   - Create a small function, e.g.:
     ```python
     def get_langsmith_trace_url(trace_id: str) -> str:
         """Return the LangSmith trace URL for the given trace_id."""
         ...
     ```
   - Make the organization/project IDs configurable via environment variables or the existing project settings if possible (fall back gracefully).
   - Add a clear docstring explaining usage and how to customize the base URL if needed.

4. **Make it discoverable**
   - Place the function in a logical location (suggested: `src/utils/langsmith.py` or similar).
   - Consider a light re-export so callers can do `from src.utils.langsmith import get_langsmith_trace_url`.

5. **Add a minimal test (optional but recommended)**
   - Add a small unit test that the function produces a valid-looking URL.

6. **Verify**
   - `uv run pytest`
   - `uv run ruff check src tests`

7. **Deliver artifacts**
   - Follow the standard workflow and remove only this file from `in-progress/`.

---

## Success Criteria

- [ ] A clear, reusable helper function exists to convert a `trace_id` into a LangSmith trace URL.
- [ ] The function is easy to find and has good documentation.
- [ ] No behavior changes to existing responses or flows.
- [ ] Tests and linting remain clean.

---

**This is an optional polish task.** It can be skipped or done later if desired. The raw `trace_id` UUID in the response is sufficient for most use cases. This helper simply improves developer/agent experience.
