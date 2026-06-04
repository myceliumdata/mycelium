# Cursor Prompt: Implement reset-mycelium as Python dev/ops script in bin/

## Context and Background
We are in active development of the Mycelium platform. The Agent Factory (Phase 2) generates specialist agents on demand. These land in the source tree at canonical paths:
- `src/agents/specialists/*_specialist.py`
- entries in `data/agent_registry.json` (with `is_generated: true`)
- sidecar data in `data/agents/<category>/{storage.json, storage_strategy.json}`

90% of future development will be on the agents themselves (template changes, scope changes, logic inside specialists). We will regularly "nuke" generated specialists:
- Global changes (template, harness, classification) → use `--all`
- Focused work on one or a few specialists → use targeted `--specialist`

Humans doing real testing use the CLI (`uv run python -m src.main` or equivalent `mycelium` entrypoint), MCP server, and (future) UI/daemon. These all default to **canonical source tree paths**. The `MYCELIUM_*` redirection env vars (MYCELIUM_SPECIALISTS_DIR, MYCELIUM_AGENT_REGISTRY_PATH, MYCELIUM_AGENT_DATA_DIR, MYCELIUM_DB_PATH, MYCELIUM_CATEGORIES_PATH) are excellent for automated tests and isolation but are **not** used by humans in normal interactive work. Humans will not remember to set them.

The old `reload-data` concept is being replaced by a more powerful tool. The tool must:
- Always operate on the **canonical source paths**, deliberately ignoring any `MYCELIUM_*` env var redirections.
- Keep the "trio" in sync when removing generated specialists (no stale registry entries after `git rm` of the .py).
- Perform `git rm --ignore-unmatch` (and `git add` for the registry) so `git status` shows clean, committable deletions.
- Be selective and safe.
- Be a pure dev/ops tool — **not** part of the primary `mycelium` CLI interface (for security: less likely to be invoked by mistake or malice; also keeps main code free of destructive dev-only logic).
- Be simple now. Future requirements (agent-owned DBs, per-specialist reset hooks, staleness detection based on template version, etc.) are unclear. Do not over-engineer. Assume the tool or its contract will evolve or be replaced later.
- Leverage existing code for reseeding and singleton reset (the `reset_*` + `get_*` patterns and Pydantic models), but do the destructive path resolution and pruning inside the script.

The script must add **zero complication** to the main library or CLI code. Do not edit `src/main.py`, do not add a subcommand, do not change `src/agents/registry.py`, `src/agents/factory/...`, classification, or storage. All logic stays in the new bin/ script. Use the exported models (`RegisteredAgent`, `AgentRegistryData`) and the `reset_*` / `get_*` functions for reseeding and cleanup, but bypass the env-aware default path helpers for the reset operations themselves.

Previous implementation work on this idea has been discarded. Implement cleanly from scratch.

## Exact Requirements for the Script
Create a single file: `bin/reset-mycelium`

- Make it a proper Python script:
  - `#!/usr/bin/env python`
  - At top, do the minimal path hack so it works when invoked directly or via `uv run python bin/reset-mycelium`:
    ```python
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    ```
  - Then normal imports from `agents.*`, `storage.*`, stdlib only (argparse, subprocess, json, shutil, etc.). No new dependencies.

- Use `argparse` for CLI (consistent with `src/main.py`).

- Supported options (exact flags and behavior):
  - `--base`, `-b`: Reset base data (`data/mycelium.db`). After unlink, call `reset_storage()` then `get_storage()` (the latter will reseed from the committed `data/seed_crm.json`).
  - `--categories`, `-c`: Reset `data/categories.json`. After unlink, call `reset_category_tree()` then `get_category_tree()` (re-seeds from embedded seed).
  - `--specialists`, `-s`: Reset **all** generated specialists.
  - `--specialist NAME`: Reset one or more specific specialists. Supports:
    - Repeated: `--specialist foo --specialist bar`
    - Comma list in one: `--specialist foo,bar`
  - `--all`, `-a`: Equivalent to `--base --categories --specialists`.
  - `--dry-run`, `-n`: Print the full plan and what would happen. Perform **no** filesystem changes, no writes, no git commands.
  - `--yes`, `-y`: Skip the interactive confirmation prompt.
  - `--no-git`: Perform filesystem operations only. Skip all `git rm` / `git add`. Still print what git would have done.
  - `-h`, `--help`: Standard help (include good usage examples in the help text).

- Always start by `cd`ing to repo root (using the script location, same as the old bash version did).

- First output a clear plan header:
  ```
  === reset-mycelium ===
    base:        ...
    categories:  ...
    specialists: ...
    specific:    ...
    dry-run:     ...
    git:         ...
  ```

- If no targets specified: print error + usage and exit 1.

- Before any destructive action (unless `--dry-run` or `--yes`): prompt "This will delete selected data and may stage git removals. Continue? [y/N] " and abort on anything but y/Y.

- **Canonical paths only** (hard-code these strings, never call the `_default_*` helpers or rely on envs for the destructive work):
  - DB: `data/mycelium.db`
  - Categories: `data/categories.json`
  - Registry: `data/agent_registry.json`
  - Specialists dir: `src/agents/specialists`
  - Agent data root: `data/agents`

- **Base data handling**:
  - If requested: `Path("data/mycelium.db").unlink(missing_ok=True)`
  - Then (not in dry): `reset_storage()`; `get_storage()` (the get will trigger reseed).

- **Categories handling**:
  - If requested: `Path("data/categories.json").unlink(missing_ok=True)`
  - Then (not in dry): `reset_category_tree()`; `get_category_tree()`

- **Specialists handling** (the key sync part):
  - Collect names to remove:
    - If `--specialists`: 
      - Read the registry (using canonical path + `AgentRegistryData.model_validate` or direct load) and take all non-`core_data` names.
      - Also scan `src/agents/specialists` for any orphan `*_specialist.py` files (even if not in registry).
    - If specific `--specialist` values: exactly those names (dedup, case sensitive, preserve order or sort for determinism).
  - Prune the registry **safely using the Pydantic models** (no direct string hacking that could corrupt the file):
    - Load the current registry JSON at the canonical path.
    - Use `AgentRegistryData.model_validate(...)`.
    - Keep `core_data` (if present) + any agents whose name is **not** in the remove list.
    - Update `last_updated` to now (UTC).
    - Serialize with `model_dump_json(indent=2)` and write back to the canonical path.
    - This must work even if the registry only contains `core_data`.
  - Collect categories that need their `data/agents/<cat>/` tree removed:
    - For every removed specialist that had a `category` in the (old) registry entry.
    - Plus: after pruning, any subdir under `data/agents/` whose name does not correspond to any remaining specialist's category (handles orphans like a stray `contact/` dir).
  - For every specialist name being removed:
    - The .py: `src/agents/specialists/<name>.py`
  - Perform the actual removals (or simulation in dry-run):
    - Use `git rm -f --ignore-unmatch <path>` (or `-r` for directories) for the .py files and the `data/agents/<cat>` trees.
    - Also do `shutil.rmtree` / `unlink` as fallback (for untracked files or when `--no-git`).
    - After the registry write: `git add data/agent_registry.json` (unless `--no-git` or dry).
  - If a path doesn't exist, the git command with `--ignore-unmatch` is harmless.
  - Print clear per-item messages ("registry entry removed: foo", "cleaning data dir: data/agents/bar", "cleaning specialist py: ...").

- After any specialists work (or at the very end if base/categories were touched), always reset the relevant singletons (so the *current* process and the next fresh CLI/MCP invocation see the clean state):
  ```python
  from agents.registry import reset_agent_registry
  from agents.factory.agent_factory import reset_agent_factory
  from agents.classification import reset_category_tree
  from storage.core import reset_storage
  reset_agent_registry()
  reset_agent_factory()
  reset_category_tree()
  reset_storage()
  ```

- In dry-run mode: never write files, never unlink, never run git. Print "(would ...)" versions of every action. Still compute the exact set of names/cats that would be affected.

- Git operations must be robust:
  - Use `subprocess.run(["git", "rm", ...], check=False)` so `--ignore-unmatch` failures don't kill the script.
  - If not inside a git repo, still do the fs operations and print a warning.
  - Capture output only for logging if useful; keep output clean.

- Output at the end (always, even in dry-run):
  ```
  Done.
  Run: git status
  Commit the cleanups if desired, or 'git checkout -- .' to revert this reset.
  ```
  (Adjust wording slightly for dry-run: "would have staged...")

- Excellent `--help` text with examples:
  ```
  bin/reset-mycelium --dry-run --all
  bin/reset-mycelium --specialist financial_specialist
  bin/reset-mycelium --specialists --yes
  bin/reset-mycelium --base --categories
  bin/reset-mycelium --specialist demographic_specialist,financial_specialist --no-git
  ```

- Make the script executable after creation (`chmod +x bin/reset-mycelium`).

- Keep the implementation small, readable, and robust. Use `pathlib.Path` everywhere. Handle missing files gracefully (`missing_ok=True`, `exists()` checks).

## Strict Guards (do not violate)
- **Only edit/create the single file `bin/reset-mycelium`**. Do not touch any file under `src/`, `tests/`, `docs/`, `pyproject.toml`, or anywhere else. No new tests, no updates to architecture docs, no changes to the agent template, no additions to `AgentRegistry` (even a `remove_agent` method), no subcommand in `main.py`.
- Do not introduce new dependencies.
- Do not make the script sensitive to `MYCELIUM_*` vars for its destructive work (the whole point).
- Do not call `get_agent_registry()` / `get_agent_factory()` etc. to discover paths during the reset phase (they would respect envs). Instantiate `AgentRegistry(registry_path=...)` only if you need the model helpers, but prefer loading via the Pydantic models directly for the prune to stay self-contained.
- After your changes, `git diff --stat` must show **only** the new `bin/reset-mycelium` file.
- The script must remain a pure dev tool. No attempt to make it part of the public interface.

## Verification Steps (run these after you finish and include the output)
You must execute the following verification sequence yourself (using the terminal) and paste the key output + final `git diff --stat` into your response:

1. `chmod +x bin/reset-mycelium`
2. `./bin/reset-mycelium --help` (show the full help text)
3. `./bin/reset-mycelium --dry-run --specialist demographic_specialist` (or any current generated one; adjust name if none exist — first run a query that triggers creation if needed, but prefer using existing state)
4. `./bin/reset-mycelium --dry-run --all`
5. `./bin/reset-mycelium --specialist <one-existing> --yes --no-git` (use a real generated specialist name from current tree)
   - After: show `ls src/agents/specialists/*_specialist.py`, contents of `data/agent_registry.json` (should still have core_data + any non-removed), `ls data/agents/`, and `git status --short -- data/agent_registry.json src/agents/specialists/ data/agents/`
6. Restore the state you just changed (use `git checkout --` on the affected paths) so the tree is back to its pre-run condition for the next steps.
7. `./bin/reset-mycelium --all --yes --no-git`
   - After: verify only `core_data` remains in registry, zero `*_specialist.py`, `data/agents/` empty (or only non-generated dirs if any), `git status` shows the expected unstaged changes.
8. Restore again with `git checkout --`.
9. `./bin/reset-mycelium --base --categories --yes --no-git` (quick sanity that base/categories paths are handled)
10. Final: `git diff --stat` (must show **only** the bin/ file) and a clean summary that the script works for both surgical and global cases without touching any main source code.

If any step fails or produces surprising output, fix the script and re-run the verification.

## Success Criteria
- The script is pleasant to use for the described agent dev cycles.
- It never leaves the registry out of sync with the filesystem after a specialists reset.
- Git operations produce clean, reviewable changes.
- It is safe by default (dry-run + confirmation) and explicit about what it will touch.
- It can be run from any subdirectory.
- No side effects on the main codebase.
- Future evolution (when agent reset hooks exist) can be done by editing only this one file or replacing it.

Implement the script now. When complete, run the full verification sequence above and report the results + the diff stat.