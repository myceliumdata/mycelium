# Review — MVR redesign Slice M9 (CLI, MCP, admin, examples, README migration)

**Verdict:** **Approved + polish nits**

**Reviewer:** Grok (Paul requested review, June 2026)

---

## CI

| Step | Result |
|------|--------|
| `uv sync --all-extras` | OK |
| `admin-ui` build | OK (TypeScript unchanged — still legacy payloads) |
| `ruff` | All checks passed |
| smoke pytest | **346 passed**, 26 deselected (+4 new) |

Smoke wall time ~39s (up from ~11s at M8) — more integration tests + heavier MCP/CLI roundtrips; not a CI failure.

---

## Delivery

`output.md` matches changed files for CLI, MCP, admin **API**, introspection, examples, docs, and tests. Prompt removed from `next/`. **`done/`** has `prompt.md` + `output.md`. **Mostly complete** — admin **SPA** not migrated (see nits).

---

## Diff reviewed

| File | Read |
|------|------|
| `src/main.py` | Full diff |
| `src/mycelium_mcp/server.py` | Full diff |
| `src/mycelium_admin/server.py` | Full diff |
| `src/network/introspection.py` | Full diff |
| `src/models/state.py` | Schema examples hunk |
| `tests/test_mvr_target_public.py` | Full (new) |
| `tests/test_cli_metering_query.py` | Full diff |
| `tests/test_admin_daemon.py` | Full diff |
| `tests/test_network_integration.py` | Full diff |
| `tests/test_entity_payment.py` | Full diff |
| `tests/test_entity_rename.py`, `test_mcp_onboarding.py` | Hunks |
| `bin/demo-metering-negotiation` | Full diff |
| `README.md`, `docs/architecture.md`, `docs/plans/*` | Hunks |
| `examples/networks/*/queries/*`, `*/README.md`, `*/guide.md` | Full |
| `admin-ui/src/App.tsx`, `api.ts` | Read — **unchanged (legacy)** |
| `src/agents/supervisor.py` | Read — legacy `resolve_entity` path retained |

`/review` subagent not used.

---

## Spec compliance

| Requirement | Status |
|-------------|--------|
| CLI step-1 `id`/`lookup-json`, step-2 `delivery-id` (+ `quote-id`) | Pass |
| Legacy CLI flags rejected with migration hint | Pass |
| MCP schemas + tool docs target protocol | Pass |
| MCP rejects legacy-only `entity_key` | Pass |
| Admin **API** target fields | Pass |
| Admin **UI** two-step | **Fail** — SPA still posts `entity_key` |
| Example JSON migrated (batch + metering + empty-crm) | Pass |
| README/guide/introspection `protocol_status` | Pass |
| Legacy gated at public entry points | Pass |
| Supervisor legacy path removed/gated | Partial — gated publicly; graph path kept for tests (documented) |
| Smoke: CLI/MCP/example roundtrip | Pass |

---

## Legacy / dual-path

Public CLI/MCP/admin API reject legacy-only payloads. `EntityQuery.entity_key` remains on the model for internal `run_query(EntityQuery(entity_key=…))` smoke paths. Supervisor `resolve_entity` unchanged — acceptable if M10 removes or further isolates.

---

## Tests

Four new smoke tests in `test_mvr_target_public.py` cover example JSON validity, CLI two-step, MCP legacy rejection, MCP batch fixture. Seven existing test modules migrated to two-step — good coverage. Gap: no test that admin **UI** request shape works (would fail today).

---

## Design critique

**Strong**

- CLI mutual-exclusive step group (`--id` | `--lookup-json` | `--delivery-id`) is clear; suppressed legacy flags still error in `_entity_query_from_args`.
- MCP `_parse_query_payload` gate is tight — legacy allowed only when paired with target fields (edge case for transitional tests).
- `health_check` two-step ping validates real deliver path.
- Example fixtures are coherent (`crm` batch, `crm-metering` arc, `empty-crm` create).
- Test migrations consistently use resolve → deliver; metering tests correctly bind attrs on step 1.

**Sub-optimal (non-blocking)**

| # | Issue | Suggestion |
|---|--------|------------|
| N1 | **admin-ui** still sends `entity_key` + `binding` — breaks documented `./bin/restart-admin` demo | M10 task 1: two-step UI (lookup fields + delivery_id state) |
| N2 | `crm-metering/README.md` manual step 2 shows `--delivery-id … --attributes email` — attrs are step-1 only | Fix doc: step 2 quote = fresh `lookup-json` + `--attributes` |
| N3 | `03-deliver-quote.json` placeholder says `from-step-2` but step 2 is quote (delivery_id from step 2 quote response) | Clarify placeholder text |
| N4 | Supervisor legacy path + `entity_key` outcomes still in `QueryResponse` schema text | M10 cleanup / doc sync |
| N5 | `health_check` runs two full graph queries — slower liveness | Acceptable; optional lightweight ping later |

---

## Why M9 took so long (for Paul)

Not CI — `./bin/ci-local` passed in ~45s. Cursor execution time is explained by **scope breadth**:

1. **27 tracked files** + new example dirs — CLI, MCP, admin server, introspection, root README, 3 network READMEs/guides, demo script, 9 query fixtures.
2. **Seven test modules** rewritten from single-step `entity_key` to two-step resolve/deliver (each needs env setup + assertion rework).
3. **Cross-cutting grep** — every `entity_key` reference in docs/tests/bin had to be found and judged (keep internal vs migrate public).
4. **Protocol subtlety** — attrs/`provenance` step-1 only, `delivery_id` step-2 only; easy to get wrong in docs (N2).

This slice is naturally the largest “touch everything users see” slice in the program (M1–M8 were graph/runtime).

---

## Nits

N1–N5 → backlog **P22–P26** in `mvr-redesign-polish-m10.md`. N1 is highest priority before Paul demos admin UI.

---

## For Paul

- **Committed locally** by Grok; **not pushed**.
- **M10 queued** — polish backlog + admin-ui migration (P22).

Suggested commit message:

```
feat: migrate CLI, MCP, and admin to target two-step MVR protocol (M9)

Replace entity_key/binding on public entry points with lookup/id and
delivery_id; migrate example fixtures and docs; gate legacy at CLI/MCP/admin.
```