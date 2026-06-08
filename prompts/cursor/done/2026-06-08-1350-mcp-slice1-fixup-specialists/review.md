# Review: MCP slice 1 fixup — framework specialists (`2026-06-08-1350`)

**Verdict: Approved**

Closes the required finding from slice 1 review.

---

## What was fixed

| Check | Result |
|-------|--------|
| `person_key` / `matched_persons` in `src/agents/specialists/*_specialist.py` | **None** (`rg` clean) |
| All four modules present locally | contact, demographic, professional, social — `entity_key` / `matched_records` |
| Smoke regression | `tests/test_specialist_entity_vocab.py` — 4 parametrized cases |
| Related smoke | 14 passed (entity vocab + entity_rename + specialist_sync_research) |
| Full smoke | 132 passed (1 pre-existing `test_langsmith_utils` flake) |

Regeneration from `specialist_agent.py.j2` was the right approach (matches CRM example copy).

---

## Note on gitignore (not a blocker)

`src/agents/specialists/*_specialist.py` is in `.gitignore` (auto-generated). Regenerated files **won’t appear in git diff** — they exist on disk for local `import_module("agents.specialists.<name>")` fallback. Fresh clones rely on `network create` / factory writing to `<network_root>/specialists/`. That predates this fixup; no change required here.

Untracked `examples/networks/crm/specialists/` (contact only) — optional to commit in slice 2; `refresh-example-network` skips `specialists/` anyway.

---

## Test coverage caveat (minor)

`test_specialist_entity_vocab` exercises specialists **generated into tmp** via factory (template path), not direct import of committed framework `.py` files. Adequate for regression given gitignore policy; optional hardening: import from `src/agents/specialists/contact_specialist.py` when file exists on disk.

---

## Unblocks

**Slice 2** (`guide.md`, `describe_network`, remove `list_specialist_routing`).

**Commit suggestion:** Commit slice 1 + fixup together (still uncommitted on `main`). Restart MCP after merge; smoke `query_entity` with `requested_attributes: ["email"]`.