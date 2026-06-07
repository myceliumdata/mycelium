# Task: Networks Phase 5a — per-network `specialists/` + env wiring

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- `docs/plans/networks-phase5.md` (Paul-approved; slice 5a section)
- `src/network/paths.py`, `src/agents/runtime.py`
- `src/agents/registry.py`, `src/agents/factory/agent_factory.py`
- `tests/test_network_paths.py`, `tests/test_network_integration.py` (env helpers)

**Depends on:** Phase 4.5 integration testing (`2026-06-09-1400`) in `prompts/cursor/done/`.

**Blocks:** slices `1600` (ontology), `1700` (`network create`).

---

## Objective

Wire **per-network specialist Python modules** under `<network_root>/specialists/` (not shared `src/agents/specialists/`). Today `apply_network_paths()` sets seed/registry/categories/agents but **not** `MYCELIUM_SPECIALISTS_DIR`, so multiple custom networks would collide on framework specialist files.

This is a **prerequisite** for Phase 5 `network create`; no LLM or new CLI subcommands in this slice.

---

## Implementation

### `src/network/paths.py`

- Add `specialists_dir: Path` to `NetworkPaths` → `<root>/specialists`
- `NetworkPaths.from_root()` populates it
- `apply_network_paths()` sets `MYCELIUM_SPECIALISTS_DIR` to `str(paths.specialists_dir)`

### `src/agents/runtime.py`

- Add `MYCELIUM_SPECIALISTS_DIR` to `_NETWORK_PATH_ENV_KEYS` so MCP `refresh_runtime_from_disk()` preserves it across `load_dotenv(override=True)` (same pattern as other network path vars)

### `src/agents/factory/agent_factory.py`

- Fix `RegisteredAgent` paths in `create_specialist()` — **do not hardcode** `data/agents/{category}/`:
  - Derive from `MYCELIUM_AGENT_DATA_DIR` (same slug logic as `SpecialistStorage._slug`)
  - `storage_path` / `strategy_path` must be network-relative strings that resolve under active `network_root` when env is set
- No behavior change to `auto_commit` defaults

### Docs in code only (if needed)

- One-line comment in `paths.py` standard layout docstring: `specialists/` for generated `*_specialist.py`

---

## Tests

Extend `tests/test_network_paths.py` (smoke):

- `NetworkPaths.from_root` includes `specialists_dir == root / "specialists"`
- `apply_network_paths` sets `MYCELIUM_SPECIALISTS_DIR` in env

Add isolation test (smoke or `@pytest.mark.full`):

- Two temp `network_root`s; `apply_network_paths` for each in sequence (clear env between)
- `AgentFactory` with `auto_commit=False` creates different `foo_specialist.py` under each root's `specialists/`
- Assert files differ and registry `get_agent_fn` loads from the active root's dir

Reuse patterns from `tests/test_agent_factory.py` and `tests/test_network_integration.py` (`_clear_network_path_env`, registry resets).

---

## Verification

```bash
uv run pytest -m smoke -q tests/test_network_paths.py
uv run pytest -m smoke -q   # full smoke suite
uv run ruff check src tests bin/
```

---

## Scope boundaries

**May modify:** `src/network/paths.py`, `src/agents/runtime.py`, `src/agents/factory/agent_factory.py`, `tests/test_network_paths.py`, (+ new test file only if cleaner)

**Out of scope:** `network create` CLI, ontology LLM, `src/network/ontology.py`, docs/README/TODO (slice `1800`), changing `copy-example-network`, moving committed CRM specialists out of `src/agents/specialists/`

---

## Deliverables

`prompts/cursor/done/2026-06-09-1500-networks-phase5a-specialists-dir/` with `prompt.md`, `output.md`.