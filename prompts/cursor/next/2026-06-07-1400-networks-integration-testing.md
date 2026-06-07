# Task: Networks Phase 4.5 — integration testing (gate before Phase 5)

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- `docs/plans/networks-terminology.md` (Phases 1–4, testing section)
- `src/network/paths.py`, `src/network/registry.py` (if present)
- `tests/test_network_paths.py`, `tests/conftest.py`
- Phase 1–4 done folders

**Depends on:** Phases 1–4 complete (path resolver, registry, CRM example, no committed `data/seed.json`).

**Do not start** until Phase 4 (`2026-06-07-1300`) is merged and reviewed.

---

## Objective

Serious verification that the **networks stack works end-to-end** before attacking Phase 5 (creation prompt). Find and fix integration bugs within scope; add durable tests so regressions are caught.

Paul explicitly wants this **before Phase 5**.

---

## Test scenarios (minimum)

### 1. Path resolver + legacy

- Unset env/flags → legacy behavior or registered default (per post-Phase 4 layout).
- `--network-dir` overrides registry default.
- `MYCELIUM_NETWORK_ROOT` used by MCP bootstrap.

### 2. Registry + default

- `network register` / `list` / `use`.
- `mycelium query --network <name>` hits correct seed.
- Plain `mycelium query` uses default network.

### 3. Multi-network isolation

- Two temp or example roots with **different** seed content → different query results.
- Use **unique `thread_id` per invocation** (avoid checkpoint cross-talk).

### 4. Example network bootstrap

- Copy `examples/networks/crm/` → temp root → register → query known person.
- Document in `output.md`.

### 5. MCP

- `_bootstrap` + `health_check`: `info.network_root` correct.
- `query_person` reads correct network when `MYCELIUM_NETWORK_ROOT` set.
- (Manual) two MCP config entries with different roots — describe in `output.md`.

### 6. `reset-mycelium`

- Respects active network root; does not touch other networks.

---

## Implementation guidance

- Prefer **new** `tests/test_network_integration.py` (smoke where mocked; `@pytest.mark.full` for real `run_query` with tmp network roots).
- Fix bugs discovered (e.g. checkpoint reuse, path wiring gaps) — keep fixes minimal and in-scope.
- Do **not** implement Phase 5 creation prompt or distributed discovery.
- Polish items from `TODO.md` → Networks polish: **only** if required to make tests pass; otherwise leave for squirt slices.

---

## Verification

```bash
uv run pytest -m smoke -q
uv run pytest -m full -q tests/test_network_integration.py   # if full tests added
uv run ruff check src tests bin/
```

`output.md` must include a **manual checklist** with pass/fail for each scenario above.

---

## Scope boundaries

**May modify:** `tests/`, minimal fixes in `src/network/`, `src/main.py`, `src/mycelium_mcp/server.py`, `bin/reset-mycelium`, docs only if tests reveal doc lies.

**Out of scope:** Phase 5 ontology, distributed discovery, unrelated refactors.

---

## Deliverables

`prompts/cursor/done/2026-06-07-1400-networks-integration-testing/` with `prompt.md`, `output.md`, manual checklist.

**After this slice:** Phase 5 creation prompt may be queued (Grok + Paul).