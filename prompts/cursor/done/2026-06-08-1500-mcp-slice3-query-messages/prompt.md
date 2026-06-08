# Task: MCP slice 3 — query-time `QueryResponse.message` (classification-aware)

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- `docs/architecture.md`
- `TODO.md` — **MCP onboarding** (query-time messages locked)
- `src/agents/responses.py`
- `src/agents/dispatch.py` (`assemble_response_node`)
- `src/agents/supervisor.py` (classifications, specialist creation audit)
- `tests/test_core_graph.py`, `tests/test_supervisor_routing.py`

**Depends on:** Slices 1–2 (`EntityQuery`, `entity_key`, `query_entity`).

---

## Workflow (mandatory)

1. Claim: move from `prompts/cursor/next/` to `prompts/cursor/in-progress/` before edits.
2. Deliver `prompts/cursor/done/2026-06-08-1500-mcp-slice3-query-messages/` with `prompt.md`, `output.md`.
3. Smoke by default; new integration-style message tests may be **smoke** if mocked/no real LLM.

---

## Objective

Refactor **`QueryResponse.message`** so visiting agents get accurate per-attribute status: classification category, specialist spin-up, researching vs unavailable vs out-of-scope. Values stay in **`results`** only (do not repeat found values in `message`).

**v1 multi-match:** Collective message when multiple seed records match one `entity_key` (Kevin Zhang). Per-record messages are **out of scope** (see TODO **Per-record query messages**).

---

## Attribute buckets

Partition each requested attribute into exactly one bucket:

| Bucket | Meaning |
|--------|---------|
| **found** | Value present in merged/shaped results for that attr |
| **researching** | In scope; specialist pending or in-flight (incl. first pass with no value yet) |
| **unavailable** | In scope; researched, no value (N/A, not pending) |
| **out_of_scope** | Classification `category == "unknown"` — not researched |

`out_of_scope` attrs must **never** use “researching” or “may be available in the future” wording.

---

## Message construction

Implement `build_query_message()` (in `responses.py` or dedicated module) used by `assemble_response_node`.

### Inputs

- `EntityQuery`
- `classifications` (list of dicts from supervisor)
- Merged records / contributions (existing merge logic)
- Optional: `audit_log` snippets for specialist creation (`Supervisor: created new specialist`)

### Prefix (seed match)

- 1 record: `Found record for {name}.`
- N records: `Found {n} records for {entity_key!r}.`

Use `name` from first record when single match; neutral “record” language (not “person”, not “anyone”).

### Per-bucket sentences (verbose — approved)

Use **category name** from classification, not module names (`contact_specialist`):

| Situation | Template |
|-----------|----------|
| Researching (known category) | `Classified {attr} as {category} — researching.` |
| New specialist created (same query) | `Classified {attr} as {category} — setting up a {category} specialist to research it.` |
| Unavailable | `Classified {attr} as {category} — {attr} not found for this record.` |
| Out of scope | `{attr} could not be classified into this network's ontology — it does not appear related to this network.` |

Combine multiple attrs in one message with separate sentences. Order suggestion: found (omit values) → researching/spin-up → unavailable → out_of_scope.

**Do not** append `(via contact_specialist)` suffixes.

### Not found

`No record found for {entity_key!r}.`

### Identity-only query (no `requested_attributes`)

Keep simple: `Found record for {name}.` / plural prefix — unchanged semantics.

---

## Implementation notes

- Refactor `assemble_response_node` to always use `build_query_message()` instead of branching `response_non_core` vs `message_for_assembled` for **message** text. You may keep internal helpers but unified messaging is required.
- When **all** requested attrs are `out_of_scope` and specialists were **not** invoked, message must **not** say “researching”.
- Mixed query example must work: `email` + garbage → researching + out_of_scope in one message.
- **Sync research today:** many queries land in **found** or **unavailable** in one response; **researching** must still work when contrib is `pending`.
- Specialist modules that `model_copy` override `message` may conflict — graph `assemble_response` is authoritative for CLI/MCP path; align or document if specialist overrides remain for non-graph paths.

### `debug`

Keep classifications. Add explicit buckets for tests/operators, e.g.  
`out_of_scope=['weather']`, `researching=['email']`, `unavailable=[]`, `found=['email']` when useful.

---

## Scope boundaries (strict)

**May modify:**
- `src/agents/responses.py`
- `src/agents/dispatch.py`
- `tests/test_core_graph.py`, `tests/test_result_shape.py`, new `tests/test_query_messages.py` (smoke)
- `tests/test_supervisor_routing.py` (only if message assertions break)
- `docs/architecture.md` (short note on message contract)
- `TODO.md` (mark MCP onboarding query-time portion done)

**Out of scope:**
- `describe_network`, `guide.md`, MCP tool list
- Entity rename
- Per-record multi-match messages
- Async job queue / thread checkpoint fixes
- Changing classification engine behavior

---

## Tests (smoke — required)

Add `tests/test_query_messages.py` (smoke) with temp network / existing fixtures:

1. **Out of scope only** — entity match + nonsense attr → message contains “does not appear related”; **no** “researching”.
2. **Mixed** — in-scope attr (e.g. `email` or `age`) + nonsense → both researching/spin-up and out_of_scope phrases.
3. **Multi-match collective** — `Kevin Zhang` + attr → prefix mentions 2 records; collective attr status (no per-record breakdown).
4. **Not found** — neutral wording with `entity_key`.

Use graph `run_query` or `assemble_response` with crafted state where unit path is simpler. Mark `@pytest.mark.smoke`.

Update `test_core_graph.py` assertions if they hard-code “still researching” / “not currently available” — align with new copy.

```bash
uv run pytest -m smoke -q tests/test_query_messages.py tests/test_core_graph.py
uv run ruff check src tests
```

Manual (document in `output.md`):

```bash
uv run mycelium query --entity-key "Nichanan Kesonpat" --attributes email
# MCP query_entity equivalent with garbage attr mixed in
```

---

## TODO.md

Update **MCP onboarding for visiting agents** — mark done when slices 1–3 complete (or note “implementation complete; Paul MCP restart verify”).

Leave **Per-record query messages** and **Seed from Queries** open.

---

## Success criteria

- `message` reflects classification buckets with approved verbose category copy.
- Out-of-scope never sounds like in-progress research.
- Found values only in `results`.
- Smoke tests green; ruff clean.