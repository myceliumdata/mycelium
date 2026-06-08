# Review: MCP slice 1 — entity rename (`2026-06-08-1300`)

**Verdict: Approve with one required fix before merge / slice 2**

Paul is the only client; scope matches the prompt. Core rename (models, CLI, MCP tool/schemas, graph state, introspection, tests, README/architecture) is solid. One runtime gap remains in committed specialist modules.

---

## What looks good

| Area | Notes |
|------|--------|
| **Models** | `SeedRecord`, `EntityQuery`, `entity_key`, `QueryResponse`; graph `matched_records` / `seed_records` |
| **CLI** | `--entity-key`, `network status --entity` |
| **MCP** | `query_entity`, schema URIs `seed-record` / `entity-query` / `query-response`; ping uses `entity_key` |
| **Tests** | New `tests/test_entity_rename.py`; broad test sweep; entity integration smoke passes |
| **Docs** | README + architecture + walkthrough updated (no public `person_key` in README) |
| **Scope** | `list_specialist_routing` retained (slice 2); no `describe_network` / message partition |
| **Template** | `specialist_agent.py.j2` uses `entity_key` / `matched_records` |

**Smoke (review run):** 128 passed, 1 failed (`test_langsmith_utils.py::test_custom_ui_base` — env flake, pre-existing, noted in output).

**Entity smoke:** `tests/test_entity_rename.py` + integration + supervisor routing — 23 passed.

---

## Required fix (before calling slice 1 done)

### Committed specialist `.py` files still use old vocabulary

**Files:** `src/agents/specialists/{contact,demographic,professional,social}_specialist.py`

Still reference `current.query.person_key`, `state.matched_persons`, return `matched_persons` in specialist payloads.

**Why it matters:** Registry loads specialists via `MYCELIUM_SPECIALISTS_DIR/<name>.py` when present, else `import_module("agents.specialists.<name>")`. The framework modules under `src/agents/specialists/` are the fallback for professional/social/demographic on any network without per-network copies. Any attribute query that invokes those specialists will raise `AttributeError` on `EntityQuery.person_key` or read empty `matched_persons`.

**Template was updated; generated copies in `src/agents/specialists/` were not.**

**Fix:** Regenerate or bulk-replace in all four files (mirror `examples/networks/crm/specialists/contact_specialist.py` which was updated correctly):

- `person_key` → `entity_key`
- `matched_persons` → `matched_records`

Optional: add a smoke test that imports each framework specialist module and invokes with minimal `EntityQuery` state (no LLM) to prevent regression.

---

## Minor nits (non-blocking)

1. **TODO.md** — Thread checkpoint item still says `PersonQuery` / `PersonResponse` (stale wording).
2. **`src/agents/seed.py`** — `find_by_key(person_key: str)` param name is internal; fine for slice 1.
3. **`_neutral_json_schema`** — sets `title` only; descriptions come from Pydantic models (already neutral). Adequate for slice 1.
4. **`examples/networks/crm/specialists/`** — only `contact_specialist.py` committed; other categories rely on framework fallback until network create renders them — reinforces need to fix `src/agents/specialists/`.
5. **Runtime artifacts in example dir** — `examples/networks/crm/{agent_registry.json,categories.json,agents/,...}` appear present from local runs; conftest cleans some; unrelated to rename but noisy in repo if committed accidentally.

---

## Unblocks slice 2

After specialist fix: safe to proceed with `guide.md`, `describe_network`, remove `list_specialist_routing`, dynamic instructions.

---

## Suggested follow-up

Tiny fix prompt or manual regen:

```bash
# After fixing template-driven files, verify:
uv run pytest -m smoke -q tests/test_entity_rename.py tests/test_specialist_sync_research.py
```

Paul should **restart MCP** after merge and smoke `query_entity` with `requested_attributes: ["email"]` once specialists are fixed.