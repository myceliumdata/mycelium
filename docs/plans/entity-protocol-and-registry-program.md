# Entity protocol & registry — full program (slice map)

**Status:** Approved by Paul (June 2026) — entity protocol Slices 1–8 shipped; **Slices 9–12** metering program shipped (design, negotiation, settlement seam, test scaffolding). Settlement protocol (real x402) deferred.
**Sources:**  
- [`conversations/2026-06-08-entity-key-negotiation.md`](conversations/2026-06-08-entity-key-negotiation.md)  
- [`conversations/2026-06-08-entity-registry-validation-growth.md`](conversations/2026-06-08-entity-registry-validation-growth.md)  
- [`entity-key-suggestions-phase1.md`](entity-key-suggestions-phase1.md) (Slice 1 locked detail)

---

## Program goal

Build **agent-to-agent negotiation** from the outside in:

1. **Protocol** — structured outcomes, no silent binding, no research spend until entity is resolved.  
2. **Policy** — per-network minimum viable record (MVR) before bind.  
3. **Registry** — one place for ids, bind keys, validation state (not replicated in specialists).  
4. **Growth** — networks gain records from queries, not only bootstrap seed.  
5. **Metering** — **priced commit** on MCP (negotiation → Slice 9–10); **payment settlement** optional behind gate (Slice 11 — x402 is settlement, not negotiation).

**Paul’s problem split (never conflate):**

| Code | Problem | Example |
|------|---------|---------|
| A | Near-miss key | Kalman vs Kalmans |
| B | Unknown entity | Paul Murphy not in system |
| C | Under-specified | Need employer before email research |
| D | Attribute research | Email — only after bind |

---

## Cross-program decisions (proposed — confirm with Paul)

| # | Decision | Proposal | Rationale |
|---|----------|----------|-----------|
| P1 | Registry pattern | **(C) Specialists propose/validate domain fields; supervisor + registry commit** | Paul’s CRM split; registry is arbiter not research agent |
| P2 | Registry storage | **`<network_root>/entities.json`** (JSON, atomic save like `categories.json`) | Matches network layout; gitignored runtime |
| P3 | Lookup order after Slice 4 | **Registry (validated/provisional) → seed bootstrap → negotiate** | Validated registry overrides seed on conflict |
| P4 | Seed role long-term | **`seed.json` = bootstrap origin only**; growth writes registry; seed export/sync optional later | Store must grow; seed not canonical forever |
| P5 | Binding input shape | **Optional `binding: dict[str, str]` on `EntityQuery`** (Slice 4+) — keys from MVR (CRM: `employer`) | Machine agents need structured follow-up; no `provided_data` blob |
| P6 | Confirmation for near-miss | **Retry with `entity_key` only** (Slice 1 — locked) | Simplest agent loop |
| P7 | Research gate | **No `current_id` → no specialists/Tavily** (enforce uniformly by Slice 6) | Fixes today’s leak: unknown key + `email` still classifies |
| P8 | Validation depth (v1) | **Sync-light, rule-based only** — no LLM plausibility; no Tavily for core bind | Paul Q5d; extended attrs still use research |
| P9 | Metering | **Negotiation Slice 9–10; settlement Slice 11+** | x402 = HTTP settlement only; MCP = quote negotiation |
| P10 | Bootstrap seed gating | **Seed rows = trusted for research gate** (maintainer-curated at bootstrap); **grown entities must validate** | Preserves CRM demo; not a claim of real-world factual truth |

---

## Outcome enum (full program target)

Evolves across slices; implement only when each slice ships.

| `outcome` | Slice | Meaning |
|-----------|-------|---------|
| `found` | — | Identity hit, no attr request (existing) |
| `assembled` | — | Attr merge complete (existing) |
| `not_found` | — | Generic miss (no suggestion, no unknown protocol yet) — **narrowed over time** |
| `entity_key_unresolved` | **1** | Near-miss; `suggestions[]` populated |
| `entity_unknown` | **3** | No match, no suggestions; entity not in network |
| `entity_under_specified` | **3** | Known name path but MVR incomplete (e.g. missing `employer`) |
| `entity_bound_provisional` | **4** | Bind accepted; provisional id allocated |
| `entity_validated` | **5** | Core bind fields validated; research may proceed |
| `quote_required` | **10** | Commit needs metering acceptance; retry with `quote_id` |
| `principal_required` | **10 fix** | Metering: billing `principal` missing for funding model |
| `payment_required` | **11** | Settlement: call `pay_quote` before `quote_id` unlocks work |

Slice 1 implements the first four rows plus `entity_key_unresolved`. Later slices replace bare `not_found` for B/C cases.

---

## Slice map (implementation order)

### Slice 1 — Entity key suggestions *(spec locked)*

**Cursor prompt:** `prompts/cursor/next/2026-06-09-1000-entity-key-suggestions-protocol.md`  
**Detail:** [`entity-key-suggestions-phase1.md`](entity-key-suggestions-phase1.md)

| | |
|--|--|
| **Solves** | Problem A (Kalman/Kalmans) |
| **Ships** | `resolve_entity_key()`, `outcome` + `suggestions[]`, `entity_key_unresolved`, supervisor short-circuit, MCP policy |
| **Persists** | Nothing |
| **Non-goals** | Unknown entity, registry, binding fields, metering |

**Exit criteria:** Kalman+email → unresolved, no Tavily; Kalmans+email → normal flow.

---

### Slice 2 — Outcome infrastructure polish

| | |
|--|--|
| **Why separate** | Slice 1 adds `outcome`/`suggestions`; this slice ensures **all** response builders set `outcome` consistently; CLI/MCP schema docs; admin UI ignores new fields gracefully |
| **Ships** | Audit all `response_*` paths; JSON schema export for MCP; snapshot tests for response shape |
| **Depends on** | Slice 1 |
| **Non-goals** | New negotiation logic |

*Optional:* merge into Slice 1 if Cursor slice stays small. Keep separate if Slice 1 diff is already large.

---

### Slice 3 — MVR policy + unknown / under-specified negotiation *(no persist)*

| | |
|--|--|
| **Solves** | Problems B and C (Paul Murphy; generic name without employer) |
| **Ships** | Per-network **MVR** declaration; `entity_unknown` + `entity_under_specified` outcomes; `required_fields[]` on `QueryResponse`; supervisor short-circuit (no classify/specialists) |
| **Persists** | Nothing |

**MVR declaration (proposal):**

```json
// <network_root>/network.json (extend existing manifest)
"mvr": {
  "bind_fields": ["name", "employer"],
  "name_source": "entity_key",
  "description": "CRM people: name plus current employer before research."
}
```

Fallback for CRM example: if `mvr` absent, default `bind_fields: ["name", "employer"]` with `name` taken from `entity_key`.

**Behaviors:**

| Query | Outcome | `required_fields` |
|-------|---------|-------------------|
| `Paul Murphy` + `email` | `entity_unknown` | `["employer"]` |
| `Paul Murphy` + `employer: Acme` in future `binding` | (Slice 4) | — |
| Exact seed hit | unchanged | `[]` |

**Message (Paul Murphy):** *"No record for 'Paul Murphy'. To look up email, tell me who they work for (`employer`)."*

**Decisions (locked):**

- MVR lives in **`network.json`**
- `entity_unknown` when zero exact match and zero suggestions; `entity_under_specified` when `binding` partial (Slice 4) or MVR incomplete
- Slice 3: `entity_key` carries name; missing MVR fields → `entity_unknown` + `required_fields`

**Exit criteria:** Paul Murphy+email → `entity_unknown`, `required_fields=["employer"]`, no Tavily; Andrea Kalman still → Slice 1 path.

---

### Slice 4 — Entity registry store + provisional bind

| | |
|--|--|
| **Solves** | Allocate id; persist bind; first step of growth |
| **Ships** | `entities.json`, `EntityRegistry` module, `resolve_entity` (registry + seed), optional `EntityQuery.binding`, provisional bind on sufficient MVR |
| **Persists** | New registry rows |

**`entities.json` shape (proposal):**

```json
{
  "version": "1.0",
  "entities": {
    "<uuid>": {
      "id": "<uuid>",
      "name": "Paul Murphy",
      "employer": "Acme Corp",
      "validation_state": "provisional",
      "bind_fields": { "name": "provisional", "employer": "provisional" },
      "created_at": "…",
      "source": "query_bind"
    }
  },
  "by_name": { "paul murphy|acme corp": "<uuid>" }
}
```

**Bind rule:** When `entity_unknown`/`entity_under_specified` and caller supplies complete MVR via `binding` (e.g. `{"employer": "Acme Corp"}`), allocate uuid, write provisional entity, return `entity_bound_provisional`.

**Lookup order:** registry exact bind match → seed `find_by_key` → suggest → unknown.

**Decisions (locked):**

- Id allocation: **new uuid4** on bind (not uuid5 seed algorithm) — distinguishes grown entities
- Duplicate bind: same name+employer → same id; conflicting employer → new entity unless exact bind key match
- `EntityQuery.binding` optional dict; keys must be MVR fields

**Exit criteria:** Paul Murphy + `binding.employer` → provisional id in registry; re-query with name+employer resolves; still no email research until Slice 5/6.

---

### Slice 5 — Core validation orchestration *(spec locked)*

**Cursor prompt:** `prompts/cursor/next/2026-06-09-1400-entity-validation-phase5.md`  
**Detail:** [`entity-validation-phase5.md`](entity-validation-phase5.md)

| | |
|--|--|
| **Solves** | Demographic validates name; professional validates employer; registry commits |
| **Ships** | Validation mode on professional + demographic specialists (rule-based); registry promotes fields `provisional` → `validated`; outcome `entity_validated` |
| **Persists** | Registry validation_state updates |

**Flow:** bind (if needed) → validate → research when validated (same turn, with Slice 6).

**Decisions (locked):**

- Q5a: Validate on every query once MVR complete (even identity-only)
- Q5b: Validator failure → stay provisional, `found` + message; no `validation_rejected`
- Q5c: Same turn: bind → validate → research when validated
- Q5d: Rule-based validation only in v1 (no LLM)

**Exit criteria:** Bind Paul Murphy → validators run → registry validated → same-turn email research when attrs requested (Slice 6).

---

### Slice 6 — Research gate (enforce bind + validate) *(spec locked)*

**Cursor prompt:** `prompts/cursor/next/2026-06-09-1500-entity-research-gate-phase6.md`  
**Detail:** [`entity-research-gate-phase6.md`](entity-research-gate-phase6.md)

| | |
|--|--|
| **Solves** | Problem D only after A/B/C resolved; closes supervisor leak |
| **Ships** | Single gate: specialists only when `current_id` set AND registry/seed entity `validation_state == validated` (seed bootstrap treated as **pre-validated** for backward compat) |
| **Persists** | Nothing new |

**Decisions (locked):**

- Q6a: No `research_gated` outcome — `found` + clear message
- Q6b: Same turn — research after validation in one graph run

**Exit criteria:** Unbound/unknown/provisional → never invokes Tavily; validated Paul Murphy + email → contact research runs (including same turn after validation).

**Bootstrap seed (locked):** seed matches are treated as **validated for gating** — no provisional loop. Research on Andrea Kalmans + `email` still works without registry mirroring. Grown entities (registry `source: query_bind`) require `validation_state: validated`.

---

### Slice 7 — Seed vs specialists boundary cleanup *(spec locked)*

**Cursor prompt:** `prompts/cursor/next/2026-06-09-1600-entity-boundary-cleanup-phase7.md`  
**Detail:** [`entity-boundary-cleanup-phase7.md`](entity-boundary-cleanup-phase7.md)

| | |
|--|--|
| **Solves** | Paul’s overlap complaint (name/employer in seed + specialist storage) |
| **Ships** | Supervisor/registry owns bind lookup; specialists receive `entity_id` + `bind` + extended storage only; Jinja template + `context.py` updated; **delete `core_identity.py`**; clean `routing.py` / test resets |
| **Depends on** | Slices 4–6 |

**Decisions (locked):**

- Q7a: Ignore legacy name/employer in specialist storage
- Q7b: Clean slate — factory template + regen reference specialists
- Q7c: Delete `core_identity.py` in Slice 7

**Non-goals:** Delete seed.json; bulk migration of historical specialist data.

---

### Slice 8 — Seed from queries & network growth *(spec locked)*

**Cursor prompt:** `prompts/cursor/next/2026-06-09-1700-entity-growth-phase8.md`  
**Detail:** [`entity-growth-phase8.md`](entity-growth-phase8.md)

| | |
|--|--|
| **Solves** | Store must grow; **data attribution** (USP) on registry |
| **Ships** | Growth path hardened; `attr_sources` + `last_researched_at` on registry; Paul Murphy smoke arc |
| **Persists** | Registry attribution metadata + specialist storage |

**Decisions (locked):**

- Q8a: Full attribution — `attr_sources` + `last_researched_at` on registry rows
- Q8b: Empty-seed demo → deferred (`TODO.md`)
- Q8c: Seed export tooling → deferred (`TODO.md`)
- Q8d: Seed vs grown linking → deferred (`TODO.md`) — multi-network-type design needed

**Depends on:** Slices 4–7.

---

### Slice 9 — Metering negotiation design *(locked)*

**Detail:** [`entity-metering-design-phase9.md`](entity-metering-design-phase9.md)

| | |
|--|--|
| **Status** | **Locked** (June 2026) — Q9a–Q9m |
| **Ships** | Design only — priced commit, funding models, quote schema, decision rationale |
| **Not** | x402 / HTTP / wallet (see Slice 11) |

**Phases:** A–B free → C quoted → D quoted (first assembly metered by default).

---

### Slice 10 — Metering negotiation implementation *(shipped)*

**Detail:** [`entity-metering-implementation.md`](entity-metering-implementation.md) · Cursor: `prompts/cursor/done/2026-06-09-2100-entity-metering-implementation/`

| | |
|--|--|
| **Status** | **Shipped** (+ fix `2110`) |
| **Ships** | `quote_required`, `quote_id`, stores, `metering_gate`, 20 tests |
| **Default** | CRM `metering.enabled: false` |

**Depends on:** Slice 9 + Slice 6 gate.

---

### Slice 10 fix — Metering review nits *(shipped)*

**Detail:** [`entity-metering-slice10-fix.md`](entity-metering-slice10-fix.md) · `prompts/cursor/done/2026-06-09-2110-entity-metering-slice10-fix/`

| | |
|--|--|
| **Status** | **Shipped** — review approved |
| **Ships** | `provenance`, `principal_required`, policy E2E tests (20 metering tests) |

---

### Slice 11 — Payment settlement *(shipped)*

**Detail:** [`entity-metering-payment-phase11.md`](entity-metering-payment-phase11.md) · [`entity-metering-payment-implementation.md`](entity-metering-payment-implementation.md)  
**Cursor:** `prompts/cursor/done/2026-06-09-2200-entity-metering-payment-slice11/`

| | |
|--|--|
| **Status** | **Shipped** — review approved |
| **Ships** | `PaymentProvider`, `pay_quote` MCP, mock/credit/x402-stub, `paid` gate, `payment_required` |
| **Distinction** | **Negotiation = MCP (Slices 9–10). Settlement = Slice 11 (x402 is backend, not negotiation).** |

**Depends on:** Slice 10 + fix.

---

### Slice 11 fix — Payment review nits *(shipped)*

**Detail:** [`entity-metering-slice11-fix.md`](entity-metering-slice11-fix.md)  
**Cursor:** `prompts/cursor/done/2026-06-09-2210-entity-metering-payment-slice11-fix/`

| | |
|--|--|
| **Status** | **Shipped** — review pending |
| **Ships** | Quote expiry in `settle_quote`, credit-after-`mark_paid`, MCP `pay_quote` test, doc exit-criteria hygiene, x402 env note |

**Depends on:** Slice 11.

---

### Slice 12 — Negotiation test scaffolding *(shipped)*

**Detail:** [`entity-metering-negotiation-test-scaffolding.md`](entity-metering-negotiation-test-scaffolding.md)  
**Cursor:** `prompts/cursor/done/2026-06-09-2300-entity-metering-negotiation-test-scaffolding/`

| | |
|--|--|
| **Status** | **Shipped** — review approved |
| **Ships** | `crm-metering` example, CLI bind/quote flags, admin quote panel, `bin/demo-metering-negotiation` |
| **Not** | Real x402 / settlement protocol (separate `TODO.md` track) |

**Depends on:** Slices 10–11.

---

### Slice 12 fix — Negotiation scaffolding nits *(shipped)*

**Detail:** [`entity-metering-slice12-fix.md`](entity-metering-slice12-fix.md)  
**Cursor:** `prompts/cursor/done/2026-06-09-2310-entity-metering-slice12-fix/`

| | |
|--|--|
| **Status** | **Shipped** — review approved |
| **Ships** | Demo sync checkpointer, admin demo docs, demo subprocess test, MCP queries README |

**Depends on:** Slice 12.

---

### Slice 13 — Entity ID unification (uuid4 everywhere) *(shipped)*

**Track:** Seed elimination step 1  
**Detail:** [`entity-uuid4-unification-slice13.md`](entity-uuid4-unification-slice13.md)  
**Cursor:** `prompts/cursor/done/2026-06-10-1000-entity-uuid4-unification-slice13/`

| | |
|--|--|
| **Status** | **Shipped** |
| **Ships** | `ensure_bound_entity` registry helper; seed loader uses uuid4 + `entities.json` persistence; MCP runtime resets registry; remove uuid5 |
| **Not** | Remove runtime seed resolution (`find_by_key` / seed branch) — Slice 14 |

**Depends on:** Slices 1–12.

---

## Explicitly out of this program (separate tracks)

| Item | Why deferred |
|------|----------------|
| **Settlement protocol** (real x402, wallets, HTTP gateway, rebate/pool) | Separate track on `TODO.md`; Slice 11 ships pluggable seam only |
| Per-record query messages (multi-match) | Kevin Zhang disambiguation works via `results` today |
| Long-running threads / suspend | Related but separate UX slice |
| Inter-network handoff | Needs distributed discovery |
| Non-person seed schemas | After person CRM path proven |
| Agent tools review | Parallel roadmap |
| Silent fuzzy resolve | Paul rejected |

---

## Dependency diagram

```mermaid
flowchart LR
  S1[1 Suggestions]
  S2[2 Outcome polish]
  S3[3 MVR + unknown]
  S4[4 Registry bind]
  S5[5 Validation]
  S6[6 Research gate]
  S7[7 Boundary cleanup]
  S8[8 Growth]
  S9[9 Negotiation design]
  S10[10 Negotiation code]
  S11[11 Payment settlement]
  S11f[11 fix Payment nits]
  S12[12 Negotiation test scaffolding]
  S12f[12 fix Scaffolding nits]

  S1 --> S2
  S1 --> S3
  S3 --> S4
  S4 --> S5
  S5 --> S6
  S6 --> S7
  S7 --> S8
  S6 --> S9
  S9 --> S10
  S10 --> S11
  S11 --> S11f
  S11f --> S12
  S12 --> S12f
```

---

## Review nit triage (Grok — Paul approved June 2026)

After each slice lands in `prompts/cursor/done/`, Grok reviews `output.md` + diff. Every nit is **blocking** or **non-blocking**.

| Severity | Action | When it runs |
|----------|--------|--------------|
| **Blocking** | Define a **fix slice** immediately; queue in `prompts/cursor/next/` **before** the next planned slice | e.g. Slice 1 review → `1005-fix-…` before `1100` |
| **Non-blocking** | Add row to [`entity-protocol-polish-post8.md`](entity-protocol-polish-post8.md) | Single polish pass via `1800` after Slice 8 |

**Blocking** means any of: spec deviation that breaks exit criteria or downstream slices; failing smoke tests; broken agent contract (MCP/outcomes); security or data-integrity risk; regression on Andrea Kalmans / Paul Murphy arcs already shipped.

**Non-blocking** means: style, naming, doc wording, optional refactors, nice-to-have tests, admin-deferred UX — ship is correct but could be cleaner.

**Fix slice naming:** `YYYY-MM-DD-HHMM-<parent-slug>-fix-<short-topic>.md` with timestamp **between** parent and next planned prompt (e.g. `1005` between `1000` and `1100`). One fix slice per review pass when possible (batch related blocking nits).

**Review artifact:** Grok writes `review.md` in the done folder: Approved / Approved with fix slice / Approved with polish nits — lists fix prompt path or polish backlog rows.

**Gate:** Do not queue the next planned slice until blocking nits are cleared (fix slice reviewed) or Paul explicitly waives.

---

## Cursor handoff policy

| Rule | |
|------|--|
| **Per slice** | One prompt in `prompts/cursor/next/` after slice spec locked |
| **Spec before code** | Slices 3–10 need short spec files like `entity-key-suggestions-phase1.md` before queueing |
| **TODO.md** | Grok + Paul update after each slice reviewed — not Cursor |
| **Batch 1** | **Locked** — `1000`–`1300` |
| **Batch 2** | **Locked** — `1400`–`1600` |
| **Batch 3** | Slice 8 **locked** (`1700`); Slices 9–10 **deferred** |
| **Cursor** | **Approved for Slices 1–8** — start `1000` (Slice 1); sequential per dependency |
| **Fix slices** | Inserted by Grok after review when blocking nits found |
| **Polish** | Non-blocking nits → `entity-protocol-polish-post8.md`; Cursor `1800` after Slice 8 |

---

## Paul decisions (locked June 2026)

| Topic | Decision |
|-------|----------|
| Slice 2 | Keep separate from Slice 1 |
| MVR location | `network.json` |
| Binding field | `EntityQuery.binding` |
| Bootstrap seed | **Trusted for gating** — maintainer-curated seed skips validation loop; not a claim of real-world truth |
| Grown entities | **Must validate** before research (Slices 5–6) |
| Slice 5 validation | Rule-based only; same turn bind → validate → research |
| Slice 6 gate | `found` + message when blocked; same-turn research after validation |
| Slice 7 cleanup | Delete `core_identity.py`; clean slate specialist storage |
| Slice 8 attribution | `attr_sources` + `last_researched_at` on registry (USP) |
| Slice 8 deferred | Empty-seed demo, seed export, seed/grown linking → `TODO.md` |
| Slices 9–12 | **Shipped** — metering negotiation + settlement seam + `crm-metering` test scaffolding (June 2026) |
| Settlement protocol | **Deferred** — real x402, wallets, HTTP gateway (separate `TODO.md` track) |
| Program scope | Slices 1–12 approved and shipped |

---

## Approval

| Role | Status |
|------|--------|
| Paul | **Approved Slices 1–12** (June 2026); settlement protocol deferred |
| Grok | Handoff ready — Cursor starts Slice 1 |