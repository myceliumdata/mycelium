# Cancelled — baseball M5 natural language question

**Date:** 2026-06-20  
**Verdict:** Not executed — deferred unlikely.

**Rationale:** Baseball demo clients (Claude + MCP) already map NL → `requested_attributes`. Server-side `EntityQuery.question` duplicates the host LLM without a identified wire-protocol consumer. M4b completes the warehouse derive track.

**Decision record:** [`docs/plans/unlikely/README.md`](../../../../docs/plans/unlikely/README.md)  
**Full design + locks (archived):** [`docs/plans/conversations/2026-06-20-baseball-m5-natural-language-question.md`](../../../../docs/plans/conversations/2026-06-20-baseball-m5-natural-language-question.md)

**Revive:** Grok + Paul explicit re-approval only; re-queue from `prompt.md` if assumptions change.