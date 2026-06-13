# Task: Admin query UX + step-1 `create_on_deliver` API field

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md` (governance, claiming, **do not commit**)
- `docs/plans/mvr-redesign-program.md` — two-step protocol, create flow table (~line 158)
- `admin-ui/src/App.tsx`, `admin-ui/src/types.ts`
- `src/models/state.py` — `DeliveryPayload`, `QueryResponse`
- `src/agents/responses.py` — `response_lookup_resolved`
- `src/agents/dispatch.py` — step-1 `target_resolve_node`
- `src/agents/target_resolve.py`, `src/agents/target_deliver.py`, `src/network/delivery.py`
- `src/network/mvr.py` — `can_create_on_zero_matches`, `is_full_mvr_lookup`

**Context (Paul + Grok, June 2026):** Post-M10 admin two-step query panel needs polish. Some fixes are already on `main` locally (commits `b6a2a2b`, `8c735a0`). This slice completes the agreed behavior and adds the missing API surface.

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- **Do not commit or push.** Leave changes in the working tree; Grok reviews and commits.
- Deliver `prompts/cursor/done/2026-06-13-2200-admin-query-step1-create-on-deliver/` with `prompt.md` + `output.md`.
- In `output.md`, include **"For Grok + Paul"** with verification notes.

---

## Workflow (mandatory)

1. **Claim:** move this file from `prompts/cursor/next/` to `prompts/cursor/in-progress/` before edits.
2. **Verify baseline:** read current `admin-ui/src/App.tsx` and `src/network/mvr.py` — do not regress behavior already shipped in `b6a2a2b` / `8c735a0` unless this prompt explicitly changes it.
3. **Run:** `./bin/ci-local` green before claiming complete.
4. **Build:** `cd admin-ui && npm run build`.

---

## Objective

Make the admin **explicit two-step** query flow clear for operators and agent/LLM consumers:

1. Step 1 (`lookup_resolved`) shows whether the registry already has matches or step 2 will **create** (full MVR, 0 registry hits).
2. Form fields reset predictably between steps.
3. Step-1 `message` and `delivery.create_on_deliver` align so agents are not misled by “Resolved 0 matches”.

**Non-goals:** auto-deliver (no silent step 2). Paul wants two explicit Run clicks.

---

## Already on `main` (verify, keep unless spec below overrides)

| Behavior | Where |
|----------|--------|
| Full MVR + 0 registry matches → step-1 `lookup_resolved` + create-on-deliver scope (no attrs required) | `src/network/mvr.py` `can_create_on_zero_matches` |
| `type="search"` on all five query inputs (browser clear X) | `admin-ui/src/App.tsx` |
| When `delivery_id` is set in form, request uses deliver path (not lookup fields) | `runQueryRequest` |
| Step 1 fills `delivery_id` → clear name, employer, attributes | `runQueryRequest` |
| Terminal outcomes (`found`, `assembled`, `entity_validated`) → clear `delivery_id` and `quote_id` in form | `runQueryRequest` |
| **No** auto-chained step 2 | `runQueryRequest` |

If any of the above is missing, implement it as part of this slice.

---

## A. API — `delivery.create_on_deliver` (implement)

### Field semantics (locked)

Add optional **`create_on_deliver`** on public **`DeliveryPayload`** (step-1 responses only).

| Value | JSON |
|-------|------|
| Step 2 will create provisional entity from lookup | `"create_on_deliver": true` |
| Existing registry match(es) | **omit field** — do **not** emit `false` |

Paul explicitly rejected redundant `"create_on_deliver": false`.

### Wiring

- Source of truth: `DeliveryScope.create_on_deliver` in `src/network/delivery.py` (already exists).
- Add `DeliveryPayload.from_scope(scope)` (or equivalent) used everywhere step-1 builds a delivery payload:
  - `issue_target_delivery` in `target_resolve.py`
  - `delivery_payload_from_scope` in `target_metering.py`
  - any quote/metering block paths that attach `delivery` to step-1 responses
- Set `create_on_deliver=True` on the payload **only** when `scope.create_on_deliver` is true.

### Serialization (locked)

Public JSON must **omit** `create_on_deliver` when not true. Use `exclude_none=True` (or equivalent) on:

- `src/mycelium_admin/server.py` — `POST /query` response
- `src/mycelium_mcp/server.py` — query tool response JSON
- `src/main.py` — CLI query JSON output

Ensure empty lists like `required_fields: []` still serialize if clients depend on them (do not break existing tests).

### Step-1 `message` strings (locked)

Replace generic “Resolved N matches for lookup” in `response_lookup_resolved` with:

| Case | `message` |
|------|-----------|
| `create_on_deliver` true | `No registry match. Full MVR lookup — step 2 will create a provisional entity, then deliver.` |
| `total_matches == 1` (lookup) | `1 registry match. Use delivery_id on step 2 to deliver.` |
| `total_matches > 1` (lookup) | `{N} registry matches. Use delivery_id on step 2 to deliver.` |
| resolve by `id` | `{N} registry match(es) for id. Use delivery_id on step 2 to deliver.` |

Keep messages one sentence where possible (no admin-style paragraphs).

### Introspection

Update `src/network/introspection.py` target-protocol policy text to mention `delivery.create_on_deliver` (true only when step 2 creates).

---

## B. Admin UI copy (implement)

In `admin-ui/src/App.tsx` result panel for step-1 pending states (`lookup_resolved`, `quote_required`, `payment_required`):

### `total_matches` line

```
total_matches: 1
```

vs create-pending:

```
total_matches: 0 (full MVR)
```

Render `(full MVR)` when `queryResult.delivery?.create_on_deliver === true` (after API ships). Do not infer from `total_matches === 0` alone.

### `delivery_id` line

**Now (wrong):**
```
delivery_id: d_… · Run again to deliver (delivery id is pre-filled).
```

**Target:**
```
delivery_id: d_… · Run again to deliver.
```

Keep showing `delivery_id` only for intermediate outcomes (same gating as today). Do **not** show it on terminal `found` / `assembled` / `entity_validated`.

Update `admin-ui/src/types.ts` — `DeliveryPayload.create_on_deliver?: boolean`.

---

## C. Tests (implement)

Add/update smoke tests:

1. **Create path JSON** — full MVR, unknown person, step 1:
   - `outcome == lookup_resolved`, `total_matches == 0`
   - `delivery.create_on_deliver == true` in model; public JSON has key; existing-match responses do **not**
   - `message` contains `step 2 will create`
2. **Existing match JSON** — e.g. Nichanan Kesonpat @ 1k(x) or seed row:
   - `total_matches >= 1`, no `create_on_deliver` in serialized JSON
   - `message` contains `registry match` and `step 2`
3. **Admin daemon** — extend `tests/test_admin_daemon.py` if needed for HTTP JSON shape (`exclude_none`)
4. Do not regress `tests/test_mvr_create_on_deliver.py` or `test_admin_query_identity_bind_without_attrs`

---

## Acceptance (Paul hands-on)

| Query | Step 1 | Step 2 |
|-------|--------|--------|
| Nichanan Kesonpat @ 1k(x) | `total_matches: 1`, no `(full MVR)`, delivery_id shown, terse message | `found` + results; form tokens cleared |
| Road Runner @ Acme (new) | `total_matches: 0 (full MVR)`, `create_on_deliver` in API, message explains create | `found` + new row; form tokens cleared |
| Either | Lookup fields cleared after step 1; only delivery_id (and quote_id if quoted) remains | — |

---

## Files likely touched

- `src/models/state.py`
- `src/agents/responses.py`
- `src/agents/target_resolve.py`
- `src/agents/target_metering.py`
- `src/mycelium_admin/server.py`
- `src/mycelium_mcp/server.py`
- `src/main.py`
- `src/network/introspection.py`
- `admin-ui/src/App.tsx`
- `admin-ui/src/types.ts`
- `tests/test_mvr_create_on_deliver.py`
- `tests/test_admin_daemon.py`
- possibly `tests/test_mvr_target_resolve.py`

---

## For Cursor output.md

Include:
- Example step-1 JSON for existing vs create-pending
- Confirmation auto-deliver is absent
- CI command + result
- Suggested commit message for Grok (single commit, admin + API together)