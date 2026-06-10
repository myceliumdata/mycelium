# Review: Identity vocabulary rename (breaking)

**Verdict: Approved + fix slice**

**Reviewer:** Grok (June 2026)  
**Scope:** Uncommitted working tree in `prompts/cursor/done/2026-06-10-entity-identity-vocabulary-rename/`

---

## Summary

The core rename is solid and well-scoped: `IdentityRecord`, graph state fields, MCP schema URI, supervisor consolidation on `matched_records`, template + CRM example specialist updated. **300 tests pass**, ruff clean.

One **blocking** gap: four committed framework specialist modules under `src/agents/specialists/` were not regenerated and still lazy-import `SeedRecord` / emit `seed_record` on the single-match return path. That path will `ImportError` at runtime when those modules are loaded from `agents.specialists.*` (registry `module_path` used in several tests and legacy paths). Cursor's `output.md` grep claim (`no matches` in `src/`) is incorrect for this reason.

Everything else is approve-as-is or non-blocking polish.

---

## What looks good

| Area | Assessment |
|------|------------|
| **Models** | `IdentityRecord` + state field renames; docstrings updated to registry vocabulary |
| **Supervisor** | Option A: canonical `matched_records`; no redundant typed lists on happy path; `planner_context` for short-circuits |
| **MCP** | `mycelium://schema/identity-record`; imports `IdentityRecord` |
| **Template** | `specialist_agent.py.j2` uses `identity_record` / `IdentityRecord` |
| **CRM example** | `examples/networks/crm/specialists/contact_specialist.py` aligned |
| **Tests** | `test_entity_rename.py`, outcome tests updated; factory-rendered specialist tests pass |
| **Docs** | `architecture.md`, `full-code-walkthrough.md` touched |
| **Intentional keep** | `seed.json`, `--seed`, `import_seed_file`, introspection `source == "seed"` (bootstrap fixture) |

**Diff footprint:** 16 files, net −118 lines — appropriate for a rename + consolidation slice.

---

## Blocking

### B1 — Framework specialists not regenerated

**Files:** `src/agents/specialists/{contact,demographic,professional,social}_specialist.py` (lines ~415–423)

Still contain:

```python
from models.state import SeedRecord
payload["seed_record"] = SeedRecord(...)
```

`SeedRecord` no longer exists. Import is lazy (inside the single-match branch), so module import succeeds and **pytest stays green**, but any invocation that hits that branch through these committed modules will fail.

**Fix:** Regenerate all four from updated `specialist_agent.py.j2` (same approach as slice `2026-06-09-1605-entity-boundary-regen-framework-specialists`), or mechanical replace to `IdentityRecord` / `identity_record`.

**Guard:** Add a smoke test that `rg 'SeedRecord|seed_record' src/agents/specialists/` is empty, or that each committed framework specialist completes a single-match `_minimal_state` invoke without error when loaded via `importlib` from `agents.specialists.<name>` (not factory tmp render).

**Queue:** `prompts/cursor/next/2026-06-10-entity-identity-vocabulary-rename-fix.md` (before commit).

---

## Non-blocking (Grok + Paul on commit / polish)

| ID | Item | Action |
|----|------|--------|
| N1 | `README.md` line ~333 still lists `SeedRecord` | One-line rename to `IdentityRecord` when batching commit |
| N2 | `output.md` grep verification overstated | Fix slice should re-run `rg` including `src/agents/specialists/` |
| N3 | Prompt mentioned `context['identity']` key | Implementation correctly uses `entity_id`/`bind` via `planner_context` — no change needed; note in commit message |
| N4 | `dispatch.py` touched per grep but not listed in output table | Cosmetic doc only |

---

## Breaking-change reminders (for Paul)

- MCP clients: `mycelium://schema/seed-record` → `mycelium://schema/identity-record`
- LangGraph checkpoints: fresh `thread_id` after upgrade
- **Do not commit until B1 fix is reviewed**

---

## Suggested commit message (after fix)

```
Breaking: rename SeedRecord to IdentityRecord and seed_* state fields.

Registry identity vocabulary; MCP schema identity-record; matched_records
canonical; regen framework specialists.
```