# Seed elimination — Slice 17: Delete runtime seed module

**Status:** Ready (June 2026)  
**Depends on:** Slice 16 (no runtime seed reads)  
**Phase map:** [`entity-seed-elimination-phase.md`](entity-seed-elimination-phase.md)

---

## Objective

Remove the runtime seed module and legacy CLI. Tests use bootstrap import helpers only.

---

## Delete

- **`src/agents/seed.py`** — entire module.
- **`mycelium seed`** subcommand in `src/main.py` (parser + handler). Queries never used SQLite seed for identity; remove the command entirely.

---

## `src/storage/core.py`

- Update module docstring: people identity is `entities.json`, not seed.
- `seed_from_file` may remain for explicit SQLite legacy/tests **or** delegate to `import_seed_file` + optional SQLite mirror — prefer **removing** auto coupling; tests should call `import_seed_file` for identity.
- `get_storage(auto_seed=False)` stays default; no seed path requirement at startup.

---

## Test helpers

**`tests/network_helpers.py`:**

- `import_seed_for_test(tmp_path, monkeypatch, seed_src)` — copy + env + `import_seed_file`.
- `import_seed_at_root(root)` — import when `root/seed.json` exists.

Replace all:

- `from agents.seed import ...`
- `get_seed_data()` / `reset_seed_data()`
- `find_by_key` from seed module

Fix any **indentation damage** from bulk edits (lines over-indented after removing `reset_seed_data()`).

---

## `tests/conftest.py`

- Session cleanup: `reset_entity_registry` (not `reset_seed_data`).

---

## Verification

```bash
rg 'agents\.seed|get_seed_data|reset_seed_data|find_by_key' src/ tests/
# expect no matches (except skip reasons / historical docs)
uv run ruff check src tests
uv run pytest -m smoke -q
```

Full suite gate is **Slice 18** exit criteria; run full here if smoke green and changes are broad.

---

## Out of scope

- Admin UI / README (Slice 18).