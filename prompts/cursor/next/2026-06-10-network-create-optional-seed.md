# Task: Network create v2 — optional `--seed`

> **READY** — Paul + Grok agreed June 2026. Move to `in-progress/` before starting.

**Read first:**

- [`docs/plans/network-create-optional-seed.md`](../../docs/plans/network-create-optional-seed.md)
- [`docs/architecture.md`](../../docs/architecture.md)
- [`examples/networks/empty-crm/README.md`](../../examples/networks/empty-crm/README.md) — target empty-network semantics

**Depends on:** `main` green. Runs **after** identity vocabulary rename if that slice is still in queue (filename order: `entity-…` before `network-…`).

---

## Objective

Make `--seed` **optional** on `mycelium network create`. Without it, create behaves like `empty-crm`: ontology + manifest + guide, zero registry rows until query bind.

Keep `refresh-example-network` auto-bootstrap: when the copied example includes `seed.json`, import into `entities.json` without the operator passing any flag.

---

## Requirements

### 1. `network create` — optional `--seed`

- CLI (`src/main.py`): remove `required=True` from `--seed`; update help text.
- `create_network()` (`src/network/create.py`):
  - `seed_path: str | Path | None = None`
  - **With seed:** validate → copy to `<root>/seed.json` → bootstrap import (today’s behavior).
  - **Without seed:** skip seed copy and import; do **not** write `entities.json`.
  - **`--force` without seed:** remove stale `<root>/seed.json` and `<root>/entities.json` if present (empty-network overwrite).
- `CreateNetworkResult`: add `entities_bootstrapped: int` (0 when no seed).
- Dry-run: validate seed only when `--seed` provided; no files written either way.
- CLI stdout: note when no seed bootstrap vs N entities imported.

### 2. Shared seed bootstrap helper

Consolidate duplicate logic in `create.py` and `example.py`:

- Prefer a small helper in `src/network/seed_import.py` (e.g. `bootstrap_seed_at_paths(paths) -> int`) that:
  - calls `apply_network_paths`
  - `reset_entity_registry`
  - `import_seed_file(paths.seed_path)` when file exists
- `create_network` uses it after optional copy.
- `refresh_example_network` uses it after copy when `<live_root>/seed.json` exists.

**Do not** add a `--seed` flag to `bin/refresh-example-network`. Auto-detect from copied `seed.json` only.

### 3. `refresh-example-network` output

When bootstrap runs (or would run on dry-run), print a clear line, e.g.:

```
  seed: seed.json → 15 entities imported
```

Add `seed_bootstrap_count` (or equivalent) to `RefreshExampleResult` for the script to print. Use `-1` or a sentinel on dry-run when seed would be imported, if helpful.

### 4. Tests

Add/update in `tests/test_network_create.py`:

- `test_create_network_without_seed` — no `seed.json`, no `entities.json`, ontology artifacts present.
- `test_create_network_without_seed_dry_run` — validates without writing.
- `test_create_network_force_without_seed_clears_stale_bootstrap` — existing root with seed + entities → force recreate without seed → artifacts removed.

Keep existing seeded create tests green (update call signature if `create_network` arg order changes).

In `tests/test_example_network.py`:

- Assert `refresh` CRM sets `seed_bootstrap_count > 0` (or entities imported).
- Assert `empty-crm` refresh leaves no seed and no entities.

### 5. Docs

- Update `README.md` network-create examples: show both with-seed and without-seed invocations.
- Brief note that `refresh-example-network` auto-imports when example ships `seed.json`.

---

## Out of scope

- `SeedRecord` → `IdentityRecord` rename (queued separately).
- `TODO.md`, `docs/plans/*` historical specs, `prompts/cursor/done/*`.
- Admin UI changes.

---

## Governance (mandatory)

- **Do not edit `TODO.md`.** Roadmap updates are for Grok + Paul after review.
- **Do not create `review.md`.**
- In `output.md`, add **"For Grok + Paul"**: check off Network launch v2 item, README notes.
- Cursor delivers: code, tests, task-scoped docs, and `output.md` only.
- **Do not commit** before Grok + Paul review.

---

## Verify

```bash
uv run ruff check src tests
rg 'required=True' src/main.py  # --seed must not be required
rg 'SeedRecord|seed_records' src/network/create.py  # no accidental rename scope
LANGCHAIN_TRACING_V2=false uv run pytest -q tests/test_network_create.py tests/test_example_network.py
```

Report full pytest count in `output.md`.

---

## Suggested commit message

```
Network create: make --seed optional; unify refresh seed bootstrap.

Empty networks match empty-crm; refresh auto-imports when seed.json
shipped in example; shared bootstrap_seed_at_paths helper.
```