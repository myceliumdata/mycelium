# Research gate — Phase 6 spec

**Status:** Locked (Paul, June 2026)  
**Program:** [`entity-protocol-and-registry-program.md`](entity-protocol-and-registry-program.md)  
**Depends on:** Slices 4–5  
**Cursor prompt:** `prompts/cursor/next/2026-06-09-1500-entity-research-gate-phase6.md`

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

## Behaviors (locked)

| Resolved entity | `email` requested | Behavior |
|-----------------|-------------------|----------|
| Seed (Andrea Kalmans) | yes | Research runs (unchanged) |
| Registry provisional | yes | No specialists; `found` + gate message |
| Registry validated | yes | Research runs |
| Unknown / unresolved | yes | Slice 1/3 short-circuit (no change) |

**Provisional + attrs message:**  
*"Record is provisionally bound; core validation must complete before researching requested attributes."*

**Outcome when gated with attrs:** `found` if identity resolved; `message` explains gate; `results` identity only, no attr values. **No `research_gated` outcome** — Paul Q6a.

---

## Same-turn validate + research (locked — Paul Q6b)

After Slice 5 validates in one graph run, allow research **in the same run** when validation just completed and `requested_attributes` non-empty.

One turn: **bind → validate → research** if validated.

Implementation: gate checks `validation_state` **after** validation step in supervisor graph order; do not require a second invoke.

---

## Implementation locus

- `supervisor.py` — do not populate `specialists_to_invoke` when gate fails; run validation before gate check when entity is provisional
- `_route_after_supervisor` — unchanged if specialists list empty
- `assemble_response` — `found` + explanatory `message` when attrs requested but gate blocks

---

## Tests (smoke)

- Validated Murphy + email → contact specialist invoked (mock Tavily)
- Provisional Murphy + email (no validation pass) → no invoke
- Provisional Murphy + email, validators pass same turn → invoke (with Slice 5)
- Seed person + email → invoke
- Kalman unresolved + email → no invoke

---

## Paul decisions (locked)

| # | Decision |
|---|----------|
| Q6a | No `research_gated` outcome — `found` + clear `message` |
| Q6b | **Yes, same turn** — research after validation in one graph run |