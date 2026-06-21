# Design conversation archives

Full-context notes from **Paul + Grok** design discussions. These preserve reasoning, examples, and open questions beyond the distilled bullets in `TODO.md`.

| Date | Topic | File | TODO anchor |
|------|-------|------|-------------|
| 2026-06-08 | Entity key suggestions, agent negotiation, x402 | [2026-06-08-entity-key-negotiation.md](2026-06-08-entity-key-negotiation.md) | Protocol → Entity key suggestions; Negotiation & metering. **Spec:** [entity-key-suggestions-phase1.md](../entity-key-suggestions-phase1.md) |
| 2026-06-08 | Entity registry, validation timing, network growth | [2026-06-08-entity-registry-validation-growth.md](2026-06-08-entity-registry-validation-growth.md) | Protocol → Entity registry, validation & growth |
| 2026-06-14 | Data factory origin (MCP on raw data); baseball motivation | [2026-06-14-data-factory-origin.md](2026-06-14-data-factory-origin.md) | Product narrative; derivative retention (deferred) |
| 2026-06-15 | Baseball example — MVR grains, uuid4, name+team bind | [2026-06-15-baseball-example-design.md](2026-06-15-baseball-example-design.md) | `TODO.md` → `baseball` example |
| 2026-06-16 | LLM alias resolution (Yanks, 465 Ventures) vs explicit tables | [2026-06-16-llm-alias-resolution.md](2026-06-16-llm-alias-resolution.md) | [`baseball-example-program.md`](../baseball-example-program.md); [`fuzzy-lookup-policy.md`](../fuzzy-lookup-policy.md) |
| 2026-06-16 | Cold start — ontology, data-source handoff, sort-yourself-out | [2026-06-16-baseball-cold-start.md](2026-06-16-baseball-cold-start.md) | [`baseball-example-program.md`](../baseball-example-program.md) § Cold start |
| 2026-06-16 | Team vs franchise grain — emergent organization | [2026-06-16-team-vs-franchise-grain.md](2026-06-16-team-vs-franchise-grain.md) | Team registry ≠ `franchID`; franchise specialist |
| 2026-06-16 | Canonical team/city names — ingest + LLM layers | [2026-06-16-canonical-team-city-names.md](2026-06-16-canonical-team-city-names.md) | Full canonical name; LLM aliases |
| 2026-06-16 | Canonical bootstrap — generic framework vs network specialists | [2026-06-16-canonical-names-bootstrap-specialists.md](2026-06-16-canonical-names-bootstrap-specialists.md) | No custom orchestrator; bootstrap phase |
| 2026-06-16 | Bootstrap experiment v0 results | [2026-06-16-bootstrap-experiment-v0-results.md](2026-06-16-bootstrap-experiment-v0-results.md) | 241 teams auto-commit; LLM hybrid |
| 2026-06-18 | Computation-centric provenance; source-first ontology | [2026-06-18-computation-centric-provenance.md](2026-06-18-computation-centric-provenance.md) | `TODO.md` → computation-centric provenance; baseball M1; dataset manifest (deferred) |
| 2026-06-19 | Warehouse layer 3, stats surface, specialist emergence | [2026-06-19-warehouse-factory-layer3-specialist-emergence.md](2026-06-19-warehouse-factory-layer3-specialist-emergence.md) | `TODO.md` → warehouse manifest M2a; specialist promotion; retention policy |
| 2026-06-19 | Deep provenance — input-fact lineage beyond computation envelope | [2026-06-19-deep-provenance-lineage-expansion.md](2026-06-19-deep-provenance-lineage-expansion.md) | `TODO.md` → deep provenance |
| 2026-06-19 | Baseball M4 — free-form derive on manifest miss | [2026-06-19-baseball-m4-free-form-derive.md](2026-06-19-baseball-m4-free-form-derive.md) | Cursor `2026-06-19-2200-baseball-free-form-derive-m4` |
| 2026-06-20 | Baseball M4b — intent normalization (label → slug) | [2026-06-20-baseball-m4b-intent-normalization.md](2026-06-20-baseball-m4b-intent-normalization.md) | `TODO.md` → M4b shipped; gate [`2026-06-19-baseball-m4b-intent-normalization-gate.md`](../manual-checks/2026-06-19-baseball-m4b-intent-normalization-gate.md) |
| 2026-06-20 | Baseball M5 — natural language `question` → intent (**deferred — unlikely**) | [2026-06-20-baseball-m5-natural-language-question.md](2026-06-20-baseball-m5-natural-language-question.md) | [`unlikely/README.md`](../unlikely/README.md) — not on `TODO.md` |
| 2026-06-20 | Live gate program — opt-in baseball + CRM regression | [2026-06-20-live-gate-program.md](2026-06-20-live-gate-program.md) | Cursor `2026-06-20-1600-live-gate-baseball-crm` |
| 2026-06-21 | Baseball bio + Tavily research (design) | [2026-06-21-baseball-bio-research-specialist.md](2026-06-21-baseball-bio-research-specialist.md) | `TODO.md` → bio design lock; slice `2410` |
| 2026-06-21 | Peer-aware specialists + analytic orchestration | [2026-06-21-peer-aware-specialists-analytic-orchestration.md](2026-06-21-peer-aware-specialists-analytic-orchestration.md) | `TODO.md` → peer orchestration; metering review |

When resuming work, read the relevant conversation doc first, then **`docs/plans/entity-protocol-and-registry-program.md`** (full slice map), then `TODO.md` for the current checklist.