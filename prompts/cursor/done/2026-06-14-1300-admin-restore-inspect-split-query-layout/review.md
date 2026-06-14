# Review: 2026-06-14-1300-admin-restore-inspect-split-query-layout

**Verdict: Approved + polish nits**

## CI

| Step | Result |
|------|--------|
| `./bin/ci-local` (Grok, 2026-06-14) | **Pass** — 405 smoke passed, 26 deselected; ruff clean; admin-ui build ok |
| Cursor `output.md` claim | 405 passed — matches |

## Delivery

| Artifact | Present |
|----------|---------|
| `admin-ui/src/ResolveForm.tsx` (shared resolve block) | ✅ |
| `admin-ui/src/EntityDrilldown.tsx` (extracted drill-down) | ✅ |
| Two panels: Entity lookup + Run query | ✅ |
| `GET /status?lookup=…` backend + `fetchStatus` wire | ✅ |
| `test_status_lookup_map_single_match` | ✅ |
| Gate doc Check 0c-vi split | ✅ |
| `prompt.md` / `output.md` | ✅ |

## Diff reviewed

- `admin-ui/src/App.tsx`
- `admin-ui/src/ResolveForm.tsx` (new)
- `admin-ui/src/EntityDrilldown.tsx` (new)
- `admin-ui/src/api.ts`
- `admin-ui/src/mvr.ts`
- `admin-ui/src/styles.css`
- `src/agents/entity_resolution.py`
- `src/mycelium_admin/server.py`
- `src/network/introspection.py`
- `tests/test_admin_daemon.py`
- `docs/manual-checks/2026-06-13-program2-post-program-gate.md`
- `prompt.md`, `output.md`

`/review` subagent not used — diff is large but cohesive; full read completed.

## Spec compliance

| Exit criterion | Pass |
|----------------|------|
| Two panels; identical shared resolve UI | ✅ |
| Entity lookup = Inspect → `GET /status` only + drill-down | ✅ |
| Run query = Step 1 **Run** + Step 2 **Deliver** | ✅ |
| Layout: toggle scopes stacked inputs; no inline cramming | ✅ |
| `GET /status` supports MVR lookup map | ✅ |
| `./bin/ci-local` green | ✅ |

## Legacy / dual-path

| Check | Pass |
|-------|------|
| `GET /status?entity=…` legacy path unchanged | ✅ |
| `POST /query` step 1/2 semantics preserved | ✅ |
| `confirm_new_entity` lookup step-1 only (1220) | ✅ |
| Polling respects last inspect or query drill-down key | ✅ |

## Tests

| Test | Coverage |
|------|----------|
| `test_status_lookup_map_single_match` | Single-match lookup map, bind fields, `entity_key` display — good smoke coverage |
| Gap | No smoke for 0-match / multi-match `lookup` param (non-blocking) |

## Design critique

**Strong:** Correct fix for the 1200 regression — inspect and query are separate actions again with one shared resolve state. `ResolveForm` + `EntityDrilldown` extraction shrinks `App.tsx` and keeps DOM/CSS identical across panels. `resolve_status_for_target_lookup()` is appropriately read-only and mirrors query resolution without graph side effects. `statusQueryParams()` gating (poll only when inspect or query drill-down active) avoids polluting overview polling.

**Sub-optimal (non-blocking):** `applySuggestion` updates form fields only — user must click **Inspect** again to refresh entity-lookup drill-down (pre-1200 auto-fetched status). Acceptable for now; slightly worse UX in the inspect panel.

## Nits

| # | Nit | Severity |
|---|-----|----------|
| N1 | Clicking a drill-down suggestion does not re-run Inspect (fields update only) | Polish |
| N2 | Step 1 **Run** sits in the same flex row as attributes; spec diagram showed Run on its own line below attributes | Polish |
| N3 | Malformed `lookup` JSON on `GET /status` is silently ignored (falls back to network overview) | Polish |

Program polish backlog: no active doc for Program 2 admin slices (MVR/entity-protocol backlogs closed) — nits logged here only.

## For Paul

**Commit message:**

```
fix(admin-ui): restore entity inspect panel and split query step buttons

Two panels share identical resolve form; Inspect uses GET /status with lookup
map; query has separate Step 1 Run and Step 2 Deliver; layout cleanup.
```

**Next:** Run Program 2 manual gate Check 0c-vi (inspect vs query split). Queue empty.

**Git:** Local commit only — no push until you ask.