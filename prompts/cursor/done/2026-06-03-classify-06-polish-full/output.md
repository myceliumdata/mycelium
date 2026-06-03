# classify-06-polish-full — Output

## Summary

Final Phase 1 polish slice completed:

1. **Atomic `_save`** in `src/agents/classification/engine.py` — `tempfile.mkstemp` + `os.replace` (small diff).
2. **`docs/architecture.md`** — supervisor bullets corrected; 1–2 sentence Classification Engine paragraph under Derivative / Non-Core Data; last-updated note.
3. **Skipped** optional `src/agents/__init__.py` re-export (low priority; imports stay via `agents.classification`).
4. **Full verification matrix** from `docs/plans/classification-engine-phase1.md` — all automated and manual checks green.

Slices 01–05 behavior preserved. Phase 1 Classification Engine is complete per the approved plan.

## Polish diffs (this slice only)

- `src/agents/classification/engine.py`: `import tempfile`; atomic `_save`; module docstring update.
- `docs/architecture.md`: classification integration sentences + supervisor accuracy fix.

## Ruff

```
$ uv run ruff check src/agents/classification src/agents/supervisor.py src/agents/core_data.py src/models/state.py tests/test_supervisor_routing.py tests/test_core_graph.py tests/conftest.py
All checks passed!
```

## Automated tests

### Smoke

```
$ uv run pytest -m smoke -q
.................                                                        [100%]
17 passed, 9 deselected in 0.06s
```

### Full targeted

```
$ uv run pytest -m full -q -k "non_core or query_non_core or supervisor or classify"
..                                                                       [100%]
2 passed, 24 deselected in 0.07s
```

### Refresh smoke (off-path merge + early return)

```
$ uv run pytest -m smoke -q -k "refresh_from_llm"
..                                                                       [100%]
2 passed, 24 deselected in 0.06s
```

## No hot-path LLM guarantee

Workspace is not a git repo; used `grep` equivalent to plan’s `git grep`:

```
$ grep -rn "ChatOpenAI\|refresh_from_llm" src/agents/supervisor.py src/agents/core_data.py src/graphs/ src/mycelium_mcp/ src/main.py src/models/
(exit 1 — zero matches)
```

Hits only in `src/agents/classification/engine.py`:

- Line 3, 18: docstring / comment
- Line 164: `def refresh_from_llm`
- Lines 191–193: lazy `ChatOpenAI` import inside `refresh_from_llm` only

`core.py` `graph.invoke` is LangGraph routing, not LLM.

## Manual hot-path (CLI, `MYCELIUM_USE_SYNC_CHECKPOINTER=1`)

### Core only

```json
{
  "results": [{"id": "person-0001", "name": "Nichanan Kesonpat", "employer": "1k(x)"}],
  "message": "Found core record for Nichanan Kesonpat.",
  "debug": "person_key='Nichanan Kesonpat'; requested_attributes=[]; outcome='found'; num_matches='1'",
  "trace_id": "019e8ce8-2d41-7c70-b315-83d7746482ce",
  "thread_id": "ebb59832-0ecc-447d-b14d-6d3d2676d86c"
}
```

### Non-core email — classifications in debug

```json
"debug": "... outcome='non_core_requested'; ... classifications=[{'attribute': 'email', 'category': 'contact', 'assigned_agent': 'contact_specialist', ... 'confidence': 0.95}]"
```

### Non-core spouse

```json
"classifications=[{'attribute': 'spouse', 'category': 'relationships', 'assigned_agent': 'relationships_specialist', ... 'confidence': 0.95}]"
```

### Unknown `weird_attr` — confidence 0.0

```json
"classifications=[{'attribute': 'weird_attr', 'category': 'unknown', 'assigned_agent': None, ... 'confidence': 0.0}]"
```

### Ambiguous Kevin Zhang + x_handle — 2 results + social classification

```json
{
  "results": [
    {"id": "person-0058", "name": "Kevin Zhang", "employer": "Bain Capital Ventures"},
    {"id": "person-0438", "name": "Kevin Zhang", "employer": "Upfront Ventures"}
  ],
  "message": "We have 2 core records for 'Kevin Zhang', but we're still researching x_handle.",
  "debug": "... num_matches='2'; classifications=[{'attribute': 'x_handle', 'category': 'social', 'assigned_agent': 'social_specialist', ... 'confidence': 0.95}]"
}
```

## MCP path

```python
query_person(json.dumps({"person_key": "Nichanan Kesonpat", "requested_attributes": ["linkedin", "spouse", "weird"]}))
```

Response: core record + message mentions linkedin, spouse, weird; debug includes three `classifications` entries (social, relationships, unknown).

## Test isolation & cache

### `MYCELIUM_CATEGORIES_PATH` override

```
path: /var/folders/.../categories.json
exists: True
email: contact 0.95
```

Fresh temp path → seed written → classify works.

### Delete `data/categories.json` (restored after)

```
after delete classify email: contact 0.95
file recreated: True
restored committed categories.json
```

Embedded seed fallback + file rewrite confirmed.

## Off-path LLM refresh

- Early return: `{'added_categories': [], 'updated_attributes': [], 'skipped': [], 'reason': 'all already known'}`
- Mock merge: covered by `test_refresh_from_llm_merge_with_mock_llm` (smoke) — adds `net_worth` → `financial`, subsequent `classify` sees it.
- No live OpenAI call in matrix (optional manual with key not required for Phase 1 sign-off).

## Observability

- **audit_log**: `test_supervisor_routing` asserts `classified 'email'` in audit; unknown attrs not logged as classified.
- **state.classifications**: supervisor injects; `test_core_graph` / `test_query_non_core_attributes` assert `classifications=` in debug.
- **response.debug**: all manual CLI/MCP runs above show `classifications=[...]`.

## Success criteria (approved plan) — all satisfied

| Criterion | Status |
|-----------|--------|
| Fast `classify()` on hot path (in-memory after load) | Yes |
| Unknown → safe result, confidence 0.0 | Yes |
| Persistent `data/categories.json` + reseed on missing file | Yes |
| LLM never on hot path | Yes (grep + code review) |
| Supervisor injects metadata; route stays `core_data` | Yes |
| Smoke + full targeted + supervisor classify tests green | Yes |
| Ready for Phase 2 (real specialist routing) | Yes |

## Incremental review note

Slices 01–05 were delivered and reviewed in prior `prompts/cursor/done/` tasks. This slice adds polish + runs the complete end-to-end matrix. Recommended next: add `review.md` here, re-run key smoke commands, commit Phase 1 as a series.
