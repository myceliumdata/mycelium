# Admin UI — restore entity inspect, split query, identical resolve form, layout fix

> **READY** — Move to `in-progress/` before starting (see `prompts/cursor/WORKFLOW.md`).

**Context (Paul, June 2026):** Slice `1200` merged **Run query** and **Entity lookup** into one panel and removed **status-only inspect → drill-down** without approval. Paul asked only for the **same resolve UI** in both places — not one action, not removing browse-only inspection.

**Regression to fix:**

| Capability | Before 1200 | After 1200 (wrong) |
|------------|-------------|-------------------|
| **Entity lookup** | `GET /status` only → drill-down table (`entity_fields`, versions) | Gone — drill-down only after `POST /query` |
| **Run query** | `POST /query` step 1 / step 2 | Same, but Step 1 has **no Run button** (Run lives under Step 2) |

**Paul requirements (locked):**

1. **Two panels** again — **Entity lookup** and **Run query** — with **identical** step-1 resolve form (toggle, fields, spacing).
2. **Entity lookup** = **Inspect** → `GET /status` only (read-only drill-down). **No** `POST /query`.
3. **Run query** = separate **Step 1 Run** and **Step 2 Run deliver** buttons; each calls `POST /query` appropriately.
4. **Layout fix** — mode toggle must clearly scope its inputs; stop cramped/inline-attached fields; attributes placement consistent and readable.

**Prerequisites:** `1200`, `1215`, `1220` on `main`.

---

## Read first

- `admin-ui/src/App.tsx` — current unified panel
- `admin-ui/src/mvr.ts` — bind fields, `statusEntityKeyForResolve`, `buildLookupPayload`
- `admin-ui/src/api.ts` — `fetchStatus`, `runQuery`
- `src/mycelium_admin/server.py` — `GET /status`, `POST /query`
- `src/network/introspection.py` — `build_network_status`
- `prompts/cursor/done/2026-06-14-1200-admin-query-unified-mvr-lookup/review.md` — what was wrongly merged

---

## A. Two panels, one shared resolve form

Extract a shared component (e.g. `ResolveForm` in `admin-ui/src/ResolveForm.tsx` or inline helper) used by **both** panels:

| Control | Both panels |
|---------|-------------|
| Radio | **Registry ID** \| **MVR lookup** (mutually exclusive) |
| ID mode | Single UUID input |
| Lookup mode | Dynamic inputs from `mvrBindFieldsFromPolicy(capabilities.policy)` |
| Mode switch | Clears other mode; lookup mode clears `confirm_new_entity` when switching to ID (keep `1220` behavior) |

**Query panel only:** `requested_attributes` input + `confirm_new_entity` checkbox (after `lookup_suggested`).

**Entity lookup panel only:** no attributes, no confirm, no step 2.

Visual structure must be **identical** for the shared resolve block (same DOM/CSS classes).

---

## B. Entity lookup panel — restore inspect

**Summary label:** `Entity lookup` (not merged title).

**Action:** **Inspect** button (not “Run”, not form submit that hits query).

**Behavior:**

1. Read shared resolve form state.
2. **ID mode:** `GET /status?entity=<uuid>` (+ optional `category` filter).
3. **Lookup mode:** `GET /status` with **lookup map** — see §C (backend).
4. **Do not** call `POST /query`. **Do not** populate `queryResult`.
5. Show drill-down below: match count, multi-match list, `entity_fields` table + version history (existing markup).

Category filter stays in this panel (or directly above drill-down), same as today.

---

## C. Backend — status must understand MVR lookup map (required)

`GET /status?entity=…` today uses legacy `resolve_entity_for_lookup(entity_key)` — **single string**, not target `lookup` map. That is insufficient for identical MVR lookup UI (name + employer).

**Extend admin status endpoint:**

```text
GET /status?lookup={"name":"Andrea Kalmans","employer":"Lontra Ventures"}
```

(or equivalent: JSON-encoded `lookup` query param; document in handler).

**In `build_network_status` (or small helper):**

- If `lookup` param non-empty (and `entity` empty): use `registry.lookup_by_target_lookup(lookup)` read-only.
  - 1 match → populate `entity_fields` drill-down for that row (same as today’s single-match path).
  - 0 matches → `entity_matches=0`; optional `entity_resolution_kind` / message; no graph.
  - 2+ matches → `entity_match_summaries`, no `entity_fields` until narrowed.
- If `entity` param set: keep existing legacy path (backward compatible).
- **Never** create, deliver, or run graph on status path.

Add smoke test in `tests/test_admin_daemon.py`: `GET /status?lookup=…` returns 1 match + expected shape for seeded Andrea.

Update `admin-ui/src/api.ts` `fetchStatus` to accept optional `lookup` object.

---

## D. Run query panel — restore step buttons

**Summary label:** `Run query`.

**Step 1 fieldset** — resolve form (shared) + attributes + **Run** button:

- Button label: **Run** or **Resolve** (step 1).
- Handler: `POST /query` with `id` or `lookup` only — **no** `delivery_id`.
- Show `queryResult` (outcome, suggestions, required_fields, delivery_id, etc.).
- Optional: after step-1 success, refresh drill-down via status (lookup param or entity id) — query panel may show a compact drill-down OR Paul may prefer query outcomes only; **default:** refresh status for single-match convenience using same lookup/id as inspect would.

**Step 2 fieldset** — separate:

- `delivery_id`, `quote_id`
- Button label: **Deliver** (not the only Run on the page).
- Handler: `POST /query` with `delivery_id` (+ optional `quote_id`).
- `confirm_new_entity` checkbox adjacent to step 1 when `lookup_suggested` (lookup mode only — keep `1220`).

When `delivery_id` is non-empty, disable step-1 fieldset (keep current `step2Active` idea).

**Critical:** Step 1 must have its **own** visible button inside the Step 1 fieldset — not only under Step 2.

---

## E. Layout fix (Paul: “really ugly”)

Current problems: attributes inline with ID input; MVR fields in a different visual row; inputs visually attached without spacing; unclear what the radio toggles.

**Required layout (both panels, shared resolve block):**

```
┌─ Step 1 — Resolve by ─────────────────────────┐
│  ( ) Registry ID   ( ) MVR lookup             │
│                                               │
│  ┌─ [mode-specific inputs — full width] ─┐   │
│  │  ID: one input per row OR              │   │
│  │  MVR: one bind field per row (stacked) │   │
│  └────────────────────────────────────────┘   │
└───────────────────────────────────────────────┘
```

**Query panel adds below shared block:**

```
│  Requested attributes: [____________]         │
│  [ Run ]                                      │
```

**Entity lookup adds:**

```
│  [ Inspect ]                                  │
```

**CSS guidance (`admin-ui/src/styles.css`):**

- `.resolve-inputs` — `display: flex; flex-direction: column; gap: 0.5rem; width: 100%;`
- Each input `width: 100%` or `min-width` with consistent max-width inside panel
- Radio row separated from inputs with margin
- Step fieldsets visually distinct; buttons not crammed in `row-actions` with inputs on one line unless deliberate for step 2 delivery ids only
- No bare sibling inputs without a wrapper — fixes “attached” look

Paul should be able to tell at a glance: radios choose **what appears in the box below**.

---

## F. State / wiring

- **Separate state or clear handlers** so Inspect does not set `queryResult` and Query Inspect does not conflate outcomes.
- Shared resolve form state: either lifted to parent and passed to both panels, or duplicate state synced — prefer **one shared state object** in `App.tsx` passed to both panels so fields stay identical when user switches panels.
- Polling `fetchStatus(statusQueryParams())` should respect entity lookup’s last inspect key (restore `entityKey` set on Inspect only, not only after query).

---

## Scope

**May modify:**

- `admin-ui/src/App.tsx`, new `ResolveForm.tsx` (optional), `admin-ui/src/api.ts`, `admin-ui/src/styles.css`
- `src/mycelium_admin/server.py` — `GET /status` lookup param
- `src/network/introspection.py` — lookup-aware status build
- `tests/test_admin_daemon.py`
- `docs/manual-checks/2026-06-13-program2-post-program-gate.md` — split Check 0c-vi: entity inspect vs query (brief)

**Out of scope:** `TODO.md`, MCP, CLI changes.

---

## Verification

```bash
./bin/ci-local
./bin/restart-admin crm
```

| Check | Pass |
|-------|------|
| Entity lookup → Andrea by name → **Inspect** → drill-down table, **no** network call to `POST /query` (DevTools) |
| Entity lookup → full MVR lookup map → Inspect uses `GET /status?lookup=…` |
| Run query → Step 1 **Run** visible in step 1 fieldset → `lookup_resolved` / etc. |
| Run query → Step 2 **Deliver** → step 2 only |
| Both panels: identical resolve form layout |
| Registry ID / MVR toggle layout readable |

---

## Governance

- Do not edit `TODO.md`.
- `output.md` → **For Grok + Paul**: confirm inspect restored; note layout; gate doc tweaks.
- Do not commit or push.

## When finished

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-14-1300-admin-restore-inspect-split-query-layout/`
3. Remove from `in-progress/` and `next/`
4. Tell Paul **slice ready for review**

---

## Exit criteria

- Two panels; identical shared resolve UI
- Entity lookup = Inspect → status only + drill-down
- Query = Step 1 Run + Step 2 Deliver buttons
- Layout: toggle clearly scopes inputs; no ugly inline cramming
- `GET /status` supports lookup map for inspect parity
- `./bin/ci-local` green

Suggested commit message:

```
fix(admin-ui): restore entity inspect panel and split query step buttons

Two panels share identical resolve form; Inspect uses GET /status with lookup
map; query has separate Step 1 Run and Step 2 Deliver; layout cleanup.
```