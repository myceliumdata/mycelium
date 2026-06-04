# Task: Filter query `results` to requested attributes; fix specialist-first merge and messaging

**Created:** 2026-06-04

**Prerequisite:** Complete `2026-06-04-1300-rename-person-id-to-id` first (`person_id` → `id` everywhere). This task assumes a single canonical `id` field only.

## Problem (repro)

```bash
uv run mycelium query --person-key "Nichanan Kesonpat" --attributes name
```

Current output (incorrect):

```json
{
  "results": [
    {
      "id": "b08b24db-6231-5ad8-aca1-81a09d052460",
      "name": "Nichanan Kesonpat",
      "employer": "1k(x)",
      "person_id": "b08b24db-6231-5ad8-aca1-81a09d052460"
    }
  ],
  "message": "Found record for Nichanan Kesonpat. name not currently available but may be in the future (via contact_specialist)."
}
```

**Expected behavior:**

1. **`results` must include only what was asked for** (plus `id` for disambiguation when a person was found):
   - For `--attributes name` → `{"id": "…", "name": "…"}` — no `employer`.
2. **Specialist always invoked** for classified requested attributes (e.g. `name` → `contact_specialist`). Specialist value **overrides** seed when present; seed is **provisional** while specialist is pending.
3. **Message must match data:** If `name` appears in `results` (including provisional seed value), do not say `name` is "not currently available". Use wording that distinguishes provisional seed vs specialist-confirmed values when useful.

**Out of scope for this slice:** `trace_url` in JSON — CLI keeps printing LangSmith URL on a separate line after JSON (`main.py`).

---

## Read first

- `prompts/system/CORE_PROMPT.md`
- `docs/architecture.md` (Public query flow, Response fields, Storage)
- `prompts/cursor/WORKFLOW.md` and `.cursor/rules/04-cursor-workflow.mdc`
- `src/agents/supervisor.py` — `_identity_records_from_seed`
- `src/agents/dispatch.py` — `assemble_response_node`
- `src/agents/responses.py` — `response_found`, `response_non_core`, `_build_identity_results`
- `src/models/state.py` — `Person`, `PersonResponse`
- `src/main.py` — `_print_response` (CLI trace URL)
- `src/mycelium_mcp/server.py` — MCP JSON shape
- `tests/test_core_graph.py` — result shape assertions

---

## Objective

Implement **attribute-scoped `results`** on `PersonResponse` and **specialist-first merge** with honest messaging (seed provisional until specialist resolves).

---

## Rules for `results` shaping

Centralize filtering in one helper (e.g. `src/agents/responses.py` or a small `src/agents/result_shape.py`) used by all response builders and `assemble_response_node`.

| Case | `results[]` shape |
|------|-------------------|
| **Not found** | `[]` |
| **Found, no `requested_attributes`** | `id`, `name`, `employer` from seed (identity summary lookup) |
| **Found, with `requested_attributes`** | `id` + **only** keys in `requested_attributes` that have values after merge (seed + specialist contributions). Omit keys with no value unless you intentionally surface `"pending"` / `"N/A"` per specialist contract — document the choice in `output.md`. |
| **Multiple matches** | One dict per person; each dict follows the same rules; `id` required per record for disambiguation. |

---

## Implementation hints

1. **`assemble_response_node`** (`dispatch.py`): Merge `specialist_contrib["values"]` over seed per requested attribute (specialist wins when non-pending); then filter to requested keys + `id`.
2. **`_identity_records_from_seed`** (`supervisor.py`): Should not be the final shape for attribute queries — use the merge + filter helper.
3. **Do not skip specialist invocation** for seed-known fields like `name`; seed is fallback only until specialist returns a value.
4. **Factory template** / specialists: align with shared result-shaping helper if they emit `PersonResponse.results`.
5. **Docs:** `PersonResponse` / `architecture.md` / README — document attribute-scoped `results` and provisional seed messaging.

---

## Tests

Follow `prompts/cursor/WORKFLOW.md` test policy: smoke by default; update/add tests as needed.

**Must update:**

- `tests/test_core_graph.py` — update for attribute-scoped `results` and new messaging.
- Add focused unit tests for the result-shaping helper (smoke): e.g. requested `["name"]` → only `id`+`name`; empty requested → `id`, `name`, `employer`.

**Manual verification (record in `output.md`):**

```bash
uv run mycelium query --person-key "Nichanan Kesonpat" --attributes name
uv run mycelium query --person-key "Nichanan Kesonpat"
uv run ruff check src tests
uv run pytest -m smoke -q
```

---

## Out of scope

- Changing classification mapping (`name` → `contact`) in `data/categories.json`.
- Postgres / storage migrations.
- LangGraph graph topology changes beyond assembly/response wiring.

---

## Deliverables (WORKFLOW.md)

1. **Claim:** Move this file to `prompts/cursor/in-progress/2026-06-04-1400-filter-query-results-and-trace-url/prompt.md` before any edits.
2. **Done:** `prompts/cursor/done/2026-06-04-1400-filter-query-results-and-trace-url/` with `prompt.md`, `output.md` (summary, diff stat, test output, before/after JSON for the Nichanan repro).
3. Do not create `review.md` (Grok reviews separately).

---

## Success criteria

- [ ] `--attributes name` returns `results` with only `id` and `name` (no `employer`).
- [ ] Bare lookup (no attributes) still returns useful identity (`id`, `name`, `employer`).
- [ ] Message does not claim an attribute is unavailable when that attribute appears in `results` (including provisional seed).
- [ ] Specialist still invoked for `name`; specialist value overrides seed when present.
- [ ] MCP and CLI share the same `PersonResponse` JSON shape.
- [ ] Smoke tests and ruff pass.