# Slice 1720 — Eliminate legacy id from seed transform (reprocess)

## Claim

Moved `prompts/cursor/next/2026-06-09-1720-eliminate-id-from-seed-transform-reprocess.md` → `prompts/cursor/in-progress/.../prompt.md`, then delivered here.

## Summary

Introduced `data/prepare_seed.py` to build `data/seed.json` from `seed_crm.json` with **name + employer only** (no `"id"` keys). Regenerated committed `seed.json` (457 people). Loader assigns `person_id` via uuid5(name|employer); public `results["id"]` and `results["person_id"]` are that UUID. `find_by_key` resolves by UUID or name. Legacy `person-0001`-style keys no longer match.

**Note:** `person_id` values changed from the pre-1720 formula (which used legacy seed ids). Specialist storage keyed by old UUIDs may need `./bin/reset-mycelium --specialists` if stale.

## Scoped changes

| File | Change |
|------|--------|
| `data/prepare_seed.py` | **New** — CRM → seed transform (strips `id`) |
| `data/seed.json` | Regenerated without `id` fields |
| `src/agents/seed.py` | No `seed_id`; uuid from name\|employer; lookup by `person_id` or name |
| `src/agents/supervisor.py` | Public `id` = `person_id` UUID |
| `src/agents/specialists/*` + template | Identity builders use UUID for `id` |
| `src/storage/core.py` | `seed_from_file` assigns UUID when row has no `id` (test fixture compat) |
| `tests/test_core_graph.py`, `tests/test_trace_capture.py` | Fixtures omit `id`; lookup by name; assert `id` == `person_id` |
| `docs/architecture.md`, plan doc | Seed shape + public id semantics |

## Verification

```text
$ python data/prepare_seed.py
Wrote 457 people to data/seed.json (no id fields)

$ python3 -c "import json; d=json.load(open('data/seed.json')); assert not any('id' in p for p in d['people'])"
457 ok no id keys

$ uv run ruff check data/prepare_seed.py src/agents/seed.py src/agents/supervisor.py src/storage/core.py tests/test_core_graph.py tests/test_trace_capture.py
All checks passed!

$ uv run pytest -m smoke -q
23 passed, 11 deselected in 1.06s

$ uv run pytest -m full -q -k "query_existing_person or query_missing_person or query_non_core_attributes or test_results_are_plain_dicts"
4 passed, 30 deselected in 0.17s
```

### Manual CLI

```text
$ uv run mycelium query --person-key "Nichanan Kesonpat"
results[0].id == results[0].person_id == "b08b24db-6231-5ad8-aca1-81a09d052460" (UUID, not person-0001)

$ uv run mycelium query --person-key "Nichanan Kesonpat" --attributes name
message: ... name not currently available ... (via contact_specialist).

$ uv run mycelium query --person-key "Kevin Zhang"
2 results; distinct UUID ids (cbc9a460-..., 17c181b3-...)
```

### grep (transform does not emit id)

`data/prepare_seed.py` — no `"id"` key in output construction (only reads CRM, writes name/employer).

## Scope confirmation

Seed transform + loader + identity builders + tests/docs only. Redesign queue slices **1500–1720** complete.

**Ready for next slice:** All redesign slices through 1720 are done; no further items in `prompts/cursor/next/` for this redesign reprocess queue.
