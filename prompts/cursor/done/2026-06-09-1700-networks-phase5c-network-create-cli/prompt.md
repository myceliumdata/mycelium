# Task: Networks Phase 5c — `mycelium network create` CLI

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- `docs/plans/networks-phase5.md` (full create flow)
- `src/main.py` (existing `network` subcommands)
- `src/network/ontology.py` (from 5b)
- `src/network/registry.py`, `src/network/paths.py`
- `src/agents/factory/agent_factory.py` (`render_specialist_py`, `create_specialist`)
- `src/agents/specialists/base.py` (`SpecialistStorage`)
- `tests/test_network_integration.py`

**Depends on:** 5a (`1500`) + 5b (`1600`) in `prompts/cursor/done/`.

**Blocks:** slice `1800` (docs).

---

## Objective

Implement **`mycelium network create`** — single command to stand up a custom-domain network:

```bash
uv run mycelium network create <name> \
  --root <abs-path> \
  --seed <file> \
  (--prompt "..." | --prompt-file <file>) \
  [--display-name "..."] \
  [--default] \
  [--dry-run] \
  [--force] \
  [--no-mcp-snippet]
```

Subsumes manual `copy-example-network` + `register` for **custom** ontologies. Do **not** remove `register` / `copy-example-network`.

---

## Orchestration

Prefer new module `src/network/create.py` (keeps `main.py` thin) with e.g.:

```python
def create_network(
    name: str,
    root: str | Path,
    seed_path: str | Path,
    creation_prompt: str,
    *,
    display_name: str | None = None,
    default: bool = False,
    dry_run: bool = False,
    force: bool = False,
    print_mcp_snippet: bool = True,
) -> CreateNetworkResult:
    ...
```

### Steps (in order)

1. **Validate** `name` (non-empty; registry-safe slug — document rules in `output.md`)
2. **Resolve** `root` to absolute path; `mkdir -p` if missing
3. **Guard** — if `(root / "network.json").exists()` and not `force` → error
4. **Validate seed** — read JSON; must have `people` list; each row dict with at least `name` (employer optional per seed loader)
5. **Ontology** — `generate_skeleton_ontology(creation_prompt)` from 5b
6. **`--dry-run`** — print summary + ontology JSON to stdout; return without writes
7. **Write artifacts** (non-dry-run):
   - Copy seed → `<root>/seed.json`
   - Write `<root>/categories.json` from ontology
   - Write `<root>/agent_registry.json`
   - `apply_network_paths(NetworkPaths.from_root(root))` before factory work
   - For each registry agent: `SpecialistStorage(category)` + `AgentFactory.render_specialist_py(...)` (do **not** use `create_specialist` auto_commit path; no git commit)
   - Write `<root>/network.json`:

     ```json
     {
       "name": "<name>",
       "display_name": "...",
       "description": "<truncated creation prompt or first line>",
       "created_at": "<ISO8601 UTC>",
       "creation_prompt": "<full prompt>",
       "ontology_model": "gpt-4o-mini"
     }
     ```

8. **`register_network(name, root, default=default)`**
9. **Print summary** — categories count, specialists count, root path, registered name
10. **MCP snippet** (unless `--no-mcp-snippet`) — copy-paste JSON block:

    ```json
    "mycelium-<name>": {
      "command": "uv",
      "args": ["run", "mycelium-mcp"],
      "cwd": "<framework_root>",
      "env": { "MYCELIUM_NETWORK_ROOT": "<absolute root>" }
    }
    ```

    Use `framework_root()` from `network.paths` for `cwd`.

---

## CLI (`src/main.py`)

Add `network create` subparser with flags above. Mutually exclusive `--prompt` / `--prompt-file`. Rich/console messages consistent with existing `network register` style.

Exit codes: `0` success, `2` validation/user error (match existing network commands).

---

## Tests

### `tests/test_network_create.py` (smoke + full)

| Test | Approach |
|------|----------|
| Dry run | Mock `generate_skeleton_ontology`; assert no files written |
| Happy path | Mock ontology (3 categories); assert all artifacts + `specialists/*.py` + registry entry |
| Existing network.json without force | Error |
| Invalid seed | Error before ontology call |
| Force overwrite | With `--force`, replaces ontology files |
| MCP snippet | Captured stdout contains `MYCELIUM_NETWORK_ROOT` |

### Integration (`@pytest.mark.full`)

- Mock ontology returning minimal 2-category tree
- `create_network` → `apply_network_paths` → `run_query` with seed person + one requested attribute from examples
- Assert no `_SEED_CATEGORIES` CRM fallback (categories file content matches mock)

Use isolated `MYCELIUM_NETWORKS_CONFIG` like `test_network_integration.py`.

**Do not** require real `OPENAI_API_KEY` in automated tests.

---

## Verification

```bash
uv run pytest -m smoke -q tests/test_network_create.py
uv run pytest -m full -q tests/test_network_create.py
uv run pytest -m smoke -q
uv run ruff check src tests bin/
```

`output.md` must include a **manual checklist template** for Paul (real `OPENAI_API_KEY` create + query) — **not a merge blocker**. Paul will run hands-on testing **after slice `1800`**, not during 5c.

---

## Scope boundaries

**May modify:** `src/main.py`, new `src/network/create.py`, `tests/test_network_create.py`, minimal test helper exports

**Out of scope:** README/TODO/terminology docs (slice `1800`), query-as-seed, per-network credentials, `network regen-ontology`, changing CRM example layout, non-person seed schema

---

## Deliverables

`prompts/cursor/done/2026-06-09-1700-networks-phase5c-network-create-cli/` with `prompt.md`, `output.md`, manual checklist.