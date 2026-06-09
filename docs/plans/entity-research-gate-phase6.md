# Research gate — Phase 6 spec (draft)

**Status:** Partially locked (Paul, June 2026) — Q6b confirmed pending spec lock  
**Depends on:** Slices 4–5

---

## Problem

Today, unknown or provisional entities with `requested_attributes` can still reach specialists/Tavily. Slice 3–5 add negotiation and validation; Slice 6 **enforces one gate** everywhere.

---

## Objective

**Single rule:** invoke specialists (and Tavily) only when:

```
current_id is set
AND (
  seed match (bootstrap, pre-validated)
  OR registry entity validation_state == validated
)
```

---

## Behaviors (proposal)

| Resolved entity | `email` requested | Behavior |
|-----------------|-------------------|----------|
| Seed (Andrea Kalmans) | yes | Research runs (unchanged) |
| Registry provisional | yes | No specialists; message: validation required |
| Registry validated | yes | Research runs |
| Unknown / unresolved | yes | Slice 1/3 short-circuit (no change) |

**Provisional + attrs message (proposal):**  
*"Record is provisionally bound; core validation must complete before researching requested attributes."*

---

## Implementation locus

- `supervisor.py` — do not populate `specialists_to_invoke` when gate fails
- `_route_after_supervisor` — unchanged if specialists list empty
- `assemble_response` — may need `response_gated` helper or extend `found` with explanatory message when attrs requested but gate blocks

**Outcome when gated with attrs (proposal):** `found` if identity resolved, else prior negotiation outcome; `message` explains gate; `results` identity only, no attr values.

**Locked (Paul):** `found` + clear `message` (no `research_gated` outcome).

---

## Tests (smoke)

- Validated Murphy + email → contact specialist invoked (mock Tavily)
- Provisional Murphy + email → no invoke
- Seed person + email → invoke
- Kalman unresolved + email → no invoke

---

## Open questions for Paul

1. **`research_gated` outcome** vs `found` + message when identity known but research blocked?

2. **Validate + research same turn:** after Slice 5 validates in one query, should Slice 6 allow research **in the same graph run** if validation just completed? **Proposal: yes** — one turn: bind → validate → research if validated.