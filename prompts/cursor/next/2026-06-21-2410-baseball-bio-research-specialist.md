# Baseball bio specialist — warehouse + Tavily research hybrid

> **DRAFT — do not claim** until Paul + Grok resolve open questions in [`docs/plans/conversations/2026-06-21-baseball-bio-research-specialist.md`](../../../docs/plans/conversations/2026-06-21-baseball-bio-research-specialist.md) § Open questions. Program sign-off done (2026-06-21). **Do not edit `TODO.md`.**

## Objective

Extend bio coverage so **manifest warehouse reads** stay the fast path, and **unaliased bio labels** fall through to **synchronous LLM + Tavily research** (CRM pattern) — not `derive_on_miss` / sqlite codegen.

Paul direction: follow-up bio questions need the web; Lahman `People` is necessary but not sufficient.

Read: [`docs/plans/conversations/2026-06-21-baseball-bio-research-specialist.md`](../../../docs/plans/conversations/2026-06-21-baseball-bio-research-specialist.md), [`docs/architecture/whys/specialist-class-hierarchy.md`](../../../docs/architecture/whys/specialist-class-hierarchy.md), CRM research in `src/tools/research.py`.

---

## Design (locked)

### Framework (`src/agents/specialists/`)

Add **`WarehouseResearchPlayerSpecialist`** (name negotiable in `output.md` if clearer):

- Extends `WarehousePlayerStatSpecialist`
- After warehouse evaluate loop: for owned fields still missing (not found, not N/A from manifest), invoke **`run_field_research`** when domain manifest allows research (see manifest flag below)
- Pack hook: `_research_enabled(manifest) -> bool` or manifest key `research_on_miss: true` on bio domain only in v1

**Do not** enable `derive_on_miss` on bio.

### Manifest (`warehouse_domains.json`)

Bio domain:

```json
"research_on_miss": true
```

Document: mutually independent from `derive_on_miss`; bio uses research only.

### Baseball pack

- `BioSpecialist(BaseballWarehousePlayerHooks, WarehouseResearchPlayerSpecialist)` — thin subclass only if hooks suffice
- **Do not** duplicate research loop in `bio_specialist.py`

### Guinea-pig attributes (live gate — discover anchors)

Pick **one** primary + optional synonym (M4b-style) from live research on Hank Aaron:

| Candidate label | Why | Anchor discovery |
|-----------------|-----|------------------|
| `hall_of_fame_year` | Canonical bio fact outside People | Web research → `"1999"` (Cooperstown induction) |
| `primary_nickname` | Fan-facing bio follow-up | e.g. `"Hammer"` — verify via gate discovery, tolerate normalization |

Cursor runs `./bin/gate-live baseball --discover` or manual step-2 on live root after implementation; **do not guess** anchors.

---

## Live gate (required)

Add to `tests/live/catalogs/baseball.yaml`:

| ID | Phase | Notes |
|----|-------|-------|
| `bb-bio-research-01` | `bio_research` (new — add to `networks.yaml` phases) | Aaron + `hall_of_fame_year`; `skip_if_missing_env: OPENAI_API_KEY`, `TAVILY_API_KEY` |
| `bb-bio-research-02` | `bio_research` | Optional synonym cache hit after 01 |

Update `tests/test_live_gate_runner_unit.py` minimum count + phases.

Drift check in `gate_runner.py` for new anchor keys.

---

## Tests

| Layer | Requirement |
|-------|-------------|
| Framework | Unit test: research invoked only when warehouse miss + `research_on_miss` |
| Pack | Bio smoke: warehouse attrs unchanged (`birth_date`); mocked research returns value for unknown label |
| Regression | Existing `test_baseball_bio_specialist.py` smokes green |
| CRM | No regression — shared `run_field_research` |

---

## Docs

- `examples/networks/baseball/README.md` — bio warehouse vs research paragraph
- `docs/manual-checks/2026-06-19-baseball-specialist-hand-test.md` — research rows
- `docs/architecture/whys/specialist-class-hierarchy.md` — add `WarehouseResearchPlayerSpecialist` to target tree

---

## Constraints

- No `derive_on_miss` on bio
- No team specialist research
- `./bin/ci-local` must pass
- Live gate scenarios `@pytest.mark.live_gate` only

---

## Output

Follow `prompts/cursor/WORKFLOW.md`. In `output.md` **For Grok + Paul**:

- Hierarchy diagram update
- Anchor discovery table
- Final scenario count
- Paul: run `./bin/gate-live baseball` with Tavily keys

Suggested commit message:

```
feat(baseball): bio specialist warehouse + Tavily research on miss
```