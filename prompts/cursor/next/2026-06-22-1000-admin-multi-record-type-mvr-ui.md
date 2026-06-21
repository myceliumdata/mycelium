# Admin UI — multi-record-type MVR bind fields (baseball)

> **READY** — Move to `in-progress/` before starting (see `prompts/cursor/WORKFLOW.md`). **Do not edit `TODO.md`.**

## Objective

Fix admin **Run query** lookup forms for networks with **nested** `policy.mvr` capabilities (e.g. **baseball** `player` + `team`). Today `mvrBindFieldsFromPolicy()` only reads flat `policy.mvr.bind_fields`; baseball exposes `default_record_type` + `record_types` (from `load_mvr_config().summary()` in `src/network/introspection.py`). The UI falls back to CRM `["name", "employer"]`, so `./bin/restart-admin baseball` shows the wrong fields.

**Live gate: N/A** — admin-ui + optional daemon smoke only; no example-network catalog changes.

---

## Read first

- `admin-ui/src/mvr.ts` — `mvrBindFieldsFromPolicy`, `DEFAULT_MVR_BIND_FIELDS`, `statusEntityKeyForResolve`
- `admin-ui/src/App.tsx` — `bindFields` from capabilities; `ResolveForm` wiring
- `admin-ui/src/ResolveForm.tsx` — dynamic inputs per bind field
- `admin-ui/src/types.ts` — `MvrPolicy` / `CapabilitiesResponse`
- `src/network/introspection.py` — `build_network_capabilities()` → `policy.mvr` shape
- `src/network/mvr.py` — `NetworkMvrConfig.summary()`
- `examples/networks/baseball/network.json` — player + team bind fields
- `docs/examples/getting-started.md` §6 — one network per daemon (no change to binding model)
- Prior slice: `prompts/cursor/done/2026-06-14-1200-admin-query-unified-mvr-lookup/prompt.md`

---

## Problem (repro)

1. `./bin/refresh-example-network baseball --yes` (or use existing live root)
2. `./bin/restart-admin baseball`
3. Open admin UI → Run query → MVR lookup mode
4. **Bug:** inputs are `Name` / `Employer` instead of `Player` / `Debut team` / `Debut year`; no way to query `team` record type

Daemon `POST /query` is fine — gap is **admin-ui MVR parsing + record-type selection**.

---

## Deliverables

### A. Parse nested MVR capabilities (`admin-ui/src/mvr.ts`)

Extend policy parsing to support **both** shapes:

| Shape | Source | `bind_fields` |
|-------|--------|----------------|
| Legacy flat | Older docs / tests | `policy.mvr.bind_fields` |
| Multi record type | Baseball, future networks | `policy.mvr.record_types[<selected>].bind_fields` |

Add helpers (names illustrative):

- `listRecordTypesFromPolicy(policy)` → `string[]` (empty → treat as single implicit default)
- `defaultRecordTypeFromPolicy(policy)` → `string | null` from `policy.mvr.default_record_type`
- `mvrBindFieldsFromPolicy(policy, recordType?)` → bind fields for selected or default record type

Keep `DEFAULT_MVR_BIND_FIELDS` as **loading fallback only** (comment: CRM placeholder until capabilities load).

Update `statusEntityKeyForResolve` (and related helpers if needed) so display keys work when `name` is not a bind field (prefer first non-empty bind value; do not assume `name` exists).

### B. Record-type selector (`admin-ui/src/App.tsx`)

When `policy.mvr.record_types` has **more than one** key:

- Show a **Record type** `<select>` above resolve form (player / team for baseball)
- Default selection: `policy.mvr.default_record_type`
- Changing record type resets lookup field values (or clears them) and updates `bindFields` passed to `ResolveForm`
- Helper text lists active bind fields for the selected type

Single-record-type networks (crm-seeded, crm-empty, crm-metering): **no selector** — unchanged UX.

### C. Types (`admin-ui/src/types.ts`)

Type `policy.mvr` to reflect nested summary:

```ts
record_types?: Record<string, { bind_fields: string[]; description?: string; ... }>;
default_record_type?: string;
bind_fields?: string[];  // legacy flat
```

### D. Tests

**Required:** pure-function tests for `mvr.ts` (add **vitest** to `admin-ui` devDependencies + `npm test` script):

| Case | Expected bind fields |
|------|---------------------|
| Flat CRM policy | `["name", "employer"]` |
| Baseball default (`player`) | `["player", "debut_team", "debut_year"]` |
| Baseball `team` | `["team"]` |
| Missing/loading policy | CRM fallback |

Run `cd admin-ui && npm test` in verification; `./bin/ci-local` must stay green (`npm run build` still required).

**Optional (nice):** `tests/test_admin_daemon.py` — `GET /capabilities` against a tmp root with copied `examples/networks/baseball/network.json` asserts `policy.mvr.record_types.player.bind_fields` present (API smoke, not UI).

### E. Docs (minimal)

- One line in `docs/examples/baseball/getting-started.md` (or shared getting-started §6): admin Run query supports baseball after this slice; use record-type selector for team vs player.

**Do not** edit `TODO.md`.

---

## Constraints

- **No** multi-network switcher in one admin session — still one daemon per network
- **No** hardcoded baseball strings in React — all from capabilities policy
- Match existing admin-ui patterns (`ResolveForm`, `bindFieldLabel`)
- `npm run build` / `tsc --noEmit` must pass

---

## Verification

```bash
./bin/ci-local
cd admin-ui && npm test

# Manual (Paul/Grok)
./bin/restart-admin baseball
# Player: lookup player=Hank Aaron → step 1 lookup_resolved → step 2 deliver
# Team: select team, lookup team=Boston Red Sox → resolve

./bin/restart-admin crm-seeded
# Still name + employer; no record-type dropdown
```

---

## Output

Per `prompts/cursor/WORKFLOW.md`:

- `prompts/cursor/done/2026-06-22-1000-admin-multi-record-type-mvr-ui/`
- `prompt.md`, `output.md` with verification counts and **For Grok + Paul**
- Do not commit; Grok reviews and commits after **Approved**

**Suggested commit message:** `fix(admin-ui): multi-record-type MVR bind fields for baseball`