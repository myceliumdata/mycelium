# Why two-step query (resolve → deliver)

**Status:** Shipped (MVR redesign M1–M10, June 2026)  
**Mechanics:** [`architecture.md`](../../architecture.md) § MVR redesign · [`mvr-best-practices.md`](../../plans/mvr-best-practices.md) · [`mvr-redesign-entity-query-examples.md`](../../plans/mvr-redesign-entity-query-examples.md)

---

## The short answer

Public query is intentionally **two HTTP-equivalent steps**:

1. **Step 1 — Resolve:** send `id` or `lookup`; optionally bind `requested_attributes` and `provenance`. Response: `total_matches`, empty `results[]`, and a scoped **`delivery_id`** (plus a **quote** when metering is on).
2. **Step 2 — Deliver:** send `delivery_id` (+ `quote_id` when metered). Response: `found` / `assembled` with full `results[]`.

There is no `deliver: true` flag and no way to request extended attributes on step 2. The ticket from step 1 is the contract for what step 2 will do.

---

## What problem we were solving

Before June 2026, identity lookup, attribute delivery, create negotiation, and metering were tangled in a single request shape (`entity_key`, `binding`, implicit deliver). That caused four recurring failures:

| Failure | Symptom |
|---------|---------|
| **Scope ambiguity** | Client asks for “Kevin Zhang” — system does not know if they want identity only, LinkedIn research, or 200 employer matches until work has already started. |
| **Billing surprise** | Metered networks could not quote **before** expensive specialist / research work; agents could not compare marginal cost vs duplicate production. |
| **Accidental spend** | A loose lookup returning hundreds of rows could trigger N× research without an explicit client commitment to that batch. |
| **Protocol creep** | Every new capability (create-on-miss, provenance, batch) became another optional flag on one endpoint instead of a clear lifecycle. |

We separated three concerns (identity, lookup, MVR) *and* separated **cheap resolve** from **expensive deliver**. The two-step protocol is the delivery half of that separation.

---

## Why step 1 returns no `results[]`

Step 1 answers: **“Who matches, how many, and what am I about to deliver?”** — not **“Give me the data.”**

- **Resolve is cheap:** registry index lookup, bind-field negotiation (`lookup_suggested`, fuzzy), record-type inference. No specialist graph for extended attributes unless step 2 runs.
- **Deliver is expensive:** specialist invocation, warehouse SQL, web research, LLM derive (baseball M3+), provenance assembly, batch fan-out.

Returning empty `results[]` on step 1 is deliberate. It forces clients to treat resolve and deliver as distinct operations and keeps step-1 responses stable whether the client ultimately delivers or abandons the scope.

---

## Why `delivery_id` exists

`delivery_id` is a **short-lived scoped ticket** (default TTL 5 minutes) that freezes:

- matched `entity_ids` (0, 1, or N),
- step-1 `lookup` / `id` context,
- `requested_attributes` and `provenance` flags,
- create-on-deliver intent when applicable (`delivery.create_on_deliver: true`).

**Benefits:**

1. **Explicit commitment** — Step 2 is an intentional “yes, run the work you described in step 1,” not an accidental follow-on to a casual lookup.
2. **Stable scope** — Registry rows and indexes can change between steps; delivery hydrates from the ticket, not a re-interpretation of stale client input.
3. **Batch safety** — N matches are bound at issue time; step 2 delivers all N (no silent truncation) because the client already saw `total_matches` on step 1.
4. **Create-on-deliver** — Zero registry hits with full MVR in step-1 `lookup` yields a ticket scoped for provisional create; step 2 binds the row then runs research only if attrs were bound on step 1.

Unknown or expired `delivery_id` → `not_found`. There is no step-2 fallback that re-runs lookup from memory.

---

## Why `requested_attributes` are step-1 only

Extended attributes define **workload**, not **identity**. They must be known before:

- quoting metered research (CRM),
- routing specialists (baseball `career_hr` vs `birth_date`),
- deciding provenance assembly cost.

Allowing attrs on step 2 would let clients change the workload after seeing match counts or after accepting a quote — breaking metering integrity and making supervisor planning non-deterministic.

Step 2 sends only tokens (`delivery_id`, optional `quote_id`). Everything else was bound at resolve time.

---

## Why this still matters without metering

Baseball and other demo networks run with `metering.enabled: false`. Step 2 is free on `delivery_id` alone.

The same split still applies:

| Reason | Unmetered example |
|--------|-------------------|
| **Cheap vs expensive** | Step 1: “Hank Aaron” → one player uuid. Step 2: warehouse sums, bio dates, future derive codegen. |
| **Scope before specialists** | Supervisor reads attrs from `DeliveryScope`, not a second client payload. |
| **Agent ergonomics** | MCP/CLI clients mirror the same flow; wrappers can hide two round-trips but the protocol stays honest. |
| **Consistent outcomes** | `lookup_resolved` + empty `results[]` everywhere; no special-case single-step path to maintain. |

Metering adds **quote_required** between resolve and deliver. The underlying resolve → ticket → deliver shape is unchanged.

---

## Relationship to quotes (metered networks)

When `metering.enabled: true`, step 1 with `requested_attributes` (or deliverable scope) may return `quote_required` instead of immediate free delivery. The quote prices the **frozen scope** in `delivery_id`; step 2 requires `quote_id` after acceptance.

Negotiation (MCP `query_entity`) and payment settlement (`pay_quote`) are separate layers — see [`architecture.md`](../../architecture.md) § Metering negotiation vs payment settlement. The two-step query protocol is the negotiation spine; quotes attach to step 1, not a parallel ad-hoc API.

---

## What we deliberately did not do

| Alternative | Why we rejected it |
|-------------|-------------------|
| Single-step `deliver: true` | Hides cost and scope; broke metering and batch semantics. |
| `results[]` preview on step 1 | Blurs resolve/deliver; encourages clients to skip commitment for “just peeking.” |
| Re-resolve on step 2 from raw `lookup` | Race-prone; batch counts could change between steps. |
| Attrs on step 2 | Workload mutation after quote or match disclosure. |
| Permanent `delivery_id` | Orphan scopes and stale create intents; TTL bounds abandoned work. |

---

## Exceptions (by design)

**Bootstrap** (`network create`, `refresh-example-network`) bypasses the two-step protocol. Bulk seed import is an operator/maintainer action, not a visiting agent query. See [`seed-bootstrap.md`](../../seed-bootstrap.md).

**Status inspect** (`network status`, admin `/status`) is read-only diagnostics with exact `id`/`lookup` — not the public deliver path.

---

## Mental model

```text
Client                          Mycelium
  |  step 1: lookup + attrs?      |
  |------------------------------>|
  |  total_matches, delivery_id   |
  |  (+ quote if metered)         |
  |<------------------------------|
  |  [client decides: deliver?]   |
  |  step 2: delivery_id          |
  |------------------------------>|
  |  results[], provenance?       |
  |<------------------------------|
```

Treat step 1 + step 2 as **one logical operation** for UX (CLI can store `delivery_id` between commands), but **two protocol commitments** for correctness and cost control.