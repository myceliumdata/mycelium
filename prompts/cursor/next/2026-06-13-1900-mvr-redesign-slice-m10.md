# MVR redesign — Slice M10 (polish + doc sync + admin-ui)

**Program:** [`docs/plans/mvr-redesign-program.md`](../../docs/plans/mvr-redesign-program.md)  
**Prerequisite:** M9 reviewed and approved  
**Backlog:** [`docs/plans/mvr-redesign-polish-m10.md`](../../docs/plans/mvr-redesign-polish-m10.md) (P1–P26)

---

## Objective

Close the **M1–M9 polish backlog** and finish remaining public-surface gaps (especially **admin-ui** two-step migration). Sync docs, add missing smoke tests, and retire or isolate legacy `entity_key` graph paths where safe.

**This is the final MVR redesign slice** before program push.

---

## Read first

- [`docs/plans/mvr-redesign-polish-m10.md`](../../docs/plans/mvr-redesign-polish-m10.md) — all open rows
- [`admin-ui/src/App.tsx`](../../admin-ui/src/App.tsx), [`admin-ui/src/api.ts`](../../admin-ui/src/api.ts) — **P22**
- [`examples/networks/crm-metering/README.md`](../../examples/networks/crm-metering/README.md) — **P23**
- [`src/agents/supervisor.py`](../../src/agents/supervisor.py) — legacy path **P25**
- [`src/agents/responses.py`](../../src/agents/responses.py) — `partition_attribute_buckets` **P18**

---

## Tasks (priority order)

1. **admin-ui two-step (P22)** — Replace entity-key form with lookup fields (name, employer); show `delivery_id` from step-1 `lookup_resolved`; step-2 deliver with stored id + optional `quote_id`; update `api.ts` / types.

2. **Doc fixes (P23, P24, P17, P21)** — Correct `crm-metering` manual CLI steps; architecture slice bullets; fixture placeholder text.

3. **Backlog smoke/tests (P7, P12, P13, P16, P19)** — Add targeted smoke where missing (metered create, principal/payment on target path, provenance-only quote, batch identity-only deliver).

4. **Code polish (P1, P4, P10, P11, P14, P18, P25)** — Shared env util; `mvr.bind_fields` generalization where still hard-coded; `partition_attribute_buckets` per-entity; legacy path isolation; typing/helpers as listed in backlog.

5. **Schema/doc pass (P2, P15)** — `QueryResponse` legacy outcome strings; `EntityQuery.id` naming notes.

Work backlog rows in table order where practical; mark waived rows in `output.md` with reason.

---

## Constraints

- **Do not edit `TODO.md`.**
- **Do not** start Program 2 (versioned bind storage).
- Prefer small, focused fixes — no drive-by refactors outside backlog rows.

---

## Governance (mandatory)

- **Do not edit `TODO.md`.** Roadmap updates are for Grok + Paul after review.
- In `output.md`, list **closed backlog row ids** (P1–P26) and any waivers.
- Cursor delivers: code, tests, task-scoped docs, and `output.md` only.

## When finished (mandatory)

1. `./bin/ci-local` green — record counts in `output.md`
2. Create `prompts/cursor/done/2026-06-13-1900-mvr-redesign-slice-m10/` with `prompt.md` + `output.md`
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

## Exit criteria

- P22 admin-ui two-step works against admin API (manual or smoke)
- All backlog rows addressed or explicitly waived in `output.md`
- `./bin/ci-local` green