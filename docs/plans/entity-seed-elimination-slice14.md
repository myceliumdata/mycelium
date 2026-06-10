# Seed elimination — Slice 14: Bootstrap import

**Status:** Ready (June 2026)  
**Depends on:** Slice 13 (uuid4 + `ensure_bound_entity`)  
**Phase map:** [`entity-seed-elimination-phase.md`](entity-seed-elimination-phase.md)

---

## Principle

`seed.json` is an **optional committed fixture**. It is **not** read at query time. When present at bootstrap, rows are imported into `entities.json` via `ensure_bound_entity` (`source: seed_bootstrap`, `validation_state: validated`). Idempotent via `bind_index`.

| Trigger | Behavior |
|---------|----------|
| `./bin/refresh-example-network <name>` | Copy example files; **if** `live_root/seed.json` exists → `import_seed_file` |
| `mycelium network create` with `--seed` | Copy seed; **if** file exists → `import_seed_file` |
| Query / MCP / admin | **Never** read `seed.json` |

---

## `network/seed_import.py`

```python
def import_seed_file(seed_path: Path, *, registry: EntityRegistry | None = None) -> int
```

- Return `0` when `seed_path` missing (no error).
- Validate JSON shape: `{ "people": [ { "name": str, "employer"?: str }, ... ] }`.
- Each row: `registry.ensure_bound_entity(name, employer, source="seed_bootstrap", validation_state="validated")`.
- Return count of rows processed.
- Raise `ValueError` on invalid JSON (bootstrap is operator-facing).

---

## Call sites

1. **`src/network/example.py`** — end of `refresh_example_network`, after copy, when `live_root / "seed.json"` is a file.
2. **`src/network/create.py`** — after `shutil.copy2` of seed, call `import_seed_file(paths.seed_path)` (only when seed was supplied and copied).

Do **not** add runtime seed reads elsewhere.

---

## Tests (smoke)

- `refresh_example_network("crm", ...)` on empty root → `entities.json` exists with 15 entities (CRM example).
- `import_seed_file` idempotent: second call same count, no duplicate entities.
- `import_seed_file` on missing path → `0`.

---

## Out of scope (Slice 14)

- Removing `agents.seed` / resolution changes (Slices 15–17).
- Admin UI (Slice 18).