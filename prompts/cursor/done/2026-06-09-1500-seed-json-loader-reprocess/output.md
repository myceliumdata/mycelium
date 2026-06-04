# Reprocess: Slice 1500 — seed-json-loader

**Claimed:** `prompts/cursor/in-progress/2026-06-09-1500-seed-json-loader-reprocess/prompt.md`

## Summary

Restored the seed-data-context loader slice after backout:

- **`data/seed.json`** — exact copy of the `people` array from `data/seed_crm.json` (457 records).
- **`src/agents/seed.py`** — `SeedData`, `get_seed_data` / `reset_seed_data`, uuid5 `person_id`, `find_by_key`, `MYCELIUM_SEED_PATH`.
- **`src/storage/core.py`** — `auto_seed=False` by default; docstring notes people seeding moved to `agents.seed`.
- **`tests/conftest.py`** — `reset_seed_data` in session cleanup.
- **`tests/test_core_graph.py`** — fixture seeds SQLite explicitly, loads seed loader from tmp `MYCELIUM_SEED_PATH`.

**person_id:** `uuid.uuid5(NAMESPACE_DNS, "mycelium-seed-v1:{seed_id or name|employer}")`

## Verification

```text
$ uv run pytest -m smoke -q
28 passed, 9 deselected in 1.55s

$ uv run pytest -m full -q -k "query_existing_person or query_missing_person or query_non_core_attributes"
3 passed, 34 deselected in 0.11s
```

### Manual loader

```text
count 457
person_id <uuid>
idempotent True
name match 1 Nichanan Kesonpat
env isolated 1 Only One
```

```text
$ uv run ruff check src/agents/seed.py src/storage/core.py tests/conftest.py tests/test_core_graph.py
All checks passed!
```

## git diff --stat (slice files)

```
 data/seed.json            | (new, 457 people)
 src/agents/seed.py        | (new)
 src/storage/core.py       | docstring + auto_seed=False
 tests/conftest.py         | reset_seed_data
 tests/test_core_graph.py  | seed loader in fixture
```

## Scope confirmation

Only slice 1500 work — no state model, supervisor seed routing, or response unification (later reprocess prompts).

**Ready for next slice:** `2026-06-09-1510-state-model-context-reprocess.md`
