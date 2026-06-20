# Architecture rationales (whys)

**Purpose:** Explain *why* we made specific design choices — without cluttering the main architecture doc.

**Read [`architecture.md`](../architecture.md) first** for what the system is and how it works. Come here when you need the reasoning behind a decision.

---

## Published whys

| Doc | Question it answers |
|-----|---------------------|
| [two-step-query-protocol.md](two-step-query-protocol.md) | Why resolve → `delivery_id` → deliver? Why attrs on step 1 only? |
| [specialist-owned-data.md](specialist-owned-data.md) | Why no `core_data`? Why does the supervisor route instead of read storage? |
| [identity-lookup-and-mvr.md](identity-lookup-and-mvr.md) | Why UUID identity, partial lookup, and full MVR for create are separate |
| [three-layer-storage-model.md](three-layer-storage-model.md) | Which layer is authoritative: registry, indexes, or specialist `versions[]`? |
| [data-factory-origin.md](data-factory-origin.md) | Why not MCP on raw data? Why a factory at all? |
| [computation-centric-provenance.md](computation-centric-provenance.md) | Why `sources[]` ≠ the answer; what `computation` and `parameters` record |
| [warehouse-factory-stack.md](warehouse-factory-stack.md) | Why manifest + ontology routing + specialist execution (not 500 ontology attrs) |
| [metering-economics.md](metering-economics.md) | Why quotes before work; negotiation vs settlement; marginal pricing |
| [multi-record-type-routing.md](multi-record-type-routing.md) | Why lookup key shape routes record type; fan team vs franchise grain |
| [specialist-class-hierarchy.md](specialist-class-hierarchy.md) | Why warehouse/product bases live in `src/`; target hierarchy above `SpecialistAgent` |

Each file is self-contained. Fresh contributors should not need to read `docs/plans/conversations/` or historical slice specs to understand a shipped decision.

---

## Adding a new why

When a design choice keeps coming up in review or onboarding:

1. Add `docs/architecture/whys/<short-topic>.md` — problem, constraints, decision, tradeoffs, what we did *not* do.
2. Link it from the table above.
3. Add one row in [`architecture.md`](../architecture.md) § Architecture rationales (and optionally one sentence at the relevant how-to section).

Keep [`architecture.md`](../architecture.md) as the **what/how** spine. Move rationale out of slice plans and conversation archives when the decision is stable.

---

## Candidates for future whys

Migrate when a topic confuses new readers or stabilizes after more shipping work:

| Topic | Question it answers | Current home |
|-------|---------------------|--------------|
| Query-only public API | Why no ingest / `provided_data`? How does data still enter? | [`architecture.md`](../architecture.md) § Public interface; [`legacy-ingest-and-storage-reference.md`](../../legacy-ingest-and-storage-reference.md) |
| Framework vs network pack | What lives in `src/` vs `examples/networks/*` vs live `network_root`? | [`networks-terminology.md`](../../plans/networks-terminology.md) |
| Bootstrap bypasses two-step | Why doesn't `refresh-example-network` use `delivery_id`? | [`seed-bootstrap.md`](../../seed-bootstrap.md) |
| Step-1 negotiation ladder | Exact → fuzzy → LLM alias → incomplete/create — why this order? | [`fuzzy-lookup-policy.md`](../../plans/fuzzy-lookup-policy.md); [`onboarding.md`](../../onboarding.md) |
| Fuzzy vs LLM alias (two layers) | Why typos are fuzzy but `Yanks` is LLM? Why fuzzy never writes aliases? | [`fuzzy-lookup-policy.md`](../../plans/fuzzy-lookup-policy.md); conversation `2026-06-16-llm-alias-resolution` |
| `bootstrap_only` vs `query_allowed` | Why can CRM create on query but baseball cannot? | [`query-record-type-router.md`](../../query-record-type-router.md) |
| Networks: framework vs `network_root` | Why is my data outside the git clone? | [`networks-terminology.md`](../../plans/networks-terminology.md) |
| Specialist dispatch isolation | Why framework must not open `storage.json`; what snapshots are for | [`architecture.md`](../architecture.md) § Specialist I/O protocol |
| Source keys vs protocol `id` | Why isn't Lahman `playerID` the public handle? | [`baseball-example-program.md`](../../plans/baseball-example-program.md) § Identity layers |
| Storage evolution (minisql, deferred flush) | Why JSON then SQLite at threshold; one bootstrap flush | [`storage-evolution-program.md`](../../plans/storage-evolution-program.md) |
| Derivative retention / cache economics | When to keep computed series vs one-shot discard | Conversations `2026-06-14-data-factory-origin`, `2026-06-19-warehouse-factory` |
| Agent Factory lazy specialists | When on-demand specialist creation is appropriate | [`agent-factory-phase2.md`](../../plans/agent-factory-phase2.md) |
| Ground truth vs web waterfall | CRM research path vs baseball warehouse-first policy | Partially in [warehouse-factory-stack.md](warehouse-factory-stack.md); hand-test doc |
| Franchise specialist / promotion policy | When cross-domain product specialists get created | Conversation `2026-06-19-warehouse-factory-layer3-specialist-emergence` |
| Specialist class hierarchy (full) | CRM research vs warehouse vs product tiers | [specialist-class-hierarchy.md](specialist-class-hierarchy.md) (M14) |
| Cold-start orchestrator | “Point at data source; sort yourself out” vs scripted bootstrap | Conversation `2026-06-16-baseball-cold-start`; baseball program § Cold start |
| Entity validation lifecycle | bootstrap → provisional → validated → research | Conversation `2026-06-08-entity-registry-validation-growth` |
| Classification engine (supervisor thin) | Why ontology lookup is cached map, not hot-path LLM | [`classification-engine-phase1.md`](../../plans/classification-engine-phase1.md) |
| Version history for all statuses | Why `pending` and `na` get `versions[]` too | [`attribute-provenance-program1.md`](../../plans/attribute-provenance-program1.md) |
| Bind replace policy | Why old bind keys are not kept as aliases | [`attribute-provenance-and-storage.md`](../../plans/attribute-provenance-and-storage.md) |
| Product narrative / brand | Origin stories for website and onboarding intro | [`TODO.md`](../../../TODO.md) § Brand; conversation `2026-06-14-data-factory-origin` |