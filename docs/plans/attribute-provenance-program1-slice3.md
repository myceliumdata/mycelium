# Program 1 — Slice 3: Query `provenance=true` + docs

**Status:** Ready after Slice 2 review  
**Program:** [`attribute-provenance-program1.md`](attribute-provenance-program1.md)  
**Depends on:** Slices 1–2

---

## Objective

Implement the metering promise: when `EntityQuery.provenance=true`, `QueryResponse` includes structured attribution for requested **extended** attributes. Update MCP/describe_network. No operator write.

---

## Implement

### 1 — `src/models/state.py`

Add to `QueryResponse`:

```python
provenance: dict[str, Any] | None = Field(
    default=None,
    description="Structured attribute versions when query.provenance=true; omitted otherwise.",
)
```

Shape per program spec (`provenance.entities[].attributes.<field>.versions`).

### 2 — Provenance builder

New helper e.g. `src/agents/query_provenance.py`:

- Input: matched entity id(s), requested_attributes, network paths
- Load specialist storage per attr (use registry `attr_sources` or category map)
- Copy `versions[]` + `current_version_id` for each requested extended attr
- Skip bind fields (`name`, `employer`) in Program 1

Wire from `run_query` / `assemble_response` path when `state.query.provenance` and outcome is delivered results (`found`, `assembled`, etc.).

### 3 — MCP + CLI

- MCP `query_entity` schema documents `provenance` on response
- `describe_network` / `build_network_capabilities` — document response shape and example JSON

### 4 — Tests

- `tests/test_entity_metering.py` or new `tests/test_query_provenance.py`:
  - Seed versioned linkedin in storage → query with `provenance=true` → response contains versions + sources
  - `provenance=false` → `provenance` null/absent
  - Metering gate still charges `query_provenance` meter (existing tests)

### 5 — Docs

- `docs/architecture.md` — `provenance` block on `QueryResponse`
- Cross-link from [`attribute-provenance-program1.md`](attribute-provenance-program1.md)

---

## Do NOT

- Operator edit endpoints
- MVR / Program 2
- `TODO.md`

---

## Verification

`./bin/ci-local` green. Manual: CRM query Paul Murphy linkedin with `--provenance` shows version block.