# Task: Fix MCP Server Package Name Collision

**Created:** 2026-06-04

**Objective:** Rename the MCP server package from the conflicting top-level `mcp` to `mycelium_mcp` so that the `mycelium-mcp` console script (and direct imports) resolve to the project's implementation instead of the official `mcp` SDK package (a dependency of `fastmcp`). This resolves the long-standing ImportError that prevents running the MCP server.

**References:**
- Review of task `2026-06-03-0950-update-mcp-server-for-new-response-fields` (identified the packaging blocker).
- `pyproject.toml` (scripts section)
- `src/mcp/server.py` (and its `__init__.py`)
- `README.md` (quick start, architecture diagram, package table, repo layout)
- Previous 09xx tasks that rely on the MCP server working for `thread_id` / `trace_id` support.

---

## Background

The project places its MCP server at `src/mcp/server.py`. Because `packages.find` (where = ["src"]) turns this into a top-level `mcp` package, the installed entry point `mycelium-mcp = "mcp.server:run_server"` and any `import mcp.server` end up importing the official `mcp` SDK (shipped by the `mcp` / `fastmcp` dependencies) instead of the project's code.

Consequences (observed after 0950):
- `uv run mycelium-mcp --help` (or any invocation) fails with `ImportError: cannot import name 'run_server' from 'mcp.server'`.
- The project's server logic (including the recent `thread_id` / `trace_id` wiring) is unreachable via the documented CLI.
- Direct imports require fragile `PYTHONPATH` + `importlib` hacks.
- Installing the project can shadow or be shadowed by the real `mcp` SDK, breaking FastMCP.

The collision is a pre-existing packaging flaw. The 0950 changes correctly updated the *logic* inside the server; this task makes the server actually runnable.

The chosen new name `mycelium_mcp` is unique, clearly indicates it belongs to the Mycelium project, and requires only localized changes (no full "move everything under src/mycelium/" refactor).

---

## Scope (Strict)

**In scope:**
- Rename the directory `src/mcp/` → `src/mycelium_mcp/` (including `__init__.py` and `server.py`).
- Update the console script entry point in `pyproject.toml`.
- Update all user-facing references in `README.md` (Mermaid diagram, table row, repository layout tree, any text mentioning the old path).
- Lightly update docstrings / comments inside the moved `server.py` if they reference the old import or path (keep functional changes to zero).
- Verify that `uv run mycelium-mcp` now succeeds (at minimum `--help` and basic invocation) and that `from mycelium_mcp.server import ...` works cleanly.
- Run `uv run ruff check`, `uv run pytest`, and confirm the MCP tools (query_person / submit_person_data) are still importable and functional after the rename.
- Update the module docstring in the new `__init__.py` or `server.py` to reflect the new package name if helpful.
- Document the change briefly in your `output.md`.

**Out of scope:**
- Renaming or restructuring any other top-level packages (agents, graphs, models, storage, utils, etc.).
- Changing the console script *name* (`mycelium-mcp` stays the same).
- Adding new CLI flags, MCP tools, or behavior changes.
- Modifying any files under `prompts/cursor/done/` (these are historical records; leave the 0950 review and output as-is — they correctly described the problem at the time).
- Updating `docs/architecture.md` (it only mentions MCP at a high level with no hard paths).
- Full editable-install dance or CI changes.
- Touching `.git`, `__pycache__`, or generated files (let the environment clean them).

---

## Success Criteria

- [ ] Directory `src/mycelium_mcp/` exists with the server code; old `src/mcp/` is gone.
- [ ] `uv run mycelium-mcp --help` succeeds (no ImportError) and shows the expected CLI help.
- [ ] `from mycelium_mcp.server import run_server, query_person, submit_person_data` works cleanly.
- [ ] All references in `README.md` (diagrams, tables, layout) have been updated to the new path.
- [ ] `pyproject.toml` entry point points at `mycelium_mcp.server:run_server`.
- [ ] `uv run ruff check src tests` and `uv run pytest -q` both pass with no new failures.
- [ ] The MCP tools continue to forward `thread_id` and return `trace_id`/`thread_id` in responses (spot-check via Python).
- [ ] `output.md` clearly describes the rename, rationale, and verification steps.
- [ ] No changes were made to any `prompts/cursor/done/` files or to unrelated packages.

---

**This is a packaging hygiene / usability fix.** The goal is to make the MCP server (which received important `thread_id`/`trace_id` updates in 0950) actually usable via the documented `mycelium-mcp` entry point. Keep the diff focused and minimal so it is easy to review. After this task the 09xx observability work should be fully functional end-to-end for both CLI and MCP users.
