# Task: Demo admin UI polish — scannable overview + auto-refresh

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md` (especially **Governance** — do not edit `TODO.md`)
- `admin-ui/src/App.tsx`, `admin-ui/src/styles.css`, `admin-ui/src/format.ts`
- `src/network/introspection.py` — `format_status_demo()` (CLI parity for ✅/❌ lines)
- Demo slice 4 output: `prompts/cursor/done/2026-06-08-1800-demo-slice4-admin-ui/`

**Depends on:** Demo slice 4 (`mycelium-admin-ui` + `mycelium-admin`) on `main`.

---

## Governance (mandatory)

- **Do not edit `TODO.md`.** Roadmap updates are for Grok + Paul after review.
- In `output.md`, add **"For Grok + Paul"** with any follow-up notes.
- Cursor delivers: `admin-ui/` changes, `output.md` only (no backend changes expected).

---

## Workflow (mandatory)

1. **Claim:** move this file from `prompts/cursor/next/` to `prompts/cursor/in-progress/` before edits.
2. **Deliver:** `prompts/cursor/done/2026-06-08-2000-demo-admin-ui-polish/` with `prompt.md`, `output.md`.
3. **Verify:** `cd admin-ui && npm run build`; dev smoke: daemon + `npm run dev`.
4. **Commit & push** when complete (UI only; not `TODO.md`).

---

## Objective

Polish the admin UI so the **default view is scannable** (seed / ontology / specialists status only), secondary panels start **collapsed**, and the overview **auto-updates** as MCP/CLI queries populate specialist storage — without confusing “Filter” patterns or redundant ontology copy.

Paul will test with **dev mode** (`mycelium-admin` + `npm run dev`); no daemon changes required.

---

## Requirements (locked)

### 1. Overview card — three status lines (CLI demo parity)

Replace the current mixed layout with this **fixed order**:

```
✅ Seed (15)          — or count from status.seed_people_count
✅ Ontology           — when status.ontology_present
❌ Ontology           — when not present
✅ Specialists        — when at least one specialist has record_count > 0
❌ Specialists        — when none have storage yet
```

- Use the same ✅/❌ vocabulary as `format_status_demo()` in `introspection.py`.
- **Do not** list ontology categories inline in Overview (moved per §2).
- When **✅ Specialists**, show expandable `<details>` rows below the status line: `category (count)` only — no ontology text inside (per §6).
- Remove the hint text `(expand for storage detail)` (per §4).

### 2. “Network guide & ontology” card — restructure

Keep one card titled **Network guide & ontology**, but:

| Section | Default state | Content |
|---------|---------------|---------|
| **Author guide** | `<details>` collapsed | `guide.md` in `<pre>` when `guide_present`; else `guide_note` / muted empty |
| **Ontology** | `<details>` collapsed | When `ontology.present`: category descriptions + examples from `/capabilities`. When absent: `ontology.message` |

- Move all ontology category listing **out of Overview** into the **Ontology** `<details>` block here (per §1).
- “Category descriptions” must not duplicate as a second always-open block — one collapsible **Ontology** section.

### 3. Default collapsed secondary cards (per §5)

On first load, these must be **collapsed** (`<details>` without `open`, or equivalent):

- **Network guide & ontology** — both inner sections (guide + ontology) collapsed; the outer card may stay visible with a clear heading.
- **Entity lookup** — entire card wrapped in `<details>` collapsed by default; summary line e.g. **Entity lookup**.

**Overview** stays **expanded** and is the hero content.

### 4. Entity lookup tweaks (per §7)

- Category `<select>` first option label: **`All`** (not `Any`). Value remains `""` for unscoped search.
- Keep visible **Category** label beside the select.

### 5. Specialist expand content (per §6)

Inside each specialist `<details>` when expanded, show **storage-only** detail:

- Fields tracked (comma-separated) or empty state
- Optional status counts line: `found N · pending N · n/a N` when any > 0

**Do not** repeat ontology lines (`formatCategoryExamples`, category descriptions) inside specialist expands.

### 6. Auto-refresh (per §8 — Paul confirmed)

Poll the admin API while the app is mounted:

| Setting | Value |
|---------|--------|
| Interval | **3 seconds** |
| Endpoint | `GET /status` (primary); include `entity` / `category` query params when entity lookup is active (same as manual refresh) |
| Tab visibility | Pause polling when `document.hidden` (Page Visibility API); resume when visible |
| UX | **Silent background refresh** — no global `Loading…` flash on poll; keep showing last good data until error |
| Initial load | First fetch may show loading; polls thereafter must not blank the UI |
| Manual Refresh | Keep header button; forces immediate fetch |
| `/capabilities` | Refresh on initial load and manual Refresh only (guide/ontology change rarely); **not** every 3s unless you have a strong reason — document in `output.md` if you add it |

**Preserve UI state across polls:**

- Expanded specialist `<details>` elements stay open (key by `category`).
- Collapsed/expanded state of Entity lookup, guide, and ontology `<details>` unchanged by polls.
- Entity search input values and submitted `entityKey` unchanged.

On poll error: show a subdued error (e.g. banner or muted line); do not crash; retry next interval.

Use `useEffect` + `setInterval` with cleanup, or `requestAnimationFrame`/abort pattern — avoid overlapping in-flight fetches (skip tick if previous request pending).

---

## Non-goals

- Backend / `mycelium-admin` API changes
- WebSocket / SSE
- Write actions, MCP, direct file reads
- Playwright E2E (optional note in `output.md` only)
- Redesign CSS beyond what’s needed for collapsed sections and status lines

---

## Verification

```bash
MYCELIUM_NETWORK=crm uv run mycelium-admin          # terminal A
cd admin-ui && npm run dev                          # terminal B → :5173

# In another terminal, run queries to populate storage:
uv run mycelium query --network crm --entity-key "Andrea Kalmans" --attributes email
```

**Acceptance:**

1. Default view: Overview with three ✅/❌ lines only (+ specialist expands when ✅).
2. Entity lookup + guide/ontology collapsed on load.
3. Ontology categories only inside collapsed Ontology section in guide card.
4. Category dropdown says **All**.
5. Within ~3s of a query completing, specialist row appears/updates **without** manual Refresh and without full-page loading flash.
6. `npm run build` succeeds.

---

## Scope boundaries (strict)

**May modify:** `admin-ui/src/**`, `admin-ui/package.json` only if needed for deps

**Out of scope:** `TODO.md`, `src/mycelium_admin/`, `introspection.py`, tests (unless you add a trivial Vitest for poll helper — optional)

---

## Deliverables

1. Polished UI per requirements above
2. `output.md` with before/after notes, auto-refresh behavior, **"For Grok + Paul"**
3. Commit & push