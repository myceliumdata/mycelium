# Research prompts — peer context prominence fix

## Objective

Fix **missing `PEER SPECIALIST FINDINGS` header** in research user messages when peers are present in `context.specialists` JSON but the plain-text block never renders.

**Incident (Paul, June 2026):** After slice `2010`, Angela Murphy @ TalentCare returned correct `na` for `spouse`. LangSmith showed rich peer data in JSON (`contact.email`, `social.twitter`, `demographic.city`) but **no** `PEER SPECIALIST FINDINGS` section at the top. First search and disambiguation worked; peers were buried in JSON only.

**Root cause:** Shape mismatch.

| Producer | `context.specialists` shape |
|----------|----------------------------|
| `build_full_context` / graph | `specialists[category][entity_id] → {field: record}` |
| `_research_context()` (what research receives) | `specialists[category] → {field: record}` **flattened** (entity_id stripped) |

`peer_specialists_for_entity()` only handles the nested shape (`records.get(entity_id)`). Production research context is flattened → function returns `{}` → `_peer_context.j2` never renders.

**Read-only context:** `docs/architecture.md`, slice `2010` output (`prompts/cursor/done/2026-06-09-2010-research-prompt-context-enrichment/`).

## How to start (mandatory)

Follow `prompts/cursor/WORKFLOW.md`:

1. **Claim** this file: move from `prompts/cursor/next/` to `prompts/cursor/in-progress/` before work.
2. Deliver under `prompts/cursor/done/2026-06-09-2110-research-peer-context-prominence/`.
3. **Do not commit or push** until Grok + Paul review.

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- In `output.md`, add **"For Grok + Paul"**: any roadmap notes, suggested commit message.
- Cursor delivers: code, tests, `output.md` only.

## Scope boundaries (strict)

**You may modify:**

- `src/tools/research.py` — `peer_specialists_for_entity()` (and small helpers if needed)
- `src/agents/factory/templates/research/_peer_context.j2` — human-readable formatting
- `tests/test_research.py`

**Out of scope:**

- `TODO.md`
- `_research_context()` shape change in `specialist_agent.py.j2` (fix the consumer, not the producer — flattened research context is intentional)
- Specialist regen
- Bind disambiguation / MVR logic
- Persistence validation

## Implementation

### 1. Fix `peer_specialists_for_entity()` — dual shape support

In `src/tools/research.py`, update `peer_specialists_for_entity()` to resolve peer rows from **either**:

**A. Nested (graph / test fixture):** `specialists[cat][entity_id] → field dict`

**B. Flattened (research context from `_research_context`):** `specialists[cat] → field dict` directly

Suggested approach:

```python
def _peer_category_row(records: dict, entity_id: str) -> dict | None:
    """Row of field records for entity_id, or flattened row already scoped to entity."""
    nested = records.get(entity_id)
    if isinstance(nested, dict) and nested:
        return nested
    # Flattened: keys are field names, values are storage records
    if records and not any(isinstance(k, str) and k == entity_id for k in records):
        if _looks_like_field_record_map(records):
            return records
    return None
```

Implement `_looks_like_field_record_map` robustly: e.g. non-empty dict whose values are dicts with a `status` key (specialist storage record shape). Do not mis-detect arbitrary nested graph data.

Then existing trim logic: omit fields where `status == "pending"`. **Also omit `status == "na"`** from the prominent peer block (reduces noise; `na` remains in JSON payload).

Exclude own `category` as today.

### 2. Make peer block human-readable (`_peer_context.j2`)

Replace raw `{{ fields | tojson }}` with readable lines, e.g.:

```
PEER SPECIALIST FINDINGS (read-only):
Use these to disambiguate the person and inform searches. Do not write peer fields unless listed in target_fields.

contact:
  - email: a******@talentcare.us (sources: https://rocketreach.co/...)
demographic:
  - city: Austin, TX
```

Prefer Jinja loop over `peer_specialists` field records: show `field`, `value` when `status == "found"`, optionally one source URL. Skip `pending` and `na`. Keep template simple; Python can pre-format a `peer_display` structure if cleaner.

### 3. User message ordering (verify)

When both disambiguation and peers present, order must be:

1. `DISAMBIGUATION (mandatory):` …
2. `PEER SPECIALIST FINDINGS` …
3. Intro + category guidance + JSON

Current code inserts peer then disambiguation at index 0 — disambiguation ends first. **Preserve** disambiguation-first; ensure peer block is second (index 1 after disambiguation insert, or insert peers at 1 when both exist). Document if you adjust insert logic.

### 4. Smoke tests

In `tests/test_research.py`, add/update `@pytest.mark.smoke` tests:

1. **Flattened research context (production path)** — context matching Paul's trace:

```python
context={
    "bind": {"name": "Angela Murphy", "employer": "TalentCare"},
    "storage": {"spouse": {"status": "pending", ...}},
    "specialists": {
        "contact": {
            "email": {"status": "found", "value": "a@talentcare.us", "sources": ["https://rocketreach.co/..."]},
            "address": {"status": "na", "reason": "..."},
        },
        "demographic": {
            "city": {"status": "found", "value": "Austin, TX", "sources": ["https://..."]},
        },
    },
}
```

`build_research_prompts(category="relationships", ...)` → user message contains `PEER SPECIALIST FINDINGS`, `contact`, `Austin, TX`, `a@talentcare.us`; does **not** lead with only JSON peers.

2. **Nested shape still works** — keep/update existing `test_build_research_prompts_includes_peer_specialists` (graph-shaped `specialists[cat][entity_id]`).

3. **`na` peer fields omitted from header** — `address` na not in peer block text (may still be in JSON).

Import only from `tools.research`; no live LLM/Tavily.

## Verification

```bash
uv run pytest tests/test_research.py -m smoke -q
uv run ruff check src/tools/research.py tests/test_research.py src/agents/factory/templates/research/_peer_context.j2
```

## Deliverables

`prompts/cursor/done/2026-06-09-2110-research-peer-context-prominence/`:

- `prompt.md`, `output.md` with **For Grok + Paul**

## Exit criteria

- [ ] `peer_specialists_for_entity()` handles flattened `_research_context` specialists shape
- [ ] `PEER SPECIALIST FINDINGS` renders when peers exist in production-shaped context
- [ ] Peer block human-readable (not single-line JSON blob per category)
- [ ] `pending` and `na` peer fields omitted from prominent block
- [ ] Nested graph shape still supported (regression test)
- [ ] Ruff clean; no `TODO.md` edit