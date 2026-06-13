# MVR redesign — Slice M8 (batch deliver + batch provenance)

**Program:** [`docs/plans/mvr-redesign-program.md`](../../docs/plans/mvr-redesign-program.md)  
**Prerequisite:** M7 reviewed and approved  
**Depends on:** M5–M7 step-2 deliver, create-on-deliver, metering batch pricing (M6)

---

## Objective

Harden **batch step-2 deliver** (N entities in `DeliveryScope`) and implement **`provenance.entities[]`** shape when step-1 scope had `provenance=true` across multiple results. Ensure research/assembly runs for all N matches (R9).

**Not in M8:** CLI/MCP migration (M9), polish pass (M10).

---

## Read first

- [`docs/plans/mvr-redesign-program.md`](../../docs/plans/mvr-redesign-program.md) — R9 batch rules
- [`src/agents/query_provenance.py`](../../src/agents/query_provenance.py)
- [`src/agents/dispatch.py`](../../src/agents/dispatch.py) — `_attach_provenance`, multi-match deliver
- M7: [`src/agents/target_deliver.py`](../../src/agents/target_deliver.py)

---

## Tasks

1. **Batch deliver** — verify/fix N-row `results[]` for multi-entity scopes with and without attrs; no silent truncation.

2. **Batch provenance** — when `delivery_scope_provenance` and N > 1, return structured `provenance.entities[]` per program doc (not single-entity shape).

3. **Create + batch** — create-on-deliver remains N=1; document; ensure batch paths do not break it.

4. **Tests** — smoke: 3-match deliver with attrs; provenance across batch; optional metered batch quote roundtrip.

---

## Constraints

- **Do not edit `TODO.md`.**
- **Do not** migrate CLI/MCP to target protocol (M9).

---

## Governance (mandatory)

- **Do not edit `TODO.md`.** Roadmap updates are for Grok + Paul after review.
- In `output.md`, add **"For Grok + Paul"**: what to check off, any roadmap notes.
- Cursor delivers: code, tests, task-scoped docs, and `output.md` only.

## When finished (mandatory)

1. `./bin/ci-local` green — record counts in `output.md`
2. Create `prompts/cursor/done/2026-06-13-1700-mvr-redesign-slice-m8/` with `prompt.md` + `output.md`
3. Every file in `output.md` must exist on disk
4. Remove claimed prompt from **`in-progress/`** and **`next/`**
5. **Do not `git commit` or `git push`**
6. Tell Paul: **"slice ready for review"**

See `prompts/cursor/WORKFLOW.md` §3.

---

## Verification

```bash
./bin/ci-local
```

---

## Output

`prompts/cursor/done/2026-06-13-1700-mvr-redesign-slice-m8/` — note M9 queue hint in **For Grok + Paul** only.

Do not commit until Grok review.

---

## Exit criteria

- N-entity deliver returns N `results[]` rows with attrs
- Batch `provenance.entities[]` when requested on step 1
- Smoke green
