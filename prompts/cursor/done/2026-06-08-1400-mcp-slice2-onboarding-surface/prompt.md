# Task: MCP slice 2 — onboarding surface (`guide.md`, `describe_network`, trim MCP)

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- `docs/architecture.md`
- `TODO.md` — **MCP onboarding**, **Remove list_specialist_routing**
- `src/network/introspection.py`
- `src/mycelium_mcp/server.py`
- `src/network/example.py`, `src/network/create.py`
- `prompts/cursor/done/2026-06-08-1300-mcp-slice1-entity-rename/` (must be merged/done first)

**Depends on:** Slice 1 (`EntityQuery`, `query_entity`, `QueryResponse`, schema resource URIs).

---

## Workflow (mandatory)

1. Claim this file: move from `prompts/cursor/next/` to `prompts/cursor/in-progress/` before edits.
2. Deliver `prompts/cursor/done/2026-06-08-1400-mcp-slice2-onboarding-surface/` with `prompt.md`, `output.md`.
3. Smoke tests by default per WORKFLOW.

---

## Objective

Implement **connect-time** MCP onboarding: author guide file, structured `describe_network`, regenerated instructions, remove registry dump tool. Reuse one capabilities builder for instructions + tool output.

**Do not** change query-time `message` shaping (slice 3).

---

## 1. `guide.md` (author layer)

**Path:** `<network_root>/guide.md` — free-form markdown, no required structure, no frontmatter.

### CRM committed example

Create `examples/networks/crm/guide.md` with **exactly** this content (unless typos):

```markdown
# CRM example

This network is seeded with **investor information**: person names and firms
from a public-safe CRM subset.

Use it to look up people and research investor-related attributes — contact
details, professional background, social profiles, financial signals, and
similar fields that help you understand an investor.

Ask for any attribute that fits that purpose. The network classifies each
request, routes it to the right specialist, and researches it if we do not
have it yet. If a request does not fit this network's purpose, you will
get a clear refusal in the response message.
```

### `refresh-example-network`

- Copy `guide.md` from example dir like `seed.json` (ensure not in `_SKIP_NAMES`).
- Update `examples/networks/crm/README.md`: list `guide.md` in layout; tell operators to edit `guide.md` at network root for visiting agents.

### `network create`

On real create (not `--dry-run`), scaffold `guide.md` using **option B**:
- Short static template (title, section headings).
- Embed the user's `creation_prompt` under an “About this network (draft — edit freely)” section.
- Do **not** call an LLM to write the guide.
- `--dry-run`: do **not** write `guide.md`; optional CLI note that create will scaffold it.

### `network.json` `description`

Keep for manifest/operators only. **`describe_network` must not expose `description`** — only `guide.md` is author prose for agents.

---

## 2. `build_network_capabilities()` (introspection)

Add to `src/network/introspection.py` (or adjacent module imported by MCP):

Returns a JSON-serializable dict:

```python
{
  "network_name": str | None,
  "display_name": str | None,
  "guide_present": bool,
  "guide": str | None,  # full markdown verbatim when present
  "ontology": {
    "present": bool,
    "message": str | None,  # when not present, e.g. bootstrap hint
    "categories": [
      {
        "name": str,
        "description": str,
        "examples": list[str],
      }
    ],
  },
  "policy": {
    "extensibility": "<exact string below>",
    "out_of_scope": "<exact string below>",
    "multi_match": "<exact string below>",
    "query": {
      "tool": "query_entity",
      "request_schema": "mycelium://schema/entity-query",
      "response_schema": "mycelium://schema/query-response",
      "key_field": "entity_key",
      "optional_fields": ["requested_attributes", "thread_id"],
    },
  },
}
```

**Policy strings (use verbatim):**

- **extensibility:**  
  `You may request attributes that fit this network's domain. Each request is classified against the ontology. In-scope attributes are researched by specialist agents; a specialist is created automatically when one does not exist yet.`

- **out_of_scope:**  
  `If an attribute cannot be classified into this network's ontology, the query response will say it does not appear related to this network. Such attributes are not researched.`

- **multi_match:**  
  `When entity_key matches multiple seed records, results contains every match. Disambiguate using fields in each record (for example id and employer on CRM networks). The message summarizes status collectively unless per-record messaging is added later.`

**Ontology:** Reuse category summaries from `categories.json` (name, description, examples). Do **not** include `seed_count`, `network_root`, specialist registry, or full `attribute_map`.

**Missing guide:** `guide_present: false`, `guide: null`, include top-level or policy note:  
`Network author has not provided guide.md yet.`

**Missing ontology:** `ontology.present: false` with short message (align with existing status copy).

**Do not** expose `list_specialist_routing` data.

---

## 3. MCP server changes

### `describe_network` tool

- `@mcp.tool` returning `json.dumps(build_network_capabilities(), indent=2)`.
- After `_bootstrap()` + `refresh_runtime_from_disk()` (same as other tools).
- **Tool only** — no separate MCP resource.

### Instructions

Replace static CRM boilerplate. Generate from the same capabilities builder at `_bootstrap()` / `_apply_mcp_instructions()`:

> Mycelium network **{display_name}** (`{network_name}`). Call **`describe_network`** for the author guide, ontology, and usage policy. Use **`query_entity`** with JSON: `entity_key`, optional `requested_attributes`, optional `thread_id`. Responses are **`QueryResponse`** (`results`, `message`, `debug`, `trace_id`, `thread_id`); read **`message`** for per-attribute status and classification. Use **`health_check`** for server liveness and network binding. Registry, categories, seed, and specialists reload from disk before each query — restart MCP only after code deploy or if reload fails.

Append active network label when metadata available (existing pattern).

### Remove `list_specialist_routing`

- Delete the `@mcp.tool` `list_specialist_routing`.
- Keep `_routing_payload()` for `health_check` `lightweight_tool` check only.
- Update `health_check` docstring (remove “list_specialist_routing” prose).
- Update tests that call standalone `list_specialist_routing`; remove or repoint to `_routing_payload` / `health_check`.

---

## Scope boundaries (strict)

**May modify:**
- `src/network/introspection.py` (+ `network/__init__.py` exports if needed)
- `src/mycelium_mcp/server.py`
- `src/network/example.py`, `src/network/create.py`
- `examples/networks/crm/guide.md`, `examples/networks/crm/README.md`
- `tests/test_mcp_*.py`, `tests/test_network_*.py`, new smoke tests for capabilities
- `README.md`, `docs/architecture.md`, `docs/full-code-walkthrough.md`
- `TODO.md` (mark **Remove list_specialist_routing** done; partial MCP onboarding note)

**Out of scope:**
- Query-time message refactor (slice 3)
- Entity rename (slice 1 — assume done)
- Seed size / `people` array
- Admin daemon HTTP API (demo slice 3)

---

## Tests (smoke)

- `build_network_capabilities()` with temp network root: `guide_present` true when `guide.md` exists; ontology categories when `categories.json` present.
- `describe_network` returns parseable JSON with `policy`, `ontology`, `guide` keys.
- `list_specialist_routing` not importable as MCP tool (grep / tool list).
- `health_check` still passes `lightweight_tool`.
- `refresh-example-network` copies `guide.md` (test or document manual verify).

```bash
uv run pytest -m smoke -q
uv run ruff check src tests
```

---

## TODO.md

- [x] **Remove `list_specialist_routing` from MCP**
- Note on **MCP onboarding**: slice 2 done (guide + describe_network + instructions); slice 3 query messages pending

---

## Success criteria

- CRM example includes committable `guide.md`.
- MCP exposes `describe_network` + `query_entity` + neutral schemas; no `list_specialist_routing`.
- Instructions dynamically reference `describe_network`.
- Smoke green; ruff clean.