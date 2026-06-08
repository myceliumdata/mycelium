# Design conversation: Entity key suggestions & agent negotiation

**Date:** 2026-06-08  
**Participants:** Paul, Grok  
**Status:** Design captured — not yet implemented  
**Distilled in:** `TODO.md` → **Entity key suggestions (protocol slice)** + **Negotiation & metering phases**  
**Related code today:** `src/agents/seed.py` (`find_by_key`), `src/agents/responses.py`, `src/agents/supervisor.py`, `QueryResponse` in `src/models/state.py`

---

## Paul — opening problem

Paul tests frequently with **Andrea Kalmans**. Claude (visiting agent) often “helps” by assuming a typo and querying Mycelium for **Andrea Kalman** (missing the *s*).

**One obvious solution:** fuzzy search — Mycelium silently returns Kalmans’ data for Kalman.

**Paul’s preference:** that feels **wrong**. Mycelium should tell Claude: there is no Kalman, but there is a Kalmans, which may be the entity it’s looking for. The visiting agent decides — no silent rewrite.

**Broader goal:** lay foundations for **agent-to-agent negotiation**. Pricing will eventually follow an **x402** view: cost depends on **what the client needs in total**, not the single datum requested — so back-and-forth is required before commit. Paul expects **~99% of conversations will not include humans**.

---

## Grok — response (substance)

### What happens today

- `find_by_key` is **exact only**: UUID or case-insensitive full name equality.
- `"Andrea Kalman"` → zero matches → `response_not_found`, empty `results`, message like `No record found for 'Andrea Kalman'.`
- No structured hint that `"Andrea Kalmans"` exists.
- Claude then improvises retries — behavior Paul wants Mycelium to own.

### Suggest vs silent fuzzy (different problems)

| Approach | Behavior | Fit |
|----------|----------|-----|
| **Silent fuzzy resolve** | Kalman → return Kalmans’ data | Convenience; bad for trust and billing |
| **Suggest & negotiate** | Kalman → “no exact match; did you mean Kalmans?” | Agent-to-agent loops, x402 |

Paul wants the second. That is **entity resolution with an explicit negotiation outcome**, not retrieval fuzzy-matching.

### Already in the codebase

- `QueryResponse.message` — agent-readable narrative
- `thread_id` — multi-turn sessions
- Multi-match policy — exact name, multiple seed rows → caller disambiguates via `results`
- `debug` with `outcome=not_found` — labeled outcomes internally

### What’s missing (foundation layer)

1. **Resolution before specialists** — `resolve_entity_key(key) → exact | multiple | none | suggest`. On `suggest`: **no specialists, no research**, no Tavily spend.

2. **Machine-readable public outcome** — not prose alone. Example shape discussed:

   ```json
   {
     "outcome": "entity_key_unresolved",
     "results": [],
     "message": "No record for 'Andrea Kalman'. Closest seed match: 'Andrea Kalmans' (id=…). Reply with that entity_key to continue.",
     "suggestions": [
       {
         "entity_key": "Andrea Kalmans",
         "id": "…",
         "name": "Andrea Kalmans",
         "score": 0.92,
         "reason": "edit_distance"
       }
     ],
     "thread_id": "…"
   }
   ```

3. **Contract for visiting agents** — document in `describe_network` / MCP: on `entity_key_unresolved`, caller must re-call `query_entity` with suggested `entity_key` (or future explicit confirm). No attribute data is authoritative until resolution is exact.

### x402 / pricing connection

Multi-phase conversation model discussed:

- **Phase A** — Discover / bind entity (cheap or free)
- **Phase B** — Scope attributes + ontology (quote inputs)
- **Phase C** — Commit + research (paid)
- **Phase D** — Deliver + follow-ups

Kalman/Kalmans is **Phase A**. Silent resolve + email research would commit work on the wrong binding.

Negotiation rounds should stay **cheap until commit**: suggestions and disambiguation do not invoke specialists.

### Match strategy (when implemented)

- Exact match first (unchanged).
- Only on zero exact matches: normalize for **comparison** (whitespace, punctuation — **never** silently rewrite caller’s key).
- Rank: edit distance, token overlap, etc.
- Thresholds: single high-confidence suggestion vs list vs plain `not_found`.
- **Rule:** never return attribute values for a suggested entity until caller confirms.

### Relation to old TODO “fuzzy entity_key matching”

Paul’s clarification **supersedes** vague fuzzy matching: **suggestions + negotiation**, not silent auto-resolve for visiting agents.

### Recommended build (protocol slice)

1. `resolve_entity_key()` + suggestion ranking  
2. `response_entity_unresolved()` with `outcome` + `suggestions[]`  
3. Supervisor short-circuit when unresolved  
4. MCP/CLI schema + `describe_network` policy  
5. Tests: Kalman → suggests Kalmans, no email; corrected key → normal flow  

Open for later spec: outcome enum on `QueryResponse`, confidence floors, `entity_key` retry vs `confirm_suggestion_id`, tie-in to quotes.

---

## Paul — decisions

- Agreed: **protocol slice**, and an **important** one.
- Asked Grok to **update TODO** with conversation context for when we build it.

---

## Grok — TODO action taken

Added **Entity key suggestions (protocol slice — important)** and **Negotiation & metering phases (design)** under `TODO.md` → Protocol & conversation. Committed `95e13c2`.

---

## Open questions (when picking this up)

- Final `outcome` enum values on `QueryResponse`
- Single vs multiple suggestions; confidence floors
- Confirmation: retry with new `entity_key` vs explicit `confirm_suggestion_id`
- How suggestions interact with **unknown** entities (Paul Murphy — see companion conversation doc)
- Metering: which phases are free vs quoted vs paid