# Task: Update all documentation to reflect query-only public interface and proper core data agent

## Objective
Revise user-facing and architectural documentation to match the new reality: public interface supports only queries; there is now (or will be after wiring) a proper `core_data_agent` specialist for core data management. Remove or clearly mark as "future / internal only" all references to public ingestion, the old enrich/validator loop for adds, and the unified ingest handshake.

## Files to touch (at minimum)
- README.md
- docs/architecture.md
- docs/full-code-walkthrough.md
- Any other .md files that have prominent ingest language (e.g. TODO.md if it still lists public ingest items)

## Constraints
- Keep the architectural vision (supervisor as thin coordinator, specialists for core and non-core).
- Clearly state that data addition is being removed from public for now and will return later via internal agent coordination.
- The "Core Ingestion Handshake" section in architecture.md should be rewritten or moved to a "Future Work" note.
- Update diagrams and flow summaries that showed the ingest path.
- Mention that `core_data_agent` (in `src/agents/core_data.py`) is the new home for core data logic.

## Exact Steps (suggested order)
1. Start with `docs/architecture.md`:
   - Rewrite the Core Ingestion Handshake section into a short "Future" note.
   - Update the flow table (remove or footnote the Ingest row).
   - Update any text about public adding of records.
   - Add a sentence about the new core data agent.
2. Update `README.md`:
   - Change the opening sentence if it mentions ingest routing.
   - Remove or comment the ingest CLI example (or mark it as "to be re-added").
   - Update the "Local Debugging with Studio" section to remove "full ingest path", "enrich, and validator nodes" language.
   - Clean any other references.
3. Update `docs/full-code-walkthrough.md`:
   - This is the longest; focus on the sections that explain the graph, the ingest trace, enrich/validator roles, and the "unified PersonQuery for ingest".
   - Rewrite explanations so they describe the current query-only graph using supervisor + core_data_agent.
   - Keep historical context if it helps understanding, but clearly label what has changed.
4. Touch TODO.md if it still talks about public ingest follow-ups; move them under a "Re-adding data addition" heading.
5. Run a quick grep across the repo for "ingest", "provided_data", "submit_person_data", "enrich_agent" etc. in *.md files and clean the remaining ones.
6. Do not edit source code in this task (that's for the code tasks).

## Required Output
- Diffs or before/after excerpts in the output.md.
- Confirmation that the main docs no longer promise public ingest.
- A clear statement in architecture.md that "public interface is query-only; core data is now owned by the CoreDataAgent specialist".

Claim the file from next/ into in-progress/ before starting edits.
