# Task: MCP slice 1 — public Entity vocabulary rename (option B)

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md` (claim from `next/`, deliver under `done/`)
- `docs/architecture.md` (public interface)
- `TODO.md` — **MCP onboarding for visiting agents** (schema neutralization locked)
- `src/models/state.py`
- `src/mycelium_mcp/server.py`
- `src/main.py` (CLI query + network status)
- `tests/test_core_graph.py`, `tests/test_network_integration.py`, `tests/test_network_status.py`

**Depends on:** None (first of three MCP onboarding slices).

**Follows:** Design locked in Grok + Paul session (June 2026). Paul is the only client — **no backward-compat aliases** (`person_key`, `query_person`, `PersonQuery`, etc. must not remain as public API).

---

## Workflow (mandatory)

1. Claim this file: move it from `prompts/cursor/next/` to `prompts/cursor/in-progress/` **before** any edits.
2. On completion: deliver `prompts/cursor/done/2026-06-08-1300-mcp-slice1-entity-rename/` with `prompt.md`, `output.md`; remove **only** your claimed file from `in-progress/`.
3. Default tests: `uv run pytest -m smoke -q` unless you add full tests (then run those too per WORKFLOW).

---

## Objective

Rename the **public query vocabulary** from person-centric to entity-neutral across CLI, MCP, models, graph state, responses, and docs. Internal seed file remains `seed.json` with a `people` array (generic seed deferred).

### Rename map (complete — no aliases)

| Old | New |
|-----|-----|
| `Person` | `SeedRecord` |
| `PersonQuery` | `EntityQuery` |
| `person_key` (JSON field) | `entity_key` |
| `PersonResponse` | `QueryResponse` |
| `query_person` (MCP tool) | `query_entity` |

### Graph state (`MyceliumGraphState`)

| Old | New |
|-----|-----|
| `person` | `seed_record` |
| `persons` | `seed_records` |
| `matched_persons` | `matched_records` |

Update docstrings and Field descriptions to use neutral language (“seed record”, “entity”) not “person”.

### CLI

| Old | New |
|-----|-----|
| `--person-key` | `--entity-key` |
| `network status --person` | `--entity` |

### MCP (`src/mycelium_mcp/server.py`)

- Rename tool `query_person` → `query_entity`; docstrings and examples use `entity_key`.
- `_parse_query_payload` validates `EntityQuery`; accepts optional top-level `thread_id` as today.
- `health_check` internal ping JSON uses `entity_key` (not `person_key`).
- **Schema resources** — rename and add request schema:
  - `mycelium://schema/person` → `mycelium://schema/seed-record` (export `SeedRecord.model_json_schema()`)
  - Add `mycelium://schema/entity-query` (`EntityQuery`)
  - `mycelium://schema/person-response` → `mycelium://schema/query-response` (`QueryResponse`)
- Override exported JSON Schema **titles/descriptions** where Pydantic still says “person” — descriptions must be network-neutral (seed record, entity lookup). Titles: `SeedRecord`, `EntityQuery`, `QueryResponse`.
- **Do not** remove `list_specialist_routing` yet (slice 2).
- **Do not** add `describe_network` or change MCP instructions prose beyond replacing `query_person` / `PersonResponse` names if touched (full instructions rewrite is slice 2).

### Responses / debug

- `debug_for_query` uses `entity_key=`.
- All `response_*` builders take `EntityQuery` and return `QueryResponse`.
- `message` strings: replace “anyone” / “person” with neutral record language where user-facing (e.g. “did not match any record”). **Do not** implement the new classification-aware message builder (slice 3).

### Introspection (minimal)

- Rename `PersonFieldStatus` → `EntityFieldStatus` (or `FieldStatus`) and `person_key` / `person_*` fields on `NetworkStatusSummary` to `entity_key` / `entity_*` if present — keep behavior; update formatters and tests.

### Docs

Update `README.md`, `docs/architecture.md`, `docs/full-code-walkthrough.md` for new public names. Do not add `guide.md` (slice 2).

---

## Scope boundaries (strict)

**May modify:**
- `src/models/state.py`, `src/models/__init__.py`
- `src/mycelium_mcp/server.py` (rename only; no `describe_network`, no remove `list_specialist_routing`)
- `src/main.py`
- `src/agents/{supervisor,dispatch,responses,routing,core_identity}.py`
- `src/graphs/core.py`
- `src/network/introspection.py` (rename fields/types only)
- `src/agents/specialists/*_specialist.py` (only if they reference `PersonQuery` / `person_key`)
- `tests/**` (all broken references)
- `README.md`, `docs/architecture.md`, `docs/full-code-walkthrough.md`

**Out of scope (slice 2 / 3):**
- `guide.md`, `describe_network`, `build_network_capabilities()`, dynamic MCP instructions
- Removing `list_specialist_routing`
- Query-time message partition (found / researching / unavailable / out_of_scope)
- Seed file size or `people` array shape
- Generic seed schemas

If you must touch out-of-scope files to fix imports, keep changes minimal and note in `output.md`.

---

## Tests

- Fix all tests broken by rename.
- Add or update **smoke** tests asserting:
  - `EntityQuery.model_json_schema()` title/description do not contain “person” (case-insensitive) in description fields.
  - MCP module exposes `query_entity` (import and `getattr` / tool list if easy).
- Preserve existing behavior: Kevin Zhang ambiguous name → 2 results; smoke graph query still works with `entity_key`.

```bash
uv run pytest -m smoke -q
uv run ruff check src tests
```

Manual (document in `output.md`):

```bash
uv run mycelium query --entity-key "Nichanan Kesonpat"
uv run mycelium network status --entity "Andrea Kalmans"
```

---

## TODO.md

Do **not** mark **MCP onboarding** complete. Optionally add a one-line note under that item: “slice 1 entity rename done” when finished.

---

## Success criteria

- No public `PersonQuery`, `PersonResponse`, `person_key`, or `query_person` in `src/`, CLI, or MCP.
- Smoke tests green; ruff clean.
- Slices 2 and 3 can build on this without further rename work.