# Program 3 — Slice 1540: Legacy test migration and cleanup

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` before starting.

**Program:** [`docs/plans/entity-protocol-legacy-cleanup-program.md`](../../docs/plans/entity-protocol-legacy-cleanup-program.md)  
**Prerequisite:** Slice **1530** approved (legacy graph removed).

---

## Objective

Migrate or delete the **entity_key-era test corpus** so the suite exercises only the target protocol (`lookup` / `id` / `delivery_id`). Remove `MYCELIUM_ALLOW_LEGACY_ENTITY_KEY` from `conftest.py`.

---

## Read first

- [`tests/conftest.py`](../../tests/conftest.py)
- Grep `entity_key` under `tests/` — ~30 files
- High-value modules to migrate or retire:
  - [`tests/test_entity_key_suggestions.py`](../../tests/test_entity_key_suggestions.py)
  - [`tests/test_entity_unknown_mvr.py`](../../tests/test_entity_unknown_mvr.py)
  - [`tests/test_entity_registry_bind.py`](../../tests/test_entity_registry_bind.py)
  - [`tests/test_entity_validation.py`](../../tests/test_entity_validation.py)
  - [`tests/test_entity_research_gate.py`](../../tests/test_entity_research_gate.py)
  - [`tests/test_entity_growth.py`](../../tests/test_entity_growth.py)
  - [`tests/test_entity_metering.py`](../../tests/test_entity_metering.py)
  - [`tests/test_core_graph.py`](../../tests/test_core_graph.py)
  - [`tests/test_mvr_target_resolve.py`](../../tests/test_mvr_target_resolve.py) — `test_legacy_entity_key_still_uses_supervisor_path`

---

## Locked design

### 1. Migration pattern

Replace legacy step-1:

```python
EntityQuery(entity_key="Paul Murphy", binding={"employer": "Acme Corp"})
```

With target step-1:

```python
EntityQuery(lookup={"name": "Paul Murphy", "employer": "Acme Corp"})
```

Two-step flows: step 1 → `delivery_id` → step 2 `EntityQuery(delivery_id=…)`.

Replace `entity_unknown` / `entity_validated` / `entity_key_unresolved` outcome assertions with target outcomes (`lookup_incomplete`, `lookup_suggested`, `lookup_resolved`, `found`, etc.).

### 2. Delete redundant modules

Delete entire test files that **only** test removed legacy behavior with no target-protocol equivalent, e.g.:

- `test_entity_key_suggestions.py` if cases are covered by `test_target_step1_lookup_clarity.py`
- `test_entity_unknown_mvr.py` if superseded by lookup_incomplete / lookup_suggested tests

**Do not delete** coverage without equivalent smoke elsewhere — document merges in `output.md`.

### 3. `conftest.py`

- Remove `MYCELIUM_ALLOW_LEGACY_ENTITY_KEY` default.
- Remove any legacy-only fixtures.

### 4. Registry assertions

Use `bind_values` in JSON assertions (post-1500).

### 5. Status assertions

Use `resolve` / `resolve_matches` (post-1520).

---

## Tests (smoke — mandatory)

- **Zero** remaining `EntityQuery(entity_key=…)` in `tests/` (grep clean).
- **Zero** `MYCELIUM_ALLOW_LEGACY_ENTITY_KEY` in repo (except historical `prompts/cursor/done/`).
- `./bin/ci-local` green.
- Report smoke test count in `output.md`.

Optional: run `uv run pytest tests/ -q --co -q | wc -l` before/after for `output.md`.

---

## Out of scope

- `describe_network` / docs (1550)
- Full integration mark (`full`) — Grok runs at 1550 review

---

## Docs

Do not edit `TODO.md`.

---

## Deliverable

`prompts/cursor/done/2026-06-14-1540-test-migration/` — suggested commit:

```
test: migrate suite to target protocol; remove legacy entity_key tests
```
