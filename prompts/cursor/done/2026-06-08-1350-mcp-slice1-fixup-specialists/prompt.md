# Task: MCP slice 1 fixup — framework specialist modules entity rename

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- `prompts/cursor/done/2026-06-08-1300-mcp-slice1-entity-rename/review.md` (required fix)
- `src/agents/factory/templates/specialist_agent.py.j2` (canonical vocabulary)
- `examples/networks/crm/specialists/contact_specialist.py` (correct reference copy)

**Depends on:** Slice 1 entity rename (local/uncommitted or merged). **Blocks:** slice 2 onboarding.

---

## Workflow (mandatory)

1. Claim: move this file from `prompts/cursor/next/` to `prompts/cursor/in-progress/` before edits.
2. Deliver `prompts/cursor/done/2026-06-08-1350-mcp-slice1-fixup-specialists/` with `prompt.md`, `output.md`.
3. Smoke tests by default per WORKFLOW.

---

## Problem

Slice 1 updated `specialist_agent.py.j2` to `entity_key` / `matched_records`, but the **committed framework specialist modules** under `src/agents/specialists/` were not regenerated. They still use `person_key` and `matched_persons`.

Registry loads these via `import_module("agents.specialists.<name>")` when a network has no override at `<network_root>/specialists/<name>.py`. Attribute queries (email, age, etc.) can raise `AttributeError` on `EntityQuery`.

---

## Objective

Bring all four framework specialist modules in line with slice 1 vocabulary. No behavior changes — rename only.

---

## Files to fix (all occurrences in each file)

| Old | New |
|-----|-----|
| `person_key` | `entity_key` (including `current.query.person_key` → `current.query.entity_key`) |
| `matched_persons` | `matched_records` (state fields and return dict keys) |

**Target files:**
- `src/agents/specialists/contact_specialist.py`
- `src/agents/specialists/demographic_specialist.py`
- `src/agents/specialists/professional_specialist.py`
- `src/agents/specialists/social_specialist.py`

**Reference:** `examples/networks/crm/specialists/contact_specialist.py` already correct — use as diff guide if unsure.

**Do not** change `specialist_agent.py.j2` (already correct) unless you find a missed spot.

---

## Regression test (smoke — add)

Add `tests/test_specialist_entity_vocab.py` (or extend `tests/test_entity_rename.py`) with **smoke** tests:

For each of the four specialist module names, `registry.get_agent_fn("<name>")` after minimal registry bootstrap (pattern from `tests/test_specialist_sync_research.py` `_setup_contact_specialist` — tmp paths, `factory.create_specialist`, one specialist is enough if you parametrize four categories OR test all four with four `create_specialist` calls).

Invoke with minimal `MyceliumGraphState`:

```python
MyceliumGraphState(
    query=EntityQuery(entity_key="Jane", requested_attributes=["email"]),
    current_id="test-uuid",
    context={"seed": {"id": "test-uuid", "name": "Jane", "employer": "Acme"}, "specialists": {}},
    target_fields=["email"],
    matched_records=[{"id": "test-uuid", "name": "Jane", "employer": "Acme"}],
)
```

Monkeypatch `tools.research.is_research_available` → `False` (or mock `run_field_research`) so no network/LLM.

**Assert:** call completes without `AttributeError`; result dict uses `matched_records` key if present (not `matched_persons`).

Mark `@pytest.mark.smoke`.

---

## Scope boundaries (strict)

**May modify:**
- `src/agents/specialists/{contact,demographic,professional,social}_specialist.py`
- `tests/test_specialist_entity_vocab.py` (new) or `tests/test_entity_rename.py`

**Out of scope:**
- Slice 2 (`guide.md`, `describe_network`, remove `list_specialist_routing`)
- Slice 3 (query-time messages)
- Regenerating specialists under live `~/mycelium-networks/` (operator runs `refresh` / `network create` separately)
- `examples/networks/crm/specialists/` (already fixed for contact; optional: add other three if missing and trivial)

---

## Verification

```bash
uv run pytest -m smoke -q tests/test_specialist_entity_vocab.py tests/test_entity_rename.py tests/test_specialist_sync_research.py
uv run ruff check src tests
rg 'person_key|matched_persons' src/agents/specialists/*.py
# → no matches (exclude base.py if it has unrelated prose)
```

Document in `output.md`:

```bash
uv run mycelium query --entity-key "Nichanan Kesonpat" --attributes email --network-dir examples/networks/crm
# → QueryResponse without internal AttributeError (may research or pending; must not crash)
```

---

## TODO.md

No change required unless you want one line under slice 1 note: “specialist fixup done”.

---

## Success criteria

- Zero `person_key` / `matched_persons` in the four framework specialist `.py` files.
- New smoke test(s) green.
- Slice 2 safe to run next.