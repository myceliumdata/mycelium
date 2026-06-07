# Task: Networks alignment — sample categories in docs + polish nits

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- `prompts/cursor/done/2026-06-09-1350-networks-polish/` (output + review context)
- `examples/networks/crm/README.md`, `data/README.md`, `docs/architecture.md`
- `bin/copy-example-network`, `tests/test_example_network.py`, `.gitignore`

**Depends on:** Polish slice `2026-06-09-1350` in `done/`.

**Paul (product):** `categories.json` is a **runtime artifact** (like DB/checkpoints) — **not** committed under `examples/networks/crm/`. Users should see a **sample** in **docs** showing what the classification engine typically creates.

---

## Objective

Align repo, tooling, tests, and docs on the runtime-only `categories.json` policy, add a committed **documentation sample**, and close remaining polish-review nits before integration testing.

---

## Checklist

Implement all items; check them off in `output.md`:

### A. `categories.json` policy (runtime only)

1. **Remove** any `categories.json` (and other runtime artifacts) from `examples/networks/crm/` — committed example ships **`seed.json`** + **`network.json`** only (+ maintainer `README.md`, `prepare_seed.py`).
2. **Add** `docs/examples/sample-categories.json` — stable illustrative taxonomy (six categories + `attribute_map`). Source: copy/sanitize from a typical runtime file or `_SEED_CATEGORIES` in `classification/engine.py`; use a fixed `last_updated` string (not “now”).
3. **Add** brief `docs/examples/README.md` (or a section in `docs/architecture.md`) explaining: runtime `categories.json` lives under `<network_root>/`, is gitignored, and the doc sample shows expected shape after first classification.
4. **Update** `examples/networks/crm/README.md`, `data/README.md`, `README.md`, `docs/architecture.md` — link to `docs/examples/sample-categories.json`; remove any text implying categories is copied from the CRM example or committed there.
5. **`bin/copy-example-network`** — add `categories.json` to skip list (do not copy into user `network_root`).
6. **`.gitignore`** — consolidate example-network rules (remove duplicate/contradictory blocks); gitignore `examples/networks/**/categories.json` and other runtime artifacts; **do not** gitignore `docs/examples/sample-categories.json`.
7. **Tests** — `tests/test_example_network.py` autouse cleanup and layout/copy tests must assert **no** `categories.json` in committed example or copy target; optional smoke test that `docs/examples/sample-categories.json` parses and has expected top-level keys.

### B. Polish-review nits

8. **`mycelium seed`** — add `--network-dir` and `--network` flags (same as `query`) **or** narrow help text to “env/registry/legacy only” if flags are intentionally omitted. Prefer adding flags for parity.
9. **`--seed-path` help** — update arg help (still says “SQLite load”; subcommand help is already clearer).
10. **`docs/plans/networks-terminology.md`** — fix stale status line (“Phases 2–4 queued in next/” → reflect delivered Phases 1–4 + polish).
11. **README Status** — mention polish (`1350`) complete; networks stack ready for integration testing after this slice.

---

## Scope boundaries

**May modify:** `docs/examples/`, `examples/networks/crm/`, `bin/copy-example-network`, `.gitignore`, `tests/`, `README.md`, `data/README.md`, `docs/architecture.md`, `docs/plans/networks-terminology.md`, `src/main.py` (seed CLI only).

**Out of scope:** Phase 4.5 integration test suite (next slice), Phase 5, graph/classification logic changes.

---

## Verification

```bash
uv run pytest -m smoke -q
uv run ruff check src tests bin/
```

Confirm `examples/networks/crm/` contains no `categories.json`, `*.db`, or `*.sqlite` after tests.

---

## Deliverables

`prompts/cursor/done/2026-06-09-1380-networks-categories-sample-and-alignment/` with `prompt.md`, `output.md` (checklist pass/fail).

**Next queue item:** `2026-06-09-1400-networks-integration-testing.md`