# Task: Demo admin UI polish v3 — remove Refresh and network_root

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md` (especially **Governance** — do not edit `TODO.md`)
- `admin-ui/src/App.tsx`, `admin-ui/src/styles.css`
- Prior polish: `prompts/cursor/done/2026-06-08-2200-demo-admin-ui-polish-v2/`

**Depends on:** Admin UI polish v2 on `main` (`c025558`).

---

## Governance (mandatory)

- **Do not edit `TODO.md`.** Roadmap updates are for Grok + Paul after review.
- In `output.md`, add **"For Grok + Paul"** with any follow-up notes.
- Cursor delivers: `admin-ui/` changes + `output.md` only.

---

## Workflow (mandatory)

1. **Claim:** move this file from `prompts/cursor/next/` to `prompts/cursor/in-progress/` before edits.
2. **Deliver:** `prompts/cursor/done/2026-06-08-2300-demo-admin-ui-polish-v3/` with `prompt.md`, `output.md`.
3. **Verify:** `cd admin-ui && npm run build`; manual smoke below.
4. **Commit & push** when complete (not `TODO.md`).

---

## Objective

Simplify the demo header for non-engineer audiences: remove the manual **Refresh** button and the **`network_root:`** debug line. The 3s auto-refresh is sufficient for live demos; path info belongs in CLI/`--verbose`, not the default UI.

---

## Requirements (locked)

### 1. Remove Refresh button

- Delete the header **Refresh** `<button>` and any `onRefresh` handler used only for it.
- Delete `loadFull()` if it becomes unused after this change.
- Header keeps: **Mycelium Admin**, health badge, network label (`crm (CRM example)`).

### 2. Remove network_root line

- Delete the muted paragraph: `network_root: {health.network_root}` below the header.
- Do not replace with another path display in the UI.

### 3. Replace manual Refresh behavior (required)

v2 refreshed `/capabilities` (and full health/status) only on **initial load** + **manual Refresh**. With Refresh gone, keep guide/Categories data current without user action:

| Trigger | Silent fetch (no global “Loading…” flash) |
|---------|-------------------------------------------|
| **Tab visible again** | `GET /health`, `GET /status` (current entity/category params), `GET /capabilities` |
| **Ontology appears** | When a status poll sees `ontology_present` flip `false → true`, refetch `GET /capabilities` once |

Implementation notes:

- Reuse existing poll/visibility patterns; avoid overlapping in-flight requests (`statusInFlight` or equivalent).
- **3s interval poll** stays **status-only** (performance) — do not add `/capabilities` every 3s.
- `fetchError` remains for **initial mount** failures only; background/visibility failures use `pollError` (subdued banner).
- Remove `fetchError` code paths that existed only for manual Refresh.

### 4. Do not regress v2

Keep: Categories labels, collapsed guide/entity cards, unified disclosure arrows, uncontrolled specialist `<details>`, `fetchJson` HTML guard, 3s status poll, visibility pause.

---

## Non-goals

- Backend / API changes
- Remove polling
- Add a different “reload” affordance (keyboard shortcut, menu, etc.)
- `TODO.md` edits
- README changes unless Refresh is explicitly documented there (it is not today)

---

## Verification

```bash
cd admin-ui && npm run build

MYCELIUM_NETWORK=crm uv run mycelium-admin    # terminal A
cd admin-ui && npm run dev                      # terminal B
```

**Acceptance:**

1. No Refresh button in header.
2. No `network_root:` line anywhere in the UI.
3. Overview/specialists still update within ~3s after a query (no manual refresh).
4. After ontology is generated (first query on fresh network), Categories panel in guide card populates without page reload and without Refresh (may require tab blur/focus or wait for false→true detection).
5. `npm run build` succeeds.

---

## Scope boundaries (strict)

**May modify:** `admin-ui/src/**` only

**Out of scope:** `TODO.md`, `src/mycelium_admin/`, tests (optional — note in `output.md` if skipped)

---

## Deliverables

1. UI cleanup per requirements above
2. `output.md` with before/after and capabilities-refresh behavior, **"For Grok + Paul"**
3. Commit & push