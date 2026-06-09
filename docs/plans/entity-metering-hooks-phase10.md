# Metering hooks — Phase 10 spec (draft)

**Status:** Draft — depends on Slice 9 design lock  
**Program:** [`entity-protocol-and-registry-program.md`](entity-protocol-and-registry-program.md)  
**Depends on:** Slice 9 design + Slice 6 gate

---

## Problem

After negotiation phases are designed (Slice 9), the runtime needs **minimal hooks** so future x402 integration has stable attachment points — without real payment in v1.

---

## Objective

- `quote_required` outcome stub when research would run but quote not accepted
- `audit_log` markers for phase transitions
- MCP / `describe_network` policy strings documenting phases
- **No** payment provider, HTTP 402, or wallet

---

## `quote_required` outcome (proposal)

Returned when:

- Entity resolved + validated (or seed pre-validated)
- `requested_attributes` non-empty
- Classify complete
- **No accepted quote** on thread (stub: always missing until client sends `quote_id`)

```json
{
  "outcome": "quote_required",
  "results": [{ "id": "…", "name": "…", "employer": "…" }],
  "message": "Research requires accepting a quote before commit.",
  "required_fields": [],
  "quote": {
    "quote_id": "…",
    "scoped_attributes": ["email"],
    "phase": "C",
    "expires_at": "…"
  }
}
```

**v1 stub behavior:** generate quote object; block Tavily until `EntityQuery.quote_id` matches (optional field added in Slice 10). For demos, env flag `MYCELIUM_AUTO_ACCEPT_QUOTES=1` skips gate.

---

## `EntityQuery` extension (proposal)

```python
quote_id: str | None = Field(
    default=None,
    description="Accepted quote id from prior quote_required response.",
)
```

---

## Audit log markers (proposal)

Append structured events on phase transitions:

| Event | When |
|-------|------|
| `negotiation.phase_a_complete` | Entity resolved or bound |
| `negotiation.phase_b_complete` | Classify done |
| `negotiation.quote_issued` | `quote_required` returned |
| `negotiation.quote_accepted` | Matching `quote_id` on query |
| `negotiation.phase_c_start` | Specialists invoked post-accept |

---

## MCP policy strings (proposal)

Extend `describe_network` negotiation section:

- Phase A–B free actions list
- Phase C requires quote
- How to pass `quote_id` on follow-up `query_entity`

---

## Tests (smoke)

- Validated entity + email, no `quote_id` → `quote_required`, no Tavily
- Same query + valid `quote_id` → research runs (with `MYCELIUM_AUTO_ACCEPT_QUOTES` off)
- Audit log contains `quote_issued` and `quote_accepted` events

---

## Open questions for Paul

### Q10a — Stub strictness

| Option | Meaning |
|--------|---------|
| A | **Strict stub** — always require `quote_id` for research (demo uses auto-accept env) |
| B | **Loose stub** — quote returned but research still runs; audit only |
| C | **Feature flag** — `network.json` `metering.enabled: false` default; true enables strict gate |

### Q10b — Quote persistence

| Option | Meaning |
|--------|---------|
| A | In-memory per thread (lost on restart) |
| B | `<network_root>/quotes.json` ephemeral file |
| C | No persistence — quote valid only in same response (client must echo immediately) |

### Q10c — Auto-accept for CRM demo

| Option | Meaning |
|--------|---------|
| A | `MYCELIUM_AUTO_ACCEPT_QUOTES=1` in `bin/run-studio` for dev |
| B | CRM example network.json `metering.mode: "bypass"` |
| C | No bypass — operators must pass quote_id in tests |

### Q10d — Slice 10 code vs docs-only minimum

| Option | Meaning |
|--------|---------|
| A | Full stub: outcome + query field + audit + tests |
| B | Minimal: `quote_required` outcome + audit markers only; no `quote_id` on query yet |
| C | Audit markers + MCP strings only; defer outcome to post-program |