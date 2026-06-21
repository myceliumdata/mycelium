# Review — Admin UI multi-record-type MVR bind fields

**Verdict: Approved** (polish nits fixed in follow-up `ad4a6d3`+)

**Slice:** `2026-06-22-1000-admin-multi-record-type-mvr-ui`  
**Reviewer:** Grok  
**Date:** 2026-06-21

---

## CI

| Step | Result |
|------|--------|
| `./bin/ci-local` | **Pass** — ruff clean, admin-ui build ok, **669 smoke passed** (145 deselected) |
| `cd admin-ui && npm test` | **Pass** — 9 vitest cases |

---

## Delivery

`output.md` claims match the working tree. All prompt deliverables present:

- `admin-ui/src/mvr.ts` — nested + flat parsing helpers
- `admin-ui/src/App.tsx` — record-type selector, bind-field wiring
- `admin-ui/src/types.ts` — nested `MvrPolicy` types
- `admin-ui/src/mvr.test.ts` — vitest coverage
- `admin-ui/package.json` + `vite.config.ts` — vitest wired
- `tests/test_admin_daemon.py` — baseball capabilities smoke
- Docs — one line each in shared + baseball getting-started

No scope creep. No `TODO.md` edits.

---

## Diff reviewed

All changed/new files read:

- `admin-ui/src/mvr.ts`
- `admin-ui/src/mvr.test.ts`
- `admin-ui/src/App.tsx`
- `admin-ui/src/types.ts`
- `admin-ui/vite.config.ts`
- `admin-ui/package.json` / `package-lock.json` (vitest dep)
- `tests/test_admin_daemon.py`
- `docs/examples/getting-started.md`
- `docs/examples/baseball/getting-started.md`
- `prompts/cursor/done/2026-06-22-1000-admin-multi-record-type-mvr-ui/output.md`

`/review` subagent not used — diff is focused (~650 lines, single feature).

---

## Spec compliance

| Criterion | Result |
|-----------|--------|
| A. Parse nested MVR (`mvr.ts` helpers) | **Pass** |
| B. Record-type selector when >1 type | **Pass** |
| C. Types for nested `policy.mvr` | **Pass** |
| D. Vitest pure-function tests (4+ cases) | **Pass** (9 cases) |
| E. Minimal docs | **Pass** |
| No multi-network switcher | **Pass** |
| No hardcoded baseball strings in React | **Pass** |
| CRM single-record UX unchanged | **Pass** |
| `npm run build` / tsc | **Pass** |
| Live gate | **N/A** (as specified) |
| Optional daemon smoke | **Pass** |

---

## Legacy / dual-path

- Flat CRM `policy.mvr.bind_fields` still works; `listRecordTypesFromPolicy` returns `[]` → no selector.
- `DEFAULT_MVR_BIND_FIELDS` retained as loading fallback only (comment added).
- `statusEntityKeyForResolve` no longer assumes `name` — uses first non-empty bind field.

Framework infers record type from lookup key shape (`infer_record_type_from_lookup`); admin UI correctly sends only MVR bind-field values (e.g. `team` alone for team type) — no explicit `record_type` in POST body required.

---

## Tests

**Strong:** vitest covers flat CRM, baseball player default, baseball team, missing policy fallback, record-type listing, default type, and `statusEntityKeyForResolve` without `name`.

**Daemon smoke:** `test_capabilities_baseball_mvr_record_types` asserts nested `policy.mvr` shape from real `network.json`.

**Gap (non-blocking):** no integration test that admin query POST with team lookup resolves — acceptable; framework inference is tested elsewhere; manual check still recommended.

---

## Design critique

**Strong**

- Clean separation: policy parsing in `mvr.ts`, UI state in `App.tsx`.
- Selector only when `recordTypes.length > 1` — CRM unchanged.
- Record-type change clears lookup + inspect/query drill-down state.
- Reuses capabilities-driven bind fields; aligns with `NetworkMvrConfig.summary()` shape.

**Acceptable**

- Brief CRM-field flash before capabilities load (pre-existing pattern).
- Record type labels are raw keys (`player`, `team`) — consistent with capabilities, not user-facing polish.

---

## Nits (resolved)

| # | Nit | Fix |
|---|-----|-----|
| 1 | Wire `npm test` into `./bin/ci-local` and `.github/workflows/ci.yml` | Done — vitest runs before admin-ui build |
| 2 | Humanize record-type `<option>` labels | Done — `bindFieldLabel(recordType)` in `App.tsx` |

---

## For Paul

**Commit message (use as-is):**

```
fix(admin-ui): multi-record-type MVR bind fields for baseball
```

**Manual verify before closing baseball admin gap:**

```bash
./bin/restart-admin baseball
# Player: player=Hank Aaron → Run → Deliver
# Team: select team, team=Boston Red Sox → Run → Deliver

./bin/restart-admin crm-seeded
# Still name + employer; no record-type dropdown
```

**TODO (Grok + Paul):** Mark admin multi-record-type MVR UI done; optional website note already mentions record-type selector.

**Push:** Local commit only until Paul requests program push.