# Metering hooks — Phase 10 spec (deferred)

**Status:** **Deferred** — blocked on Slice 9 design; Paul (June 2026): no Slice 10 work until Slices 1–8 ship and metering design resumes  
**Program:** [`entity-protocol-and-registry-program.md`](entity-protocol-and-registry-program.md)  
**Depends on:** Slice 9 design lock + Slice 6 gate

---

## Paul direction (June 2026)

Metering hooks (`quote_required`, `quote_id`, audit markers) are **out of scope** for the current Cursor handoff. Complete the entity protocol through **Slice 8 (growth + attribution)** first.

Open questions Q10a–Q10d below are preserved for a future design pass. No Cursor prompt until Slice 9 is locked.

---

## Objective (future)

- `quote_required` outcome stub when research would run but quote not accepted
- `audit_log` markers for phase transitions
- MCP / `describe_network` policy strings
- **No** payment provider, HTTP 402, or wallet

---

## Open questions (deferred)

### Q10a — Stub strictness

- A: Strict stub + env bypass
- B: Loose stub (audit only)
- C: Per-network `metering.enabled` flag

### Q10b — Quote persistence

- A: In-memory per thread
- B: `quotes.json` on disk
- C: Echo-only, no server persistence

### Q10c — Auto-accept for CRM demo

- A: `MYCELIUM_AUTO_ACCEPT_QUOTES` env
- B: `network.json` bypass mode
- C: No bypass

### Q10d — Minimum deliverable

- A: Full stub
- B: Outcome + audit only
- C: Audit + MCP strings only