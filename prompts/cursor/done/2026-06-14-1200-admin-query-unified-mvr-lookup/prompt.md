# Admin UI — unified query & entity lookup with dynamic MVR fields

> **READY** — Move to `in-progress/` before starting (see `prompts/cursor/WORKFLOW.md`).

**Context (Paul + Grok, June 2026):** After step-1 lookup clarity (`lookup_incomplete`, `lookup_suggested`, `confirm_new_entity`), manual testing exposed admin UX gaps:

1. **Run query** had hardcoded `name` / `employer` inputs — no **registry ID** step-1 path, and no clear signal that step 1 is **id OR lookup** (not both).
2. **Entity lookup** was a separate panel using legacy `GET /status?entity=…` with a single search box — it showed `Required fields: employer` but offered **no employer input**.
3. **MVR bind fields** must be **dynamic** from `capabilities.policy.mvr.bind_fields` — not hardcoded in the React form.

Paul's direction (discussion, locked): one panel, one form pattern, target protocol for resolution, dynamic MVR fields from network policy.

**Note:** Grok prematurely committed `4283906` during discussion; that commit was **reverted** before this slice. Implement fresh here.

**Prerequisites:** `559bee0` (step-1 lookup clarity) on `main`.

---

## Read first

- `admin-ui/src/App.tsx` — current Run query + Entity lookup panels
- `admin-ui/src/api.ts` — `runQuery`, `fetchStatus`, `fetchCapabilities`
- `admin-ui/src/types.ts` — `QueryResponse`, `CapabilitiesResponse`
- `src/mycelium_admin/server.py` — `POST /query`, `GET /status`, `GET /capabilities`
- `src/network/introspection.py` — `build_network_capabilities()` → `policy.mvr.bind_fields`
- `docs/manual-checks/2026-06-13-program2-post-program-gate.md` — Check 0c-vi (update in `output.md` if panel name changes)

---

## Summary — what this slice delivers

### A. Single panel: "Query & entity lookup"

Merge **Run query** and **Entity lookup** into one collapsible card. Remove the duplicate Entity lookup form.

### B. Step 1 — resolve (mutually exclusive)

| Mode | Wire | UI |
|------|------|-----|
| **Registry ID** | `{ id: "<uuid>" }` | Radio + single UUID input |
| **MVR lookup** | `{ lookup: { … } }` | Radio + **dynamic** inputs per `bind_fields` |

- Radio or equivalent: **Registry ID** | **MVR lookup** — only one active.
- Switching mode clears the other mode's values.
- Short helper text: step 1 is **id OR lookup**, not both; step 2 uses `delivery_id`.
- When `delivery_id` is set (step 2), disable step-1 fields.

### C. Dynamic MVR fields (required)

- On load / when capabilities refresh, read `capabilities.policy.mvr.bind_fields` (string array).
- Render one input per bind field (placeholder/label from field name, e.g. `employer` → "Employer").
- Build `lookup` payload only from non-empty bind-field values.
- Fallback while capabilities loading: `["name", "employer"]` (CRM default) — document in code comment.
- Show active bind field list in helper text (e.g. `name, employer`).

**Do not** hardcode `queryName` / `queryEmployer` state long-term — use `Record<string, string>` keyed by bind fields or equivalent.

### D. Step 2 — deliver (unchanged semantics)

- `delivery_id`, optional `quote_id`
- If `delivery_id` present → POST body is step 2 only (no id/lookup)

### E. Resolution flow (target protocol)

- Step 1 submit → `POST /query` (not legacy status-only search).
- Show full query result: outcome badge, `total_matches`, `required_fields`, `suggestions`, `delivery_id`, message, quote panel, results JSON (existing behavior).
- `confirm_new_entity` checkbox when last outcome was `lookup_suggested` (keep existing behavior).

### F. Entity drill-down (status)

After each **step-1** `POST /query` (not step-2 deliver), refresh drill-down:

- `GET /status?entity=<key>&category=…`
- Derive status `entity` key: id mode → UUID; lookup mode → `lookup.name` if set, else first non-empty bind value.
- Show below query results in same panel:
  - Category filter (moves here from old Entity lookup)
  - Match count, single-match metadata, multi-match list
  - Bind/extended field table + version history (unchanged)

Suggestions in query result should fill dynamic lookup fields (and clear confirm flag). Clicking a suggestion should populate bind fields from `entity_key` / `name` / `employer` where those keys exist in `bind_fields`.

### G. Styling (minimal)

- Fieldsets for "Step 1 — resolve" and "Step 2 — deliver"
- Mode radio row; drill-down separated with border
- Reuse existing badge classes (`lookup_incomplete` / `lookup_suggested` → `badge negotiation`)

---

## Implementation sketch

Optional small helper module `admin-ui/src/mvr.ts`:

- `mvrBindFieldsFromPolicy(policy)`
- `buildLookupPayload(lookup, bindFields)`
- `statusEntityKeyForResolve(mode, id, lookup, bindFields)`
- `lookupFromSuggestion(item, bindFields, previous)`

Keep `App.tsx` readable — extract helpers if the diff grows.

---

## Tests

| Test | Assert |
|------|--------|
| `./bin/ci-local` | Green (admin-ui `tsc` + build + smoke) |
| Manual — dynamic fields | `./bin/restart-admin crm` → panel shows inputs matching `policy.mvr.bind_fields` from `/capabilities` |
| Manual — ID resolve | Registry ID mode + Andrea's UUID → `lookup_resolved`, drill-down table |
| Manual — partial lookup | MVR mode, name only → `lookup_incomplete`, `required_fields` includes missing bind fields |
| Manual — full lookup | name + employer → `lookup_resolved` or `lookup_suggested` per Check 0c |

No new Python tests required unless you add admin API changes (prefer UI-only slice).

---

## Scope boundaries (strict)

**May modify:**

- `admin-ui/src/App.tsx`
- `admin-ui/src/api.ts` (only if request typing needs `id` — likely already supported)
- `admin-ui/src/types.ts` (optional `MvrPolicy` typing)
- `admin-ui/src/styles.css`
- New `admin-ui/src/mvr.ts` (optional)
- `docs/manual-checks/2026-06-13-program2-post-program-gate.md` — Check 0c-vi wording only if panel label changed

**Out of scope:**

- `TODO.md`
- Backend query/status protocol changes (unless admin `POST /query` already accepts `id` — it should)
- Legacy `entity_key` graph removal
- MCP changes

---

## Verification

```bash
./bin/ci-local
./bin/restart-admin crm
# http://127.0.0.1:8741/ — Query & entity lookup panel
```

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- In `output.md`, **For Grok + Paul**: screenshots notes, bind_fields source confirmed, gate doc tweak if needed.
- Do not commit or push.

## When finished (mandatory — see WORKFLOW.md §3)

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-14-1200-admin-query-unified-mvr-lookup/`
3. Remove claimed file from `in-progress/` and `next/`
4. Tell Paul **slice ready for review**

---

## Exit criteria

- Single panel replaces duplicate Run query + Entity lookup forms
- Step 1: registry ID **or** dynamic MVR lookup — mutually exclusive and obvious in UI
- Lookup inputs driven by `capabilities.policy.mvr.bind_fields`
- Step 1 uses `POST /query`; drill-down uses `GET /status` after step 1
- Suggestions populate dynamic bind fields
- `./bin/ci-local` green

Suggested commit message:

```
feat(admin-ui): unify query lookup with dynamic MVR fields and ID resolve

Merge query and entity lookup panels; step-1 id OR dynamic MVR lookup from
policy.mvr.bind_fields; target-protocol POST /query with status drill-down.
```