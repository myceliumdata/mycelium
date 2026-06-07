# Task: Networks Phase 5 polish — review niggles before docs (5d)

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- `docs/plans/networks-phase5.md`
- `prompts/cursor/done/2026-06-09-1500-networks-phase5a-specialists-dir/review.md` (5a niggles)
- `prompts/cursor/done/2026-06-09-1600-networks-phase5b-ontology-generator/review.md` (5b niggles)
- `prompts/cursor/done/2026-06-09-1700-networks-phase5c-network-create-cli/output.md` and `review.md` (5c niggles)
- `bin/reset-mycelium`, `src/agents/factory/agent_factory.py`
- `tests/test_network_paths.py`, `tests/test_network_integration.py`, `tests/conftest.py`

**Depends on:** Phase 5c (`2026-06-09-1700`) in `prompts/cursor/done/`.

**Blocks:** slice `1800` (docs).

---

## Objective

Close **non-blocking review niggles** from Phase 5a + 5b + 5c in one bounded slice **before** documentation (`1800`). No new features.

---

## Checklist (implement all; tick in `output.md`)

### 1. `bin/reset-mycelium` — per-network `specialists/`

Today `_reset_specialists` hardcodes `src/agents/specialists/` for `.py` cleanup. After 5a/5c, generated modules live under `<network_root>/specialists/`.

- At startup (after `resolve_network_root`), call `apply_network_paths(_network_paths())` so env matches active network.
- Remove specialist `.py` files from `_network_paths().specialists_dir` (not repo-relative `src/agents/specialists/`).
- Update module docstring: framework-committed CRM specialists under `src/agents/specialists/` are **outside** active network reset scope.
- Git staging: only attempt `git rm` when `specialists_dir` is under `REPO_ROOT`; user network roots outside repo → filesystem delete only (mirror existing registry-path logic).
- Add smoke test or extend existing reset test: tmp `network_root` with a dummy `specialists/foo_specialist.py` → dry-run `--specialist foo_specialist` reports correct path.

### 2. Shared test helper — `_NETWORK_PATH_ENV_KEYS`

Duplicated in `tests/test_network_paths.py` and `tests/test_network_integration.py`.

- Extract to `tests/conftest.py` (or `tests/network_helpers.py` if cleaner) as e.g. `NETWORK_PATH_ENV_KEYS` tuple + optional `clear_network_path_env(monkeypatch)`.
- Update both test modules to import shared helper.
- No behavior change.

### 3. Category slug + public registry storage paths (5a + 5b)

`_registry_storage_paths()` in `agent_factory.py` constructs `SpecialistStorage(category)` only to obtain slug. `src/network/ontology.py` imports the private `_registry_storage_paths`.

- Extract shared slug function (e.g. `category_slug(category: str) -> str`) to `src/agents/specialists/base.py`; use in `SpecialistStorage._slug`.
- Promote storage-path builder to a **public** helper (e.g. `registry_storage_paths(category: str) -> tuple[str, str]` in `agent_factory.py` or `base.py`); no mkdir.
- Update `agent_factory.py` and `ontology.py` to use the public helper (remove private import).

### 4. Ontology — skip API key check when `llm=` injected (5b)

`generate_skeleton_ontology()` requires `OPENAI_API_KEY` even when callers pass `llm=` for tests.

- Skip `_validate_openai_api_key()` when `llm is not None`.
- Add/adjust test: mock `llm` works with `OPENAI_API_KEY` unset.

### 5. Ontology validation tests (5b, optional but preferred)

Add smoke tests in `tests/test_network_ontology.py` (mocked LLM):

- Duplicate category keys after slugify → validation error + retry path
- More than 8 categories → validation error

### 6. `network create` polish (5c, optional)

From 5c review — implement if bounded; otherwise document in `output.md` for `1800`:

- **`--dry-run`:** avoid creating empty `network_root` until non-dry-run (or document current behavior).
- **`--force`:** prune orphan `specialists/*.py` not in new `agent_registry.json` before re-render.
- **Atomic writes** for `categories.json` / `agent_registry.json` in `create.py` (match registry engine temp+replace) — optional.

### 7. `output.md` note for 5d

Document reset-mycelium + `network create --force` behavior under per-network layout so slice `1800` can reference in README/architecture (one paragraph; full doc edits stay in `1800`).

---

## Verification

```bash
uv run pytest -m smoke -q
uv run ruff check src tests bin/
```

---

## Scope boundaries

**May modify:** `bin/reset-mycelium`, `src/agents/factory/agent_factory.py`, `src/agents/specialists/base.py`, `src/network/ontology.py`, `src/network/create.py`, `tests/conftest.py` (or `tests/network_helpers.py`), `tests/test_network_paths.py`, `tests/test_network_integration.py`, `tests/test_network_ontology.py`, `tests/test_network_create.py`, minimal reset-related tests

**Out of scope:** README/TODO/terminology bulk updates (`1800`), new CLI flags, ontology/create behavior changes, moving committed CRM `.py` out of `src/agents/specialists/`

---

## Deliverables

`prompts/cursor/done/2026-06-09-1750-networks-phase5-polish/` with `prompt.md`, `output.md` (checklist ticked).