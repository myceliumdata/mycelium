# Plans index

Design specs, slice maps, and backlogs for Mycelium. **Maintained by Grok + Paul.**

## Read this first

| Need | Document |
|------|----------|
| **New contributors** | [`docs/onboarding.md`](../onboarding.md) |
| **Current architecture** | [`docs/architecture.md`](../architecture.md) |
| **Operator quick start** | [`README.md`](../../README.md) |
| **Code orientation** | [`docs/full-code-walkthrough.md`](../full-code-walkthrough.md) |
| **Roadmap checklist** | [`TODO.md`](../../TODO.md) |
| **Stale-assumption audit** | [`historical-assumptions-audit.md`](historical-assumptions-audit.md) |
| **Removed ingest/storage (memory)** | [`legacy-ingest-and-storage-reference.md`](../legacy-ingest-and-storage-reference.md) |

**Important:** Most files in this directory are **point-in-time slice specs**. Completed phases may describe code that was later removed (e.g. `agents.seed`, `core_data`, runtime seed resolution). Treat them as **history**, not runtime truth, unless the plan is listed under **Active backlogs** below.

Implementation handoffs live in `prompts/cursor/done/<slug>/` with `prompt.md`, `output.md`, and `review.md`.

---

## How to use plans

1. Start from **`docs/architecture.md`** for what the system does today.
2. Use this index to find the **program** that matches your question.
3. Read the **phase/slice map** (if any), then the specific slice file.
4. For design rationale, check [`conversations/`](conversations/README.md).
5. Do **not** bulk-edit completed slice specs to match current code; add a new plan or backlog entry instead.

---

## Completed programs (historical specs)

### Entity protocol & registry (Slices 1–8 + polish)

| Doc | Status |
|-----|--------|
| [`entity-protocol-and-registry-program.md`](entity-protocol-and-registry-program.md) | Master map (some lookup-order text is pre–seed-elimination) |
| [`entity-key-suggestions-phase1.md`](entity-key-suggestions-phase1.md) | Done |
| [`entity-outcome-infrastructure-phase2.md`](entity-outcome-infrastructure-phase2.md) | Done |
| [`entity-unknown-mvr-phase3.md`](entity-unknown-mvr-phase3.md) | Done |
| [`entity-registry-bind-phase4.md`](entity-registry-bind-phase4.md) | Done |
| [`entity-validation-phase5.md`](entity-validation-phase5.md) | Done |
| [`entity-research-gate-phase6.md`](entity-research-gate-phase6.md) | Done |
| [`entity-boundary-cleanup-phase7.md`](entity-boundary-cleanup-phase7.md) | Done |
| [`entity-growth-phase8.md`](entity-growth-phase8.md) | Done |
| [`entity-protocol-polish-post8.md`](entity-protocol-polish-post8.md) | Done |
| [`entity-protocol-v1-test-plan.md`](entity-protocol-v1-test-plan.md) | Done |

### Seed elimination (Slices 13–18 + polish)

| Doc | Status |
|-----|--------|
| [`entity-uuid4-unification-slice13.md`](entity-uuid4-unification-slice13.md) | Done |
| [`entity-seed-elimination-phase.md`](entity-seed-elimination-phase.md) | **Complete** (exit criteria met) |
| [`entity-seed-elimination-slice14.md`](entity-seed-elimination-slice14.md) … [`slice18.md`](entity-seed-elimination-slice18.md) | Done |

### Metering & payment (Slices 9–12)

| Doc | Status |
|-----|--------|
| [`entity-metering-design-phase9.md`](entity-metering-design-phase9.md) | Done (design locked) |
| [`entity-metering-implementation.md`](entity-metering-implementation.md) | Slice 10 — done |
| [`entity-metering-hooks-phase10.md`](entity-metering-hooks-phase10.md) | Done |
| [`entity-metering-payment-phase11.md`](entity-metering-payment-phase11.md) | Done |
| [`entity-metering-payment-implementation.md`](entity-metering-payment-implementation.md) | Done |
| [`entity-metering-negotiation-test-scaffolding.md`](entity-metering-negotiation-test-scaffolding.md) | Slice 12 — done |
| Fix / test plans (`slice10-fix`, `slice11-fix`, `slice12-fix`, `pre-push-test-plan`) | Done |

### Networks & launch v1

| Doc | Status |
|-----|--------|
| [`networks-terminology.md`](networks-terminology.md) | Reference (network vs profile, paths) |
| [`networks-phase5.md`](networks-phase5.md) | **Delivered** — `network create` v1 |

### Foundation (pre-2026 redesign)

| Doc | Status |
|-----|--------|
| [`seed-data-context-architecture.md`](seed-data-context-architecture.md) | Historical — describes seed-loader era graph |
| [`classification-engine-phase1.md`](classification-engine-phase1.md) | Done; pre-`core_data` removal notes |
| [`agent-factory-phase2.md`](agent-factory-phase2.md) | Done; historical “current state” at plan time |
| [`specialist-research-phase1.md`](specialist-research-phase1.md) | Done |
| [`supervisor-intelligence-v1.md`](supervisor-intelligence-v1.md) | Long-term vision phases |

### MVR redesign (M1–M10, June 2026)

| Doc | Status |
|-----|--------|
| [`mvr-redesign-program.md`](mvr-redesign-program.md) | **Complete** — target protocol shipped |
| [`mvr-best-practices.md`](mvr-best-practices.md) | Operator guide (lookup vs MVR, two-step, metering) |
| [`mvr-redesign-entity-query-examples.md`](mvr-redesign-entity-query-examples.md) | Canonical step-1 / step-2 JSON (`create_on_deliver`, messages) |
| [`fuzzy-lookup-policy.md`](fuzzy-lookup-policy.md) | Bind-field fuzzy suggestions (`lookup_suggested`, `suggested_lookup`) — **shipped** (1430–1450) |
| [`../manual-checks/2026-06-13-mvr-redesign-post-program-gate.md`](../manual-checks/2026-06-13-mvr-redesign-post-program-gate.md) | Post-program manual gate |

### Attribute provenance — Program 2 (MVR / entity storage, June 2026)

| Doc | Status |
|-----|--------|
| [`attribute-provenance-program2.md`](attribute-provenance-program2.md) | **Complete** — on `origin/main`; manual gate **CLEAR** (2026-06-14) |
| [`attribute-provenance-program2-polish.md`](attribute-provenance-program2-polish.md) | Polish P1–P7 — done |
| [`attribute-provenance-program2-slice1.md`](attribute-provenance-program2-slice1.md) … [`slice3.md`](attribute-provenance-program2-slice3.md) | Done |
| [`../manual-checks/2026-06-13-program2-post-program-gate.md`](../manual-checks/2026-06-13-program2-post-program-gate.md) | Post-program manual gate — **CLEAR** (2026-06-14) |

### Entity protocol legacy cleanup — Program 3 (June 2026)

| Doc | Status |
|-----|--------|
| [`entity-protocol-legacy-cleanup-program.md`](entity-protocol-legacy-cleanup-program.md) | **Complete** — `bind_values`, status `resolve` JSON, legacy graph removed |
| [`entity-protocol-legacy-cleanup-polish.md`](entity-protocol-legacy-cleanup-polish.md) | Polish P1–P2 — slice 1560 |
| [`../manual-checks/2026-06-14-program3-post-program-gate.md`](../manual-checks/2026-06-14-program3-post-program-gate.md) | Post-program manual gate — **CLEAR** (2026-06-14) |

### Cleared / superseded backlogs

| Doc | Notes |
|-----|-------|
| [`admin-ui-backlog.md`](admin-ui-backlog.md) | Cleared June 2026; operator work in `TODO.md` |

---

## Active backlogs (may still guide work)

| Doc | Topic |
|-----|-------|
| [`attribute-provenance-and-storage.md`](attribute-provenance-and-storage.md) | Architecture — entity/index/protocol split |
| [`next-chunk-prep.md`](next-chunk-prep.md) | Handoff notes; Program 3 code complete — manual gate pending |
| [`research-robustness-backlog.md`](research-robustness-backlog.md) | Post-2010 research hardening |
| [`historical-assumptions-audit.md`](historical-assumptions-audit.md) | Phase 1 audit; Phase 2 cleanup recommendations |

Deferred product tracks are listed in **`TODO.md`** (settlement protocol, operator edit/re-research, `network create` v2, seed export, etc.).

---

## Design conversations

Archived Paul + Grok threads: [`conversations/README.md`](conversations/README.md).

---

## Adding a new plan

1. Agree scope with Grok + Paul.
2. Add `docs/plans/<topic>.md` or a slice under an existing program.
3. Queue Cursor work in `prompts/cursor/next/` (do not edit `TODO.md` from Cursor).
4. Link the new plan from this README under the right section.

---

*Last updated: June 2026 (Program 3 gate **CLEAR**; 1560 polish queued; Program 4 next).*