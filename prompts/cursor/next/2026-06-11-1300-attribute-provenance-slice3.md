# Task: Program 1 — Attribute provenance Slice 3 (`provenance=true` response)

> **BLOCKED until Slice 2 approved** — Do not claim this file until `prompts/cursor/done/2026-06-11-1200-attribute-provenance-slice2/review.md` exists with **Approved** (or approved fix slice complete). If not approved, skip and report.

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/attribute-provenance-program1.md`](../../docs/plans/attribute-provenance-program1.md) — program context; **Query provenance response** section
- [`docs/plans/attribute-provenance-program1-slice3.md`](../../docs/plans/attribute-provenance-program1-slice3.md) — **locked spec**
- [`src/agents/specialist_fields.py`](../../src/agents/specialist_fields.py)
- [`src/models/state.py`](../../src/models/state.py) — `EntityQuery.provenance` (request flag; distinct from response field)

**Depends on:** Slices 1–2 (versioned storage + read path + introspection).

**Lane:** Cursor implements code + tests only. Do **not** edit `TODO.md`. No operator write endpoints.

---

## Objective

Fulfill the metering promise: when `EntityQuery.provenance=true`, `QueryResponse` includes structured attribution for requested **extended** attributes. Update MCP / `describe_network` docs. Default flat `results` unchanged.

---

## Implement

Follow [`attribute-provenance-program1-slice3.md`](../../docs/plans/attribute-provenance-program1-slice3.md) exactly:

### 1 — `src/models/state.py`

Add to `QueryResponse` (response payload — not the request flag on `EntityQuery`):

```python
provenance: dict[str, Any] | None = Field(
    default=None,
    description="Structured attribute versions when query.provenance=true; omitted otherwise.",
)
```

Shape per program spec:

```json
{
  "provenance": {
    "entities": [
      {
        "id": "…",
        "attributes": {
          "linkedin": {
            "current_version_id": "v1",
            "versions": [ … ]
          }
        }
      }
    ]
  }
}
```

### 2 — `src/agents/query_provenance.py` (new)

Builder helper:

- Input: matched entity id(s), `requested_attributes`, network paths
- Resolve category per attr via registry `attr_sources` or category map
- Load specialist storage; copy `current_version_id` + `versions[]` for each requested **extended** attr
- **Skip** bind fields (`name`, `employer`) in Program 1
- Return `None` when nothing to attach

Wire from `assemble_response` / `run_query` path when `state.query.provenance` is true and outcome delivers results (`found`, `assembled`, etc.). When `provenance=false`, omit or set `null` on response.

### 3 — MCP + CLI + capabilities

- MCP `query_entity` response schema documents top-level `provenance`
- `describe_network` / `build_network_capabilities` in `introspection.py` — document response shape + example JSON snippet

### 4 — Tests

Prefer `tests/test_query_provenance.py` (new) or extend `tests/test_entity_metering.py`:

- Seed versioned `linkedin` in specialist storage → query with `provenance=true` → response contains `provenance.entities[].attributes.linkedin.versions` with sources
- `provenance=false` → `provenance` null/absent on `QueryResponse`
- Existing metering tests still pass (`query_provenance` meter charged when request flag set)

Mark new tests `@pytest.mark.smoke` or `full` per WORKFLOW policy; run appropriately before claiming done.

### 5 — Docs

- `docs/architecture.md` — `provenance` block on `QueryResponse`; cross-link program doc
- Brief note that request flag (`EntityQuery.provenance`) ≠ response field (`QueryResponse.provenance`)

---

## Constraints

- **Do not touch:** operator edit/research endpoints, `entities.json` / MVR / Program 2, admin UI beyond docs (Slice 2 owns version timeline UI).
- **Do not change** flat `results[]` shape for default queries.
- `./bin/ci-local` green.

---

## Governance (mandatory)

- **Do not edit `TODO.md`.** Roadmap updates are for Grok + Paul after review.
- In `output.md`, add **"For Grok + Paul"**: mark Program 1 complete, operator correction unblocked, any roadmap notes.
- Cursor delivers: code, tests, task-scoped docs, and `output.md` only.
- **No commit before review** — leave changes in working tree; note suggested commit message in `output.md`.

---

## Deliverables

Move this file to `prompts/cursor/done/2026-06-11-1300-attribute-provenance-slice3/` with:
- `prompt.md` (copy of this file)
- `output.md` — summary + **For Grok + Paul** section
- Run `./bin/ci-local` and record result in `output.md`
- Manual check note: CRM query Paul Murphy `linkedin` with `--provenance` shows version block

---

## Review gate

Grok reviews before Program 1 closeout and Program 2 design.