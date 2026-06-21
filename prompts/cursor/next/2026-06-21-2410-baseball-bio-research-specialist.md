# Baseball bio specialist — warehouse + Tavily research hybrid

> **READY** — Design locked [`docs/plans/conversations/2026-06-21-baseball-bio-research-specialist.md`](../../../docs/plans/conversations/2026-06-21-baseball-bio-research-specialist.md) (Paul sign-off 2026-06-21). May run **parallel** with `2400` (Paul Q7). **Do not edit `TODO.md`.**

## Objective

Extend bio coverage so **manifest warehouse reads** stay the fast path (including **HallOfFame** when aliased), and **unaliased bio labels** fall through to **synchronous LLM + Tavily research** (CRM pattern) — not `derive_on_miss`.

Read: design conversation (locked), [`docs/architecture/whys/specialist-class-hierarchy.md`](../../../docs/architecture/whys/specialist-class-hierarchy.md), CRM research in `src/tools/research.py`.

---

## Design (locked)

### Framework (`src/agents/specialists/`)

Add **`WarehouseResearchPlayerSpecialist`**:

- Extends `WarehousePlayerStatSpecialist`
- After warehouse evaluate loop: for owned fields still missing, invoke **`run_field_research`** when `research_on_miss` on domain
- **Paul Q1:** framework base class in `src/` — not pack-only `run()` override

**Do not** enable `derive_on_miss` on bio.

### Manifest (`warehouse_domains.json`)

Bio domain:

```json
"research_on_miss": true
```

Add **warehouse alias** (Paul Q8 — Lahman wins over web):

```json
"hall_of_fame_year": {
  "convention": "hof_election_year",
  "table": "HallOfFame",
  "filter": "inducted = 'Y'"
}
```

Implement `hof_election_year` in pack `warehouse_resolve.py` (or shared convention module). Aaron anchor: **`1982`** (`HallOfFame.yearid`, election — not ceremony 1999). **No Tavily** for `hall_of_fame_year` once alias exists.

### Baseball pack

- `BioSpecialist(BaseballWarehousePlayerHooks, WarehouseResearchPlayerSpecialist)` — thin subclass
- **Do not** duplicate research loop in `bio_specialist.py`

### Ontology (`categories.json`)

Hand-add (Paul Q4):

- `primary_nickname` → bio (research gate)
- `hall_of_fame_year` → bio (warehouse alias)

**Follow-on:** review hand-add vs lazy ontology for self-creating network goal (not blocking).

### Live gate guinea pigs

| Attr | Gate role | Path |
|------|-----------|------|
| **`primary_nickname`** | **`bb-bio-research-01`** — proves research | Tavily on miss; discover anchor on Aaron (e.g. Hammer) — do not guess |
| **`hall_of_fame_year`** | **`bb-bio-03`** or extend m2 — proves manifest HOF | Warehouse only; `equals: "1982"` |

**Do not** use `hall_of_fame_year` for Tavily research gate — sqlite has the answer.

**Deferred (Grok committed follow-on):** `bb-bio-research-02` nickname synonym / normalization tests.

---

## Live gate (required)

Add to `tests/live/catalogs/baseball.yaml`:

| ID | Phase | Notes |
|----|-------|-------|
| `bb-bio-research-01` | `bio_research` | Aaron + `primary_nickname`; `skip_if_missing_env: OPENAI_API_KEY`, `TAVILY_API_KEY` |
| `bb-bio-03` | `m2` | Aaron + `hall_of_fame_year`; warehouse manifest; `equals: "1982"` |

Add `bio_research` phase to `tests/live/networks.yaml` if missing.

Update `tests/test_live_gate_runner_unit.py` minimum count.

---

## Tests

| Layer | Requirement |
|-------|-------------|
| Framework | Unit test: research invoked only when warehouse miss + `research_on_miss` |
| Pack | Bio smoke: `birth_date` unchanged; mocked research for `primary_nickname`; `hall_of_fame_year` manifest without Tavily |
| Regression | `test_baseball_bio_specialist.py` green |
| CRM | No regression — shared `run_field_research` |

---

## Docs

- `examples/networks/baseball/README.md` — bio warehouse vs research; Lahman wins when table exists
- `docs/architecture/whys/specialist-class-hierarchy.md` — add `WarehouseResearchPlayerSpecialist`

---

## Constraints

- No `derive_on_miss` on bio
- `./bin/ci-local` must pass
- Live gate `@pytest.mark.live_gate` only

---

## Output

Follow `prompts/cursor/WORKFLOW.md`. In `output.md` **For Grok + Paul**:

- Hierarchy diagram update
- Anchor discovery table (`primary_nickname`, `hall_of_fame_year=1982`)
- Final scenario count
- Paul: `./bin/gate-live baseball` with Tavily keys

Suggested commit message:

```
feat(baseball): bio warehouse + Tavily research on miss (framework tier)
```