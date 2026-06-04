# Slice 1540 — specialist-template-base (reprocess)

## Claim

Moved `prompts/cursor/next/2026-06-09-1540-specialist-template-base-reprocess.md` → `prompts/cursor/in-progress/.../prompt.md`, then delivered here.

## Summary

Updated the Agent Factory Jinja template for the seed-data-context model: no `CoreIdentity`, uses `person_id` / `context` / `target_fields`, three field scenarios (found / pending research / N/A), `specialist_contrib` payload, unified response builders with `base_records`, and the robustness TODO on pending threads.

| File | Change |
|------|--------|
| `specialist_agent.py.j2` | Full redesign per reset (header, 3 scenarios, `_start_research_if_needed`, daemon stub) |
| `specialists/base.py` | Comment documenting `person_id`-keyed records shape |
| `agent_factory.py` | LLM refine prompt references supervisor + new template |
| `test_agent_factory.py` | Template marker asserts + pending invoke/storage check |

Committed specialist `.py` files under `src/agents/specialists/` were **not** regenerated (that is slice 1600).

## Verification

```text
$ uv run ruff check src/agents/specialists/base.py src/agents/factory/agent_factory.py tests/test_agent_factory.py
All checks passed!

$ uv run pytest -m smoke -q tests/test_agent_factory.py
4 passed in 0.68s

$ uv run pytest -m smoke -q
25 passed, 9 deselected in 0.35s
```

Manual (via test): factory creates `contact_specialist`, invoke with `current_person_id` + `target_fields=["email"]` → `specialist_contrib.status == "pending"`, message contains `not currently available but may be in the future`, storage writes `records[person_id].email.status == "pending"`.

## Scope confirmation

Template + base + factory refine + factory tests only. No supervisor context graph (1550) or specialist re-gen (1600).

**Ready for next slice:** `2026-06-09-1550-supervisor-context-graph-reprocess.md`
