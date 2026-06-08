# Task: Retire repo-root `data/` shim — fail loud + Studio wiring

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- `docs/architecture.md` → Networks, framework credentials vs network data
- `docs/plans/networks-terminology.md` (Phase 4: no committed repo-root `data/`)
- `src/network/paths.py` (`resolve_network_root`, `NetworkPaths`, `apply_network_paths`, `NO_NETWORK_CONFIGURED_MSG`)
- `.gitignore` (line 18: entire `data/` is gitignored as retired shim)

**Context (Paul, June 2026):** Repo-root `data/` still accumulates runtime artifacts (`categories.json`, `checkpoints.sqlite`, empty `agent_registry.json`) when code falls back to hardcoded `data/...` defaults without network resolution. **Nothing** belongs there anymore — all runtime artifacts live under `<network_root>/`. LangGraph Studio (`./bin/run-studio`) is a known leak because it imports `get_core_graph` without calling `apply_network_paths()`.

---

## Objective

1. **Harden path resolution** so unconfigured processes fail loud (same message as `resolve_network_root`) instead of silently writing under repo-root `data/`.
2. **Wire Studio** (and any other entry points that bypass CLI/MCP/admin bootstrap) to resolve the active network and set `MYCELIUM_*` paths before graph import.
3. **Add tests** proving the hardening behavior.
4. **Document** the retirement in README (brief note; no new markdown files unless essential).

**Out of scope:** Deleting Paul's local `data/` directory (operator cleanup only — not in repo). Do not edit `TODO.md`.

---

## Implementation plan

### 1. Centralize runtime path resolution (`src/network/paths.py`)

Add a single helper, e.g. `runtime_path(env_var: str) -> Path`, mapping env vars to `NetworkPaths` fields:

| `env_var` | `NetworkPaths` field |
|-----------|----------------------|
| `MYCELIUM_SEED_PATH` | `seed_path` |
| `MYCELIUM_AGENT_REGISTRY_PATH` | `registry_path` |
| `MYCELIUM_CATEGORIES_PATH` | `categories_path` |
| `MYCELIUM_AGENT_DATA_DIR` | `agents_dir` |
| `MYCELIUM_SPECIALISTS_DIR` | `specialists_dir` |
| `MYCELIUM_CHECKPOINT_PATH` | `checkpoint_path` |
| `MYCELIUM_DB_PATH` | `db_path` |

**Resolution order:**
1. If `env_var` is set and non-empty → use it (expanduser, resolve).
2. Else if `MYCELIUM_NETWORK_ROOT` is set → derive from `NetworkPaths.from_root(...)`.
3. Else call `resolve_network_root()` (registry default / env name) and derive.
4. Else raise `ValueError(NO_NETWORK_CONFIGURED_MSG)`.

Also add `shell_export_network_paths() -> str` (or equivalent) that resolves the active network, calls `apply_network_paths()`, and returns bash `export` lines for all `MYCELIUM_*` path vars — for use by `bin/run-studio`.

Export new helpers from `src/network/__init__.py` if appropriate.

### 2. Replace hardcoded `data/` fallbacks

Update `_default_*` / `get_storage` / checkpoint resolution to call `runtime_path()` instead of defaulting to `data/...`:

| File | Current fallback |
|------|------------------|
| `src/agents/registry.py` | `data/agent_registry.json` |
| `src/agents/classification/engine.py` | `data/categories.json` |
| `src/agents/seed.py` | `data/seed.json` |
| `src/storage/core.py` | `data/mycelium.db`, `data/seed.json` |
| `src/graphs/core.py` | `data/checkpoints.sqlite` |
| `src/agents/factory/agent_factory.py` | `data/agent_registry.json`, `data/categories.json` |
| `src/agents/specialists/base.py` | `data/agents` |

- Remove `DEFAULT_*_PATH = Path("data/...")` constants where they only existed as silent fallbacks.
- Keep embedded seed constants (`_SEED_REGISTRY`, `_SEED_CATEGORIES`) unchanged — they seed **network_root** files on first use, not repo `data/`.
- Update docstrings/comments that still say `data/agent_registry.json` etc. to say `<network_root>/...` (only in files you touch).

**Do not change** committed specialist reference modules under `src/agents/specialists/` or `examples/networks/crm/specialists/` unless a test requires it — those are historical reference strings.

### 3. LangGraph Studio bootstrap (`bin/run-studio`)

Before starting `langgraph dev`, resolve the active network and export path env vars into the shell, e.g.:

```bash
eval "$(uv run python -c 'from network.paths import shell_export_network_paths; print(shell_export_network_paths())')"
echo "Using network_root: $MYCELIUM_NETWORK_ROOT"
```

If no network is configured, the script should **exit non-zero** with the same guidance as `NO_NETWORK_CONFIGURED_MSG` (do not start Studio against repo `data/`).

### 4. Tests

Add smoke tests in `tests/test_network_paths.py` (or a small dedicated file):

1. **`runtime_path` fails when unconfigured** — clear all `MYCELIUM_*` path vars and registry default; importing/using `runtime_path("MYCELIUM_CHECKPOINT_PATH")` raises with `refresh-example-network`.
2. **`runtime_path` derives from `MYCELIUM_NETWORK_ROOT`** — set only `MYCELIUM_NETWORK_ROOT` to a tmp dir; assert checkpoint/registry/seed paths match `NetworkPaths.from_root`.
3. **`runtime_path` respects explicit env override** — set `MYCELIUM_CATEGORIES_PATH` to a custom path; assert it wins over network_root derivation.
4. **Optional:** assert `graphs.core.build_core_graph` uses network checkpoint when paths applied (may already be covered indirectly — add only if gap is clear).

Ensure existing tests still pass: most already call `apply_network_paths(NetworkPaths.from_root(tmp))` or set per-path env vars in fixtures. Fix any that relied on silent `data/` creation.

### 5. README touch-up (brief)

In `README.md` (Networks / Studio section if present): note that repo-root `data/` is **retired** (gitignored); Studio requires a configured network like CLI/MCP. One short paragraph — no new `data/README.md`.

---

## Scope boundaries

**May modify:** `src/network/paths.py`, `src/network/__init__.py`, path consumers listed above, `bin/run-studio`, `tests/`, `README.md` (brief note only).

**Do not modify:** `TODO.md`, `examples/networks/crm/seed.json`, admin-ui, MCP onboarding beyond what path hardening requires, historical docs under `docs/plans/` (unless a one-line stale reference in README is unavoidable).

---

## Verification

```bash
uv run pytest -m smoke -q
uv run ruff check src tests bin/
```

Manual sanity (document in `output.md`, not automated):
- With default network registered, `./bin/run-studio` prints `network_root` and does **not** create `data/checkpoints.sqlite` in repo root.
- `uv run mycelium query ...` still works against registered default network.

---

## Governance (mandatory)

- **Do not edit `TODO.md`.** Roadmap updates are for Grok + Paul after review.
- In `output.md`, add **"For Grok + Paul"**: suggest checking off any open item about legacy `data/` shim if applicable; note operator can `rm -rf data/` locally.
- Cursor delivers: code, tests, task-scoped docs, and `output.md` only.

---

## Deliverables

Move this file to `prompts/cursor/in-progress/` before starting.

On completion, create `prompts/cursor/done/2026-06-08-2400-retire-data-shim-hardening/` with:
- `prompt.md` (this file)
- `output.md` — summary, checklist, verification results, **For Grok + Paul**