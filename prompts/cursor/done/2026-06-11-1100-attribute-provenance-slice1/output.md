# Program 1 — Attribute provenance Slice 1

## Summary

Introduced `versioned_provenance_v1` for extended specialist attributes. Research and pending writes append or in-place-update `versions[]` per P1-11. Flat v1 field blobs fail loud on validated read paths. Registry attribution uses current version `at` (any status).

## Changes

| Area | Change |
|------|--------|
| **New** | `src/agents/specialist_fields.py` — shared versioned field helpers |
| **Research** | `src/tools/research.py` — version bodies, append/in-place pending, actor metadata |
| **Growth** | `src/agents/entity_growth.py` — `last_researched_at` from `current_version(entry)["at"]` |
| **Strategy** | `src/agents/specialists/base.py` — `versioned_provenance_v1` for new specialist dirs |
| **Read bridge** | Four committed `*_specialist.py` — import `specialist_fields` for versioned read/pending (keeps pytest green; Slice 2 will regen from jinja) |
| **Tests** | `tests/test_specialist_fields.py`, `tests/versioned_storage_fixtures.py`; updated `test_research.py`, `test_supervisor_routing.py` |
| **Docs** | `docs/architecture.md` § Storage — versioned provenance note |

**Untouched (per scope):** `specialist_agent.py.j2`, `introspection.py`, `QueryResponse`, admin-ui, `entities.json` / MVR / `bind_index`.

## Verification

```bash
uv run ruff check src tests bin/          # All checks passed
LANGCHAIN_TRACING_V2=false uv run pytest -q   # 311 passed in 38.28s
```

## For Grok + Paul

- **Slice 1 complete** — versioned write path live; hard cutover (flat v1 raises on `validate_versioned_field`).
- **P1-11 implemented** — pending retry in-place; status transitions append; found preserved on partial errors.
- **P1-10** — registry `last_researched_at` uses current version `at` for found/na/pending.
- **Read-path note:** Committed framework specialists were minimally bridged to `specialist_fields` so the suite stays green with versioned storage. Slice 2 should regen from jinja + update introspection/admin as specced.
- **Operator action:** refresh example networks or delete `agents/<category>/storage.json` — no lazy migration.
- **Not committed** — awaiting Grok review before Slice 2.
