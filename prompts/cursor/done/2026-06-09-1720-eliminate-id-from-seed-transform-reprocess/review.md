# Review — 2026-06-09-1720-eliminate-id-from-seed-transform-reprocess

**Reviewer:** Grok (on behalf of Paul + Grok)

**Overall:** Clean capstone to the redesign. Cursor introduced prepare_seed.py (strips legacy id from CRM→seed), regenerated seed.json (name+employer only), updated loader/supervisor/specialists/storage/tests/docs so public results["id"] == person_id (UUID from name|employer), find_by_key supports name or UUID, old person-XXXX no longer resolve. Verifs and manual queries confirm.

## Strengths
- New data/prepare_seed.py: reads seed_crm, outputs only name+employer to seed.json (no "id" keys ever emitted).
- seed.json: 457 records, confirmed no "id" fields.
- seed.py: _enrich_person only adds person_id (uuid5 name|employer); no seed_id; find_by_key by person_id (exact) or name (case-insens, multi ok).
- supervisor.py: _identity_records_from_seed and _persons_from_seed now set "id" and "person_id" to the UUID (comments reference slice).
- specialists (via template): identity builders use UUID for "id".
- storage/core.py: seed_from_file falls back to _assign_person_id if no "id" (test compat).
- tests: temp seed fixture omits "id"; test_results_are_plain_dicts asserts id == person_id; other tests use name lookup.
- docs: architecture.md, plan doc updated for new seed shape + results "id" = UUID semantics.
- Verifs: python data/prepare_seed.py + assert no id in json; ruff clean; smoke 23p; full 4p (incl. plain dicts); manual CLI: single name query → id==person_id (UUID not person-0001); ambiguous "Kevin Zhang" → 2 distinct UUIDs; grep confirms transform path emits no "id".
- Scope: only seed transform/loader/builders/tests/docs; redesign 1500-1720 complete. No other slices touched.

## Minor Notes / Observations
- architecture.md line ~98 still says "(legacy seed `id` until slice 1720)" — small doc cleanup needed now that 1720 is done.
- Output notes that person_id UUIDs may have changed (pre-1720 used legacy ids), so specialist stores keyed by old UUIDs could be stale (suggest reset-mycelium --specialists if needed). Current workspace/tests use fresh temp seeds, so green.
- Smoke at 23 (consistent with prior slices post-core removal).
- No more prompts in next/ for this redesign queue.

## Follow-up Recommendations (for next Grok/Paul planning)
1. All redesign slices 1500-1720 complete. Consider a final "redesign complete" commit or summary doc update.
2. If using persistent specialist storage from before 1720, run `./bin/reset-mycelium --specialists --yes` to refresh with current person_ids.
3. Future: richer ID strategies, provenance, peer retrieval (as noted in TODOs).

**Status:** Approved. No changes requested. Ready to move forward.

**Next suggested objective for the reset prompt / TODO:** Redesign queue complete (1500-1720). Update any remaining "until 1720" notes in docs; consider end-to-end manual test matrix or commit of the full reprocess set. See existing TODO.md and architecture.md.