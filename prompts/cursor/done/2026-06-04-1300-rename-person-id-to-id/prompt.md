# Task: Rename `person_id` → `id` everywhere (single canonical identifier)

**Created:** 2026-06-04

**Runs before:** `2026-06-04-1400-filter-query-results-and-trace-url.md` (queue sorts by filename; claim this task first).

---

## Objective

Use **`id`** as the only name for a person’s stable UUID across the codebase — internal state, seed enrichment, specialist storage/contribs, graph fields, tests, and docs. Remove **`person_id`** as a parallel field (it is always identical to `id` today).

Do **not** change UUID generation logic (`uuid5` from `name|employer` in `seed.py`).

---

## Read first

- `prompts/system/CORE_PROMPT.md`, `docs/architecture.md`
- `prompts/cursor/WORKFLOW.md`, `.cursor/rules/04-cursor-workflow.mdc`
- `src/agents/seed.py`, `src/models/state.py`, `src/agents/supervisor.py`, `src/agents/context.py`, `src/agents/dispatch.py`
- `src/agents/factory/templates/specialist_agent.py.j2` — then **regenerate** committed specialists if the template changes (existing repo pattern; see `agent_factory` / prior regen slices)
- `tests/test_core_graph.py`, `tests/test_agent_factory.py`

---

## Rename map (apply consistently)

| Current | Target |
|---------|--------|
| Seed: `person_id` on enriched dicts | `id` |
| `SeedData.by_person_id` | `by_id` |
| `_assign_person_id()` | `_assign_id()` (or inline; keep behavior) |
| `find_by_key` matching on `person_id` | match on `id` |
| `Person.person_id` field | **Remove** — use `Person.id` only |
| `MyceliumGraphState.current_person_id` | `current_id` |
| `matched_persons[].person_id` | `matched_persons[].id` |
| `specialist_contrib["person_id"]` | `specialist_contrib["id"]` |
| `_resolve_person_id()` in specialists | `_resolve_id()` |
| Comments/docstrings mentioning `person_id` | `id` |
| `PersonQuery.person_key` description “person_id” | “person UUID (`id`)” |

**Specialist `storage.json`:** Records are keyed by UUID string at `records[<uuid>]`. Keys stay as UUIDs; only **code and contrib dict field names** change, not on-disk key structure unless code reads a nested `"person_id"` field (grep and fix).

**Out of scope:** `LANGCHAIN_*`, `thread_id`, `trace_id`, renaming `person_key` on `PersonQuery` (still the lookup string; may be name or UUID).

---

## Files to touch (non-exhaustive — grep `person_id` and fix all)

- `src/models/state.py`
- `src/agents/seed.py`, `supervisor.py`, `context.py`, `dispatch.py`, `person_prep.py`, `enrich.py`
- `src/storage/core.py`
- `src/agents/factory/templates/specialist_agent.py.j2`
- All `src/agents/specialists/*_specialist.py` (regen from template if template changed)
- `tests/*.py` with `person_id` assertions
- `docs/architecture.md`, `docs/plans/seed-data-context-architecture.md` (living docs only; skip `prompts/cursor/done/` history)

---

## Verification

```bash
uv run ruff check src tests
uv run pytest -m smoke -q
# Grep should find no person_id in src/ or tests/ (except comments explaining migration?)
rg 'person_id' src tests docs/architecture.md docs/plans/seed-data-context-architecture.md
```

Manual:

```bash
uv run mycelium query --person-key "Nichanan Kesonpat"
```

Confirm `results` records use **`id`** only (no `person_id` key). Attribute-filter behavior is **not** required in this slice — that is the 1400 task.

---

## Deliverables (WORKFLOW.md)

1. Claim: move to `prompts/cursor/in-progress/2026-06-04-1300-rename-person-id-to-id/prompt.md`
2. Done: `prompts/cursor/done/2026-06-04-1300-rename-person-id-to-id/` with `prompt.md`, `output.md` (summary, diff stat, grep proof, test output)
3. No `review.md`

---

## Success criteria

- [ ] No `person_id` field in `Person`, public `results`, `matched_persons`, or `specialist_contrib`
- [ ] Graph state uses `current_id`; seed loader sets `id` on enriched records
- [ ] All smoke tests pass; ruff clean
- [ ] Specialist template + generated agents aligned
- [ ] Architecture docs describe `id` as the stable UUID (not `person_id`)