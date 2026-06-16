# Network bootstrap specialist — CRM seed path (formal bootstrap phase)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting).

**Context:** Paul + Grok agreed June 2026. CRM seed import works today via `bootstrap_seed_at_paths()` → `import_seed_file()` → `ensure_bound_entity()`, bypassing the query graph. That is acceptable short-term but scattered — baseball cold start needs a **self-contained bootstrap phase** with a clear specialist contract. This slice introduces that phase for **CRM `seed.json` only**; behavior must stay identical so existing smoke/capstone tests remain the regression anchor. Baseball warehouse / multi-grain extension is a **follow-on slice**, not this one.

**Trigger semantics (locked):** Keep current **wipe + refresh** behavior — `refresh-example-network` and `network create --seed` reset registry and re-run bootstrap; no “skip if already populated” logic.

---

## Locked decisions (Paul, June 2026)

| # | Decision |
|---|----------|
| B1 | **Single entry point:** `run_network_bootstrap(paths)` is the formal network data-add path for bootstrap; `bootstrap_seed_at_paths()` becomes a thin wrapper. |
| B2 | **Separate from query graph:** Bootstrap runs at create/refresh (and test helpers that simulate that path), not inside `run_query`. |
| B3 | **CRM behavior unchanged:** 15 seed people, validated rows, `source=seed_bootstrap`, specialist bind writes via existing protocol (`ensure_bound_entity` / `write_bind_fields` / `dispatch_write_bind_fields_multi`). |
| B4 | **Self-contained module:** Bootstrap logic lives under `src/network/bootstrap/` — one place to extend for baseball. |
| B5 | **Extension point now, baseball later:** Optional network override hook (documented + tested with a stub); default handler covers CRM when no override. |
| B6 | **Inputs to bootstrap:** `NetworkPaths`, `network.json` MVR policy, `guide.md` (read when present; CRM default handler may not need it yet but pass it in context). |
| B7 | **No new LLM agent** in this slice — bootstrap “specialist” is a **handler module/protocol**, not an ontology-generated research specialist. |

---

## Read first

- `prompts/cursor/WORKFLOW.md`
- `docs/architecture.md` — § Seed bootstrap, § Specialist I/O protocol, § Data addition
- `src/network/seed_import.py` — current import loop (to relocate, not duplicate)
- `src/network/example.py` — `refresh_example_network` calls `bootstrap_seed_at_paths`
- `src/network/create.py` — `network create --seed`
- `src/agents/attribute_write.py` — bind write + registry sync
- `src/agents/specialists/protocol.py` — `dispatch_bootstrap_entity` (exists; wire default handler through existing bind path unless a clean `bootstrap_entity` per-field path is clearly better without behavior change)
- `tests/test_program2_bootstrap_matrix.py`, `tests/test_example_network_capstones.py`
- `tests/network_helpers.py` — `import_seed_for_test` documents which paths it simulates; update docstring if bootstrap entry moves
- `docs/plans/conversations/2026-06-16-canonical-names-bootstrap-specialists.md` — future baseball direction (do not implement here)

---

## Objective

Introduce a **formal bootstrap phase** with a **bootstrap handler contract**. Rewire CRM seed import to use it. Preserve all external behavior and test outcomes.

**Success in one sentence:** After refactor, `./bin/refresh-example-network crm` and Program 2 bootstrap matrix tests behave exactly as before, but all seed bootstrap logic is reachable through `src/network/bootstrap/`.

---

## Architecture target

```
create / refresh / test bootstrap helper
        │
        ▼
bootstrap_seed_at_paths(paths)          # thin wrapper → int count
        │
        ▼
run_network_bootstrap(paths) → BootstrapResult
        │
        ├─ apply_network_paths
        ├─ ensure_categories_for_mvr_bind
        ├─ reset_entity_registry
        ├─ load guide.md + network.json MVR
        ├─ resolve_handler(paths) → default_seed | network override
        └─ handler.run(ctx) → commits identities + specialist bind writes
```

**Handler contract (sketch — refine naming to match repo style):**

```python
@dataclass(frozen=True)
class BootstrapContext:
    paths: NetworkPaths
    guide_text: str | None
    # registry available via get_entity_registry() after reset

@dataclass
class BootstrapResult:
    entities_committed: int
    sources_processed: list[str]  # e.g. ["seed.json"]
    handler_id: str               # e.g. "default_seed"
    errors: list[str]             # empty on success

def run_network_bootstrap(paths: NetworkPaths) -> BootstrapResult: ...
```

**Default seed handler (`default_seed`):**

- If `paths.seed_path` missing → `entities_committed=0`, no error.
- Parse `seed.json` `people[]` with **same validation** as today (`_load_seed_people` rules: object root, non-empty `name`, string `employer`, all MVR bind fields required).
- For each row: `ensure_bound_entity(..., source="seed_bootstrap", validation_state="validated")` — same idempotency via `bind_index`.
- Return count = rows processed.

**Network override (scaffold only):**

- If `<network_root>/specialists/bootstrap_specialist.py` exists and exposes `run_bootstrap(ctx: BootstrapContext) -> BootstrapResult`, call it instead of default.
- Loader must be safe: import errors → clear `ValueError` with path hint (do not crash refresh opaquely).
- CRM examples do **not** ship an override file; add a **unit test** with a temporary override module in `tmp_path` proving the hook works.

**Do not** add baseball/Lahman logic to the default handler.

---

## Implement

### 1 — `src/network/bootstrap/` package

Suggested layout (adjust if cleaner):

| File | Role |
|------|------|
| `__init__.py` | Export `run_network_bootstrap`, `BootstrapResult`, `BootstrapContext` |
| `run.py` | Orchestration: paths, categories, registry reset, handler resolution, invoke |
| `context.py` | `BootstrapContext`, `BootstrapResult` dataclasses |
| `handlers/default_seed.py` | CRM `seed.json` handler (relocate logic from `seed_import.py`) |
| `handlers/resolve.py` | `resolve_handler(paths) -> Handler` |
| `handlers/protocol.py` | `BootstrapHandler` protocol / callable type |

Keep modules small and readable — Paul wants this **self-contained**.

### 2 — Rewire callers

| Caller | Change |
|--------|--------|
| `bootstrap_seed_at_paths` | Delegate to `run_network_bootstrap(paths).entities_committed` |
| `import_seed_file` | Keep public API for tests; implement via default seed handler **or** delegate to shared handler function (avoid two divergent loops) |
| `count_seed_rows` | Unchanged semantics |

Do **not** change `refresh_example_network` wipe semantics or copy list.

### 3 — `seed_import.py`

- Shrink to thin wrappers + shared validation helpers, **or** re-export from `network.bootstrap` with deprecation comments.
- Update module docstring: bootstrap now goes through `run_network_bootstrap`; this module keeps stable imports for tests.

### 4 — Docs

Update **`docs/architecture.md`** § Seed bootstrap:

- Document bootstrap phase, `run_network_bootstrap`, handler contract, override path.
- Note: bypasses two-step query protocol by design; baseball will extend handlers, not fork refresh.

Optional one-line cross-ref in `examples/networks/crm/README.md` only if it helps operators find the module (keep minimal).

### 5 — Tests

Add **`tests/test_network_bootstrap.py`** (smoke-marked where appropriate):

| Test | Assert |
|------|--------|
| CRM seed via `run_network_bootstrap` | 15 entities, validated, bind index populated |
| Missing seed | `entities_committed == 0` |
| Invalid seed JSON | same `ValueError` messages as today (or equivalent) |
| Missing employer row | `ValueError` |
| Idempotent re-run on same root | duplicate bind returns existing rows; count still reports rows processed (match current `import_seed_file` idempotency) |
| Override hook | tmp_path network with stub `specialists/bootstrap_specialist.py` called instead of default |

**Regression:** `./bin/ci-local` green — especially:

- `test_matrix_a_crm_refresh_seed_bootstrap_storage`
- `test_import_seed_writes_specialist_versions`
- `test_network_create` seed paths
- `test_example_network` refresh/import tests

Do **not** weaken assertions to make refactor pass.

---

## Explicit non-goals

- Baseball / Lahman warehouse ingest
- Multi-grain / multi-registry `entities.json`
- `bootstrap_experiment.py` disposition or wiring
- LLM bootstrap identity discovery
- “First launch only” skip logic
- Query graph changes
- Moving `entities.json` to an identity specialist
- Editing `TODO.md`

---

## Exit criteria

| # | Criterion |
|---|-----------|
| E1 | `run_network_bootstrap` exists and is the sole orchestration path for seed bootstrap |
| E2 | CRM refresh + create `--seed` behavior unchanged (counts, storage, capstones) |
| E3 | `empty-crm` refresh still imports 0 entities |
| E4 | Override hook implemented + tested |
| E5 | `docs/architecture.md` updated |
| E6 | `./bin/ci-local` green |
| E7 | `output.md` includes **For Grok + Paul**: suggested commit message, note that baseball slice should extend `handlers/` not scatter logic |

---

## Completion (Cursor)

Follow `prompts/cursor/WORKFLOW.md` completion checklist:

1. `./bin/ci-local`
2. `prompts/cursor/done/2026-06-16-1700-network-bootstrap-specialist-crm/` with `prompt.md`, `output.md`
3. Do **not** commit or push
4. Tell Paul: slice ready for review

**Suggested commit message (for Grok after approval):**

```
feat(network): formal bootstrap phase with CRM default seed handler

Introduce run_network_bootstrap() and relocate seed import into
src/network/bootstrap/. bootstrap_seed_at_paths delegates to the new
entry point; optional network override hook for future baseball cold start.
```

---

## For Grok + Paul (after review)

- Queue **slice 2** when ready: baseball handler extending same contract (warehouse source, multi-grain) — separate prompt.
- Update `docs/plans/baseball-example-program.md` slice map to reference bootstrap module (Grok doc pass, not required in this slice unless Cursor has spare scope — prefer Grok after approval).