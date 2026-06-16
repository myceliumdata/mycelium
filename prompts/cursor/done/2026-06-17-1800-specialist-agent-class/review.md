# Review: SpecialistAgent class — route all I/O through instances

**Verdict:** **Approved**  
**Reviewer:** Grok  
**Date:** 2026-06-17

---

## Scope checked

Read working-tree diff against prompt `2026-06-17-1800-specialist-agent-class.md`: new `agent.py`, registry `get_agent_instance`, protocol refactor, CRM specialists + factory template, `handlers.py` thin wrappers, `test_specialist_agent_class.py`, architecture addendum.

---

## CI

| Suite | Result |
|-------|--------|
| `./bin/ci-local` (Grok re-run) | **444 passed**, 94 deselected |

Matches Cursor `output.md` claim.

---

## Success criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | `SpecialistAgent` with overridable I/O + `optimize_storage` | ✅ |
| 2 | CRM specialists + template use `AGENT = …Specialist()` | ✅ |
| 3 | `dispatch_write_bind_fields_multi` via agent instances | ✅ (`agent.write_bind_fields_multi`, not protocol→handlers) |
| 4 | `get_agent_instance` on registry | ✅ |
| 5 | CI green | ✅ |
| 6 | Boundary test green | ✅ (included in smoke run) |
| 7 | CRM capstone / Program 2 matrix | ✅ (included in smoke run) |

---

## Architectural assessment

**This delivers the OO migration Paul asked for.** The June 16 boundary slice stopped framework imports of `SpecialistStorage`; this slice gives specialists a **cohesive agent object** with a stable extension point.

**What works well:**

- `SpecialistAgent` centralizes JSON `versioned_provenance_v1` mechanics; subclasses override policy (`optimize_storage`, `migrate_to`, `write_fields`).
- `write_bind_fields_multi` resolves committed module `AGENT` first (bootstrap without premature `agent_registry.json`), then registry — matches output design note.
- Rollback preserved via per-category storage snapshots on agent instances.
- Tests prove subclass `write_fields` runs through dispatch and multi-bind no longer calls `handlers.write_fields`.
- `_maybe_optimize_storage()` swallows `NotImplementedError` until `minisql_v1` slice — safe no-op today.

**Honest limits (non-blocking):**

1. **Dual storage entry in graph nodes.** Research/graph code still uses module-level `get_specialist_storage()` while protocol I/O uses `AGENT.storage` (with env rebinding). Writes from graph research and writes from bind dispatch could theoretically diverge if `MYCELIUM_AGENT_DATA_DIR` changes mid-process. **Follow-up:** graph paths should use `AGENT.storage` and drop parallel `_storage` singletons.

2. **`handlers._agent()` spawns fresh `SpecialistAgent(category, …)`** — not module `AGENT`. OK while protocol avoids handlers on hot paths; `_protocol_exports` fallback without `AGENT` still bypasses user subclasses. Document for factory-generated specialists: always set `AGENT`.

3. **All CRM specialists still share base-class JSON implementation** — correct for this slice; differentiation is override hooks, not distinct storage backends yet.

4. **Entity registry JSON perf unchanged** — baseball bootstrap still slow; enables next specialist SQLite slice only.

---

## Polish nits (non-blocking)

| # | Item | Suggestion |
|---|------|------------|
| N1 | Graph `get_specialist_storage()` vs `AGENT.storage` | Unify on `AGENT.storage` in specialist graph bodies |
| N2 | `handlers._agent` ephemeral instances | Optional: delegate to `get_agent_instance(specialist_name)` |
| N3 | Multi-bind subclass test | Optional: assert `CountingSpecialist.writes` via multi-bind, not only single-field dispatch |

---

## Commit

```
refactor(specialists): SpecialistAgent class; route all I/O through instances
```