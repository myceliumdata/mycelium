# Admin UI — deferred backlog

Running list of admin UI work deferred while protocol/registry slices focus on **backend only**.  
Review when implementing a dedicated admin polish track.

| # | Source slice | Item | Notes |
|---|--------------|------|-------|
| 1 | Slice 2 | Show `outcome` on query/status surfaces | e.g. badge on entity drill-down, network overview when status reflects last query |
| 2 | Slice 1 | Show `suggestions[]` when outcome is `entity_key_unresolved` | Read-only; help operator debug visiting-agent loops |
| 3 | Slice 3 | Show `required_fields` when outcome is `entity_unknown` | Operator visibility into negotiation state |
| 4 | Slice 4 | Show registry-backed entities (provisional vs seed) | Distinguish bootstrap seed rows from `entities.json` grown rows |
| 5 | Slice 4 | Display `binding` context if ever surfaced via status API | Likely N/A until status API exposes negotiation metadata |
| 6 | Slice 5+ | Validation state per field (`provisional` / `validated`) | Entity field drill-down |
| 7 | Slice 6+ | Indicate when research is gated vs allowed | Operator debugging for Tavily spend |
| 8 | Slice 7 | Show registry vs specialist-owned fields separately | Entity drill-down; bind fields vs extended attrs |
| 9 | Slice 8 | Show `attr_sources` + `last_researched_at` per attribute | Data attribution USP — which specialist, when researched |

Add rows as later slices land. Do not block protocol slices on this file.