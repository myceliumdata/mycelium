# Admin multi-record-type MVR UI — output

## Summary

Fixed admin **Run query** / **Entity lookup** forms for networks with nested `policy.mvr.record_types` (baseball). The UI now reads bind fields from the selected record type instead of falling back to CRM `name`/`employer`. A **Record type** selector appears when capabilities expose more than one record type; CRM networks are unchanged.

## Changes

| Area | Detail |
|------|--------|
| `admin-ui/src/mvr.ts` | `listRecordTypesFromPolicy`, `defaultRecordTypeFromPolicy`, extended `mvrBindFieldsFromPolicy(policy, recordType?)`; flat + nested shapes; `statusEntityKeyForResolve` no longer assumes `name` |
| `admin-ui/src/App.tsx` | `selectedRecordType` state, selector above `ResolveForm`, bind-field helper text, clears lookup on type change |
| `admin-ui/src/types.ts` | `MvrRecordTypePolicy`, nested `MvrPolicy` fields |
| `admin-ui/src/mvr.test.ts` | 9 vitest cases (CRM flat, baseball player/team, fallback, helpers) |
| `admin-ui/package.json` | `vitest` devDependency + `npm test` script |
| `tests/test_admin_daemon.py` | `test_capabilities_baseball_mvr_record_types` smoke |
| Docs | One line in shared getting-started §6 + baseball getting-started |

## Verification

```text
cd admin-ui && npm test          # 9 passed
cd admin-ui && npm run build     # tsc + vite ok
./bin/ci-local                   # 669 smoke passed, ruff clean, admin-ui build ok
```

## Manual (Paul/Grok)

```bash
./bin/restart-admin baseball
# Player: player=Hank Aaron → Run → Deliver
# Team: select team, team=Boston Red Sox → Run → Deliver

./bin/restart-admin crm-seeded
# Still name + employer; no record-type dropdown
```

## Live gate

**N/A** — admin-ui only; no catalog changes.

## For Grok + Paul

- Mark **2026-06-22-1000** admin multi-record-type MVR UI done.
- Optional follow-up: add `npm test` to `./bin/ci-local` (not required by prompt; tests run manually today).
- Manual baseball admin check recommended before closing baseball program polish.

Suggested commit message:

```
fix(admin-ui): multi-record-type MVR bind fields for baseball
```
