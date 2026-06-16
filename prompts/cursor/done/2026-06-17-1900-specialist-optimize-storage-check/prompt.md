# Specialist storage — threshold-based `optimize_storage()` check (policy only)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting).

**Program:** Storage evolution (specialist → entity). **Slice 1 of 5.** Map: `docs/plans/storage-evolution-program.md`

| Slice | Owner | Scope |
|-------|-------|-------|
| **1 (this)** | Cursor | Introduce threshold check in base `SpecialistAgent` |
| **2** | Cursor | Implement `migrate_to("minisql_v1")` for specialist storage |
| **3** | Paul + Grok | Re-test baseball/CRM timing (manual) |
| **4** | Cursor | Entity registry storage evolution (queued in `hold/` until slice 3) |
| **5** | Paul + Grok | Re-test timing after slice 4 |

**Context:** `SpecialistAgent` shipped (`prompts/cursor/done/2026-06-17-1800-specialist-agent-class/`). `optimize_storage()` defaults to `False`; `_maybe_optimize_storage()` runs before `write_fields` and swallows `NotImplementedError` from `migrate_to`. Paul wants **per-specialist, threshold-driven** migration in the **base class** — not per-subclass copy-paste. CRM thin subclasses stay unchanged unless opting out.

**This slice:** Policy hook only. **Do not** implement SQLite / `minisql_v1` migration yet (slice 2).

---

## Locked decisions (Paul, June 2026)

| # | Decision |
|---|----------|
| S1 | **Default policy in `SpecialistAgent`**, not in each CRM subclass. |
| S2 | **Per-instance isolation:** each `AGENT` evaluates its own `record_count()` — demographic, contact, etc. migrate independently when they cross the threshold. |
| S3 | **Cheap guard first:** if `storage.current_strategy() != "versioned_provenance_v1"`, return `False` immediately (no full JSON load for count). |
| S4 | **Threshold configurable:** env `MYCELIUM_OPTIMIZE_STORAGE_THRESHOLD` (int, default **50**) + optional class attribute override on subclass. |
| S5 | **Opt-out:** subclass may override `optimize_storage()` to return `False` always (experimental / heterogeneous backends). |
| S6 | **Bootstrap / entity registry out of scope** — specialist `write_fields` / `bootstrap_entity` paths only for the hook (entity store is slice 4). |
| S7 | **Behavior unchanged until slice 2:** crossing threshold may call `migrate_to("minisql_v1")` but must remain a no-op (swallowed `NotImplementedError`). |

---

## Read first

- `prompts/cursor/WORKFLOW.md`
- `docs/plans/storage-evolution-program.md` — program map and locked decisions
- `docs/architecture.md` — specialists own storage; dispatch through agent instances
- `prompts/cursor/done/2026-06-17-1800-specialist-agent-class/prompt.md` + `review.md`
- `src/agents/specialists/agent.py` — `optimize_storage`, `_maybe_optimize_storage`, `record_count`
- `src/agents/specialists/base.py` — `SpecialistStorage.current_strategy()`, `migrate_to` stub
- `tests/test_specialist_agent_class.py` — extend (do not break `MigratingSpecialist` test)

---

## Implement

### 1 — Base `optimize_storage()` policy

In `src/agents/specialists/agent.py`:

```python
def optimize_storage_threshold(self) -> int:
    """Records-at-or-above this count trigger migration (env override)."""
    ...

def optimize_storage(self) -> bool:
    if self.storage.current_strategy() != "versioned_provenance_v1":
        return False
    return self.record_count() >= self.optimize_storage_threshold()
```

- Read threshold from `MYCELIUM_OPTIMIZE_STORAGE_THRESHOLD` with safe int parsing; default `50`.
- Subclass `optimize_storage_threshold()` override is optional (document in architecture addendum).

### 2 — `_maybe_optimize_storage()` unchanged in behavior

- Still calls `migrate_to("minisql_v1")` when `optimize_storage()` is True.
- Still catches `NotImplementedError` until slice 2 lands.

### 3 — Factory template

Update `src/agents/factory/templates/specialist_agent.py.j2` if it duplicates `optimize_storage` — generated specialists inherit base policy; no per-template threshold copy.

### 4 — CRM specialists

**Do not** add per-subclass `optimize_storage` overrides unless needed for tests. Four committed specialists keep thin `run()`-only subclasses.

### 5 — Tests (`tests/test_specialist_agent_class.py` or new `tests/test_specialist_optimize_storage.py`)

| Test | Requirement |
|------|-------------|
| Below threshold | `optimize_storage()` → `False` on fresh tmp store |
| At threshold | `optimize_storage()` → `True` with mocked `record_count` or fixture with N entities |
| Already migrated | When `current_strategy()` returns `minisql_v1`, `optimize_storage()` → `False` **without** calling `record_count` (spy/mock) |
| Write path | Crossing threshold triggers `migrate_to` attempt; `NotImplementedError` swallowed; write still succeeds |
| CRM capstones | `./bin/ci-local` includes capstone/matrix — must stay green |

Use `@pytest.mark.smoke` on new tests.

### 6 — Docs (minimal)

- `docs/architecture.md` short addendum: threshold policy on base `SpecialistAgent`; per-category migration; env knob; subclass opt-out.
- **Do not** edit `TODO.md`.

---

## Out of scope

- `minisql_v1` implementation (slice 2)
- Entity registry / `entities/*.json` (slice 4)
- Baseball bootstrap batch save
- Changing CRM specialist storage schema

---

## Scope boundaries (strict)

**You may modify:**

- `src/agents/specialists/agent.py`
- `src/agents/factory/templates/specialist_agent.py.j2` (only if it duplicates threshold policy)
- `tests/test_specialist_agent_class.py` and/or new `tests/test_specialist_optimize_storage.py`
- `docs/architecture.md` (minimal addendum only)

**Out of scope (do not touch):**

- `TODO.md` (Grok + Paul only)
- `src/agents/specialists/base.py` — `migrate_to` stays `NotImplementedError` until slice 2
- `src/storage/`, `src/agents/entity_registry.py`, bootstrap handlers
- CRM specialist modules — no per-subclass `optimize_storage` unless a test requires it
- Graph nodes, protocol dispatch, registry

If changes outside this scope seem necessary: **stop**, document in `output.md`, do not implement.

---

## Success criteria

1. Base `optimize_storage()` uses strategy guard + threshold + `record_count()`.
2. Env `MYCELIUM_OPTIMIZE_STORAGE_THRESHOLD` works.
3. CRM specialists unchanged (no mandatory subclass overrides).
4. New smoke tests cover below/at/above threshold and already-migrated guard.
5. `./bin/ci-local` green.
6. `test_specialist_agent_class.py` green (including `MigratingSpecialist`).

---

## Deliverables

Per `WORKFLOW.md`:

- `prompts/cursor/done/2026-06-17-1900-specialist-optimize-storage-check/prompt.md`
- `output.md` with verification counts + **For Grok + Paul** (note: enables slice 2; optional pre-slice-2 timing baseline per `docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md`)
- Suggested commit message: `feat(specialists): threshold-based optimize_storage check on base agent`
- **Do not commit or push**

---

## Governance (mandatory)

- **Do not edit `TODO.md`.** Roadmap updates are for Grok + Paul after review.
- In `output.md`, add **"For Grok + Paul"**: slice 2 ready; timing gate notes.
- Cursor delivers: code, tests, task-scoped docs, and `output.md` only.

## When finished (mandatory — see WORKFLOW.md §3)

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-17-1900-specialist-optimize-storage-check/` with `prompt.md` + `output.md`
3. Remove claimed file from `in-progress/` **and** ensure no duplicate remains in `next/`
4. **Do not commit or push** — tell Paul **"slice ready for review"**

---

## Next slice

`2026-06-17-2100-specialist-minisql-v1-migrate.md` (already in `next/`). Program map: `docs/plans/storage-evolution-program.md`.