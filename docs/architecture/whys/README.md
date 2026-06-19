# Architecture rationales (whys)

**Purpose:** Explain *why* we made specific design choices — without cluttering the main architecture doc.

**Read [`architecture.md`](../architecture.md) first** for what the system is and how it works. Come here when you need the reasoning behind a decision.

---

## How to use this directory

| Doc | Question it answers |
|-----|---------------------|
| [two-step-query-protocol.md](two-step-query-protocol.md) | Why is query split into resolve (step 1) and deliver (step 2)? Why `delivery_id`? Why are `requested_attributes` step-1 only? |

Each file is self-contained. Fresh contributors should not need to read `docs/plans/conversations/` or historical slice specs to understand a shipped decision.

---

## Adding a new why

When a design choice keeps coming up in review or onboarding:

1. Add `docs/architecture/whys/<short-topic>.md` — problem, constraints, decision, tradeoffs, what we did *not* do.
2. Link it from this README table.
3. Add one sentence + link in [`architecture.md`](../architecture.md) § Architecture rationales (or at the relevant how-to section).

Keep [`architecture.md`](../architecture.md) as the **what/how** spine. Move rationale out of slice plans and conversation archives when the decision is stable.

---

## Candidates for future whys

Rationale for these topics still lives in program docs or plans; migrate when they stabilize or confuse new readers:

| Topic | Current home |
|-------|----------------|
| No `core_data` / specialist-owned storage | [`architecture.md`](../architecture.md) § Core Architectural Philosophy |
| Warehouse factory (manifest → resolve → cache) | [`plans/baseball-example-program.md`](../../plans/baseball-example-program.md) |
| Metering negotiation vs payment settlement | [`architecture.md`](../architecture.md) § Metering negotiation |
| Bootstrap bypasses two-step query | [`seed-bootstrap.md`](../../seed-bootstrap.md) |
| Identity vs lookup vs MVR (three concerns) | [`plans/mvr-redesign-program.md`](../../plans/mvr-redesign-program.md) |