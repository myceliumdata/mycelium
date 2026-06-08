# Task: Demo admin UI polish v2 — labels, collapse, arrows, specialist expand fix

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md` (especially **Governance** — do not edit `TODO.md`)
- `admin-ui/src/App.tsx`, `admin-ui/src/styles.css`, `admin-ui/src/api.ts`
- Prior polish output: `prompts/cursor/done/2026-06-08-2000-demo-admin-ui-polish/`

**Depends on:** Admin UI polish v1 + `bin/restart-admin` on `main` (`3b36a4e`, `cd78f86`, `df32d09`).

---

## Governance (mandatory)

- **Do not edit `TODO.md`.** Roadmap updates are for Grok + Paul after review.
- In `output.md`, add **"For Grok + Paul"** with any follow-up notes.
- Cursor delivers: `admin-ui/` changes + `output.md` only.

---

## Workflow (mandatory)

1. **Claim:** move this file from `prompts/cursor/next/` to `prompts/cursor/in-progress/` before edits.
2. **Deliver:** `prompts/cursor/done/2026-06-08-2200-demo-admin-ui-polish-v2/` with `prompt.md`, `output.md`.
3. **Verify:** `cd admin-ui && npm run build`; manual smoke below.
4. **Commit & push** when complete (not `TODO.md`).

---

## Objective

Fix Paul-reported bugs and UI nits from hands-on testing after polish v1. Keep the scannable Overview + 3s silent poll behavior from v1; do not regress auto-refresh or collapsed-by-default secondary panels.

---

## Requirements (locked)

### 1. Rename “Ontology” → “Categories” (UI labels only)

| Location | Change |
|----------|--------|
| Overview status line | `✅ Categories` / `❌ Categories` (was “Ontology”) |
| Guide card inner `<summary>` | **Categories** (was “Ontology”) |
| Card title | Stays **Network guide & ontology** |
| Entity lookup filter | Keep **Category** label and **All** option — unchanged |
| Backend / API field names | No changes (`ontology_present`, `/capabilities.ontology`, etc.) |

### 2. Collapse “Network guide & ontology” card (Paul’s original item 5)

Match **Entity lookup** pattern:

- Wrap the entire guide card in `<details className="card collapsible-card">` with `<summary className="collapsible-summary">Network guide &amp; ontology</summary>`.
- **Collapsed on first load** (`open={false}` or uncontrolled closed — same approach as Entity lookup).
- Inner **Author guide** and **Categories** subsections remain separate nested `<details>`, also collapsed on load.
- Remove the always-visible outer `<section className="card">` + `<h2>` pattern.

**Overview** stays always visible (not wrapped in `<details>`).

### 3. Unified disclosure arrows (all `<details>` summaries)

Paul reports outer card arrows (Entity lookup, and guide card once wrapped) are **smaller** than inner row arrows (Author guide, Categories, specialists).

**Fix:** one consistent disclosure style for every `<summary>` in the app:

- Hide native `::-webkit-details-marker` on **all** summaries (outer cards, inner sections, specialist rows).
- Use a shared class (e.g. `.disclosure-summary` or extend `.collapsible-summary`) with `::before` triangle `▸` / `▾` at a **visible size** (target: match or exceed native marker — e.g. `font-size: 1.1em` on the arrow pseudo-element, or explicit `▸` with consistent spacing).
- Apply to: Entity lookup, Network guide & ontology (outer), Author guide, Categories, specialist rows.
- Specialist rows may keep `.specialist-details` for layout but must use the **same arrow** as other summaries.

Do not change typography/weight of summary text beyond what’s needed for arrow alignment.

### 4. Fix specialist expand bug (blocking)

**Symptom:** Clicking a collapsed specialist row in Overview shows/replaces the page with raw `index.html` SPA shell (Paul report).

**Root cause (likely):** Controlled `<details open={...} onToggle={...}>` on specialist rows fights native toggle under React — polish v1 added `specialistExpanded` state for poll preservation.

**Fix (required):**

1. **Specialist rows → uncontrolled `<details>`** — remove `open` and `onToggle` props and delete `specialistExpanded` state (or stop using it for specialists).
2. Keep `key={spec.category}` so React reuses the same DOM node across 3s poll re-renders; browser-native open state must persist without controlled `open`.
3. Do **not** remount specialist rows on poll (stable keys, no `key` tied to changing record counts).

**Hardening (required):** In `admin-ui/src/api.ts` `fetchJson`:

- After `response.ok`, read `Content-Type` (or peek body): if response is HTML (e.g. `text/html` or body starts with `<!`), throw a short error like `Expected JSON from ${path}, got HTML — is mycelium-admin running?` — **do not** surface the full HTML document in error UI.
- Truncate any error message bodies to ~200 chars max before throwing.

**Verify specialist expand** in `output.md`:

```bash
# Dev
MYCELIUM_NETWORK=crm uv run mycelium-admin          # terminal A
cd admin-ui && npm run dev                            # terminal B → :5173

# Demo (optional)
cd admin-ui && npm run build
MYCELIUM_NETWORK=crm uv run mycelium-admin            # :8741 serves dist
```

With at least one specialist with `record_count > 0`: click `contact (N)` (or similar) → expands in place showing fields tracked; **no** full-page navigation; **no** raw HTML in error banner.

### 5. Preserve v1 behavior (do not regress)

| Behavior | Keep |
|----------|------|
| 3s silent `/status` poll | Yes |
| Pause poll when `document.hidden` | Yes |
| `statusInFlight` skip | Yes |
| Manual Refresh → `fetchError`; poll failures → `pollError` | Yes (already split in `cd78f86`) |
| Entity lookup collapsed on load | Yes |
| Category dropdown **All** | Yes |
| Overview three status lines only (+ specialist expands when ✅) | Yes |
| `/capabilities` on initial + manual Refresh only | Yes |

**Outer cards** (Entity lookup, guide card): controlled `open` + `onToggle` is acceptable **if** expand/collapse works reliably. Prefer fixing specialist rows first; simplify other controlled details only if still broken after testing.

---

## Non-goals

- Backend / `mycelium-admin` API changes
- Rename API fields or CLI “ontology” vocabulary
- Card title rename (“Network guide & ontology” stays)
- Playwright E2E (note in `output.md` only)
- `TODO.md` edits

---

## Verification

```bash
cd admin-ui && npm run build
```

**Acceptance checklist:**

1. Overview: `✅/❌ Categories` (not “Ontology”).
2. Entity lookup + Network guide & ontology: both outer cards collapsed on load; expand/collapse works.
3. All disclosure arrows visually consistent size (outer ≥ inner).
4. Specialist row click expands storage detail in place (dev `:5173`); no `index.html` flash.
5. Poll still updates specialist list within ~3s after a query.
6. `npm run build` succeeds.

---

## Scope boundaries (strict)

**May modify:** `admin-ui/src/**` only

**Out of scope:** `TODO.md`, `src/mycelium_admin/`, `introspection.py`, tests (optional trivial unit test for `fetchJson` HTML guard — note in `output.md` if skipped)

---

## Deliverables

1. UI fixes per requirements above
2. `output.md` with before/after, specialist-expand repro result, **"For Grok + Paul"**
3. Commit & push