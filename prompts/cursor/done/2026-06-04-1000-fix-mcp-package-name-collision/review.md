# Review — 2026-06-04-1000-fix-mcp-package-name-collision

**Reviewer:** Grok (on behalf of Paul + Grok)

**Overall:** Excellent, minimal, and precisely scoped packaging fix. Cursor correctly renamed only the colliding `mcp` package to `mycelium_mcp`, updated the entry point, refreshed the three references in README.md, and added light clarifying docstrings. The `mycelium-mcp` script now launches without ImportError, direct imports work, and all existing MCP functionality (including thread_id/trace_id support from 0950) remains intact. No scope creep, no changes to historical done/ artifacts, and verification was thorough.

## Strengths

- **Correct diagnosis and minimal rename**:
  - Chose `mycelium_mcp` (clear, unique, no broad "src/mycelium/" restructuring of agents/graphs/etc.).
  - Only touched the necessary: directory rename (git-tracked as rename), `pyproject.toml` script target, and README paths/diagrams.
  - Console script name `mycelium-mcp` left unchanged (good).

- **Documentation hygiene**:
  - Updated Mermaid, package table, and repo layout tree in README.md to reflect the new path.
  - Added explicit note in the new `src/mycelium_mcp/__init__.py` and top of `server.py` explaining the rename reason. This helps future maintainers.

- **Strict adherence to instructions**:
  - Did not touch any files under `prompts/cursor/done/` (including the 0950 review that documented the problem).
  - Did not touch `docs/architecture.md`, other packages, or add new features.
  - Output.md is clear, includes the exact problem statement, change table, verification commands, and a note about `uv sync` after pulling.

- **Verification quality**:
  - `uv run ruff check src tests` — clean.
  - `uv run pytest -q` — 19 passed (no regressions).
  - `uv run mycelium-mcp` now starts the FastMCP server successfully (no ImportError; the stdio banner appears as expected for MCP servers).
  - Direct import test: `from mycelium_mcp.server import query_person, submit_person_data, run_server, _parse_query_payload` succeeds.
  - Spot-checked that `thread_id` forwarding and `PersonResponse` serialization (with trace_id/thread_id) still work.
  - Output.md correctly notes that `--help` on an MCP stdio server starts it rather than printing usage (realistic expectation).

- **No behavior changes**: The server logic, tool signatures, `_parse_query_payload`, response serialization, etc. are byte-for-byte the same as after 0950. Only the package name changed.

## Minor Observations

- Generated files (`src/mycelium.egg-info/*`) were not part of the commit (normal; they get regenerated on `uv sync` / install). The workspace egg-info now reflects the new entry point.

- One stale reference remains in `prompts/cursor/WORKFLOW.md` (an example "Out of Scope" list still says `- `src/mcp/``). This is illustrative/example text in the workflow doc, not user-facing runtime docs, and was correctly left alone per the task's explicit "do not touch prompts/cursor/..." rule (except the in-progress prompt itself). It can be cleaned in a trivial follow-up if desired, but is not a blocker.

- The `__pycache__` directories were left behind (as instructed: "Touching `.git`, `__pycache__`, or generated files (let the environment clean them)").

- After rename, anyone with an existing venv will need `uv sync` (or `uv pip install -e . --refresh`) for the console script to pick up the new entry point metadata. Cursor documented this well in output.md.

- No updates were needed (or made) to `src/mycelium_mcp/server.py` beyond the top docstring — the internal imports (`from graphs.core`, `from models.state`, etc.) continue to work because the other packages remain top-level (consistent with the project's current flat package layout under src).

## Verdict

**Strongly Approved.**

This was the exact right follow-up task after the 09xx series and the 0950 MCP updates. The fix is surgical, the rationale is clearly documented, verification covers both the launch path and the functional behavior (thread_id/trace_id), and the historical record was left pristine.

The long-standing blocker for using the MCP server (especially the new correlation fields) is now resolved. `uv run mycelium-mcp` and `from mycelium_mcp.server import ...` work as intended.

**Status:** Approved. No changes requested.

The 09xx observability work (trace_id + thread_id for external agents + debugging) is now fully end-to-end functional for both CLI and MCP. Excellent close to the series.