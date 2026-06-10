# Task: Seed elimination — Polish (vocabulary + code nits)

> **READY** — **Run after Slices 17–18 are reviewed** (may be uncommitted — Paul batches one commit stack after polish is approved). Move to `in-progress/` before starting.

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/entity-seed-elimination-phase.md`](../../docs/plans/entity-seed-elimination-phase.md) — phase context
- Slice 18 review nits: `prompts/cursor/done/2026-06-10-1800-entity-seed-elimination-slice18/review.md`
- Slice 17 review nits: `prompts/cursor/done/2026-06-10-1700-entity-seed-elimination-slice17/review.md`
- Slice 16 review nits: `prompts/cursor/done/2026-06-10-1600-entity-seed-elimination-slice16/review.md`

**Depends on:** Slices 17–18 WIP in working tree (seed module deleted, entities-only operator surfaces, full pytest green).

**Do not redo Slice 17–18 work.** If an item is already fixed, skip and note in `output.md`.

---

## Objective

Clean up **remaining seed-runtime vocabulary** and small code-quality nits after the seed-elimination phase. Add a committed **empty-seed CRM example** (`empty-crm`) demonstrating query-time entity growth. Close the **Slice 16–18 review nit backlog** below. No behavior changes unless required for renamed public docstrings; smoke and full pytest must stay green.

---

## Nit backlog (from Grok reviews — implement in this slice)

| Source | Nit | Polish item |
|--------|-----|-------------|
| Slice 18 | `src/main.py` help still says "seed record" | P1 |
| Slice 18 | `admin-ui/dist/` stale vs `App.tsx` (Entities-only) | P8 — rebuild for `--demo`; **do not commit** dist |
| Slice 18 | `src/mycelium.egg-info/PKG-INFO` stale curl (`seed_people_count`) | P8 — regen via editable install |
| Slice 17 | `docs/full-code-walkthrough.md` still references `agents.seed` | P5 |
| Slice 17 | CLI help strings | P1 |
| Slice 16 | `build_full_context(..., seed_records=)` param name | P4 |
| Slice 15 | `registry._data` peek in suggestions | P3 |
| Slice 16 | `SeedRecord` / state field renames | **Deferred** — docstrings only (P2) |
| TODO Q8b | Empty-seed committed example | P7 |

---

## P1 — CLI + MCP operator strings

Update user-facing help/docstrings that still imply query-time seed loading:

| File | Fix |
|------|-----|
| `src/main.py` | `query` help ("Query a seed record" → entity/registry); `network status` help ("Drill down to one seed record" → entity); other subparser strings that imply query-time seed reads |
| `src/mycelium_mcp/server.py` | `query_entity` docstring: entity lookup via registry |
| `src/network/introspection.py` | Verify no `Seed:` in demo/verbose (Slice 18 should have fixed — grep and patch stragglers) |

Keep `--seed` on `network create` (bootstrap fixture path) — that flag name is correct.

---

## P2 — Model / graph docstrings (no schema renames)

**Docstrings and Field descriptions only** — do **not** rename Pydantic fields (`SeedRecord`, `seed_records`, `seed_record`) in this polish slice; that would be a breaking public/schema change.

| File | Fix |
|------|-----|
| `src/models/state.py` | `EntityQuery`, `QueryResponse`, `MyceliumGraphState` descriptions: registry/bootstrap vocabulary |
| `src/graphs/core.py` | Module docstring: registry resolution, not seed loader |
| `src/agents/dispatch.py` | Audit strings like `no seed match` → `no entity match` |
| `src/agents/supervisor.py` | Docstrings on `_identity_records_from_seed` / `_seed_records_from_seed` (rename **functions** to neutral names if trivial; update call sites in `dispatch.py` / `supervisor.py` only) |

---

## P3 — Registry API nit (Slice 15 carry-over)

| File | Fix |
|------|-----|
| `src/agents/entity_registry.py` | Add public `list_entities() -> list[RegistryEntity]` |
| `src/agents/entity_resolution.py` | Replace `_iter_registry_entities` / `registry._data` peek with `list_entities()` |

---

## P4 — Context builder param name

| File | Fix |
|------|-----|
| `src/agents/context.py` | Rename `build_full_context(..., seed_records=)` → `matched_records=`; update call sites in `src/agents/dispatch.py` only |

---

## P5 — Docs (not covered by Slice 18)

Slice 18 updates `README.md` and `docs/architecture.md`. This polish pass hits **remaining stale runtime-seed references**:

| File | Fix |
|------|-----|
| `docs/full-code-walkthrough.md` | Identity from registry + bootstrap import; remove `agents.seed` / `find_by_key` |
| `docs/database-notes.md` | Query identity via `entities.json`; note legacy `seed` CLI removed |
| `prompts/system/CORE_PROMPT.md` | Storage section: seed.json = optional bootstrap fixture |
| `prompts/system/PROJECT_BRIEF.md` | Current implementation blurb (June 2026) |

**Out of scope:** `docs/plans/*` historical slice specs, `prompts/cursor/done/`, `prompts/resets/`, `TODO.md`.

---

## P6 — Example README tweaks

| File | Fix |
|------|-----|
| `examples/networks/crm/README.md` | Clarify `seed.json` is bootstrap fixture; runtime uses `entities.json` |

Only if still misleading after Slice 18.

---

## P7 — Empty-seed example network (`empty-crm`)

**Deferred since Slice 8 (Q8b); now feasible post seed-elimination.** Committed example with **no `seed.json`** — entities appear only via query bind (Paul Murphy arc).

### Create `examples/networks/empty-crm/`

| File | Content |
|------|---------|
| `network.json` | Same CRM MVR/bind rules as `examples/networks/crm/network.json`; `name`: `empty-crm`; `display_name`: e.g. "CRM (empty seed)"; `metering.enabled`: false |
| `guide.md` | Operator-facing: no preloaded people; first bind creates `entities.json` rows; Paul Murphy @ Acme Corp walkthrough |
| `README.md` | Maintainer notes: contrast with `crm` (bootstrap import vs growth-from-query); `refresh-example-network empty-crm` usage |

**Do not** add `seed.json`, `entities.json`, or runtime artifacts (`categories.json`, `agents/`, DB files).

Optional: `queries/01-bind-paul-murphy.json` with `EntityQuery`-shaped JSON for docs/MCP demos (mirror `crm-metering/queries/` style).

### Smoke test

Add to `tests/test_example_network.py` (smoke):

- `refresh_example_network("empty-crm", ...)` → success; **no** `entities.json` **or** empty `entities` / zero `registry_entity_count` after refresh
- Do not require a full `run_query` integration test here unless trivial with existing fixtures

### Doc cross-links

In `examples/networks/crm/README.md` and/or root `README.md` (only if Slice 18 did not already): one line pointing to `empty-crm` for the no-seed growth demo.

---

## P8 — Admin dist + package metadata (Slice 18 nits)

| Task | Action |
|------|--------|
| **Admin `--demo` bundle** | Run `cd admin-ui && npm run build` so local `admin-ui/dist/` matches Entities-only `App.tsx`. Confirm Overview shows **Entities**, not Seed. |
| **Do not commit `admin-ui/dist/`** | Project convention (`admin-ui/dist/` is gitignored; dev/restart-admin is canonical). Note build verification in `output.md`. |
| **Stale `PKG-INFO`** | After README curl examples are final, run `uv pip install -e .` (or equivalent) so `src/mycelium.egg-info/PKG-INFO` reflects `registry_entity_count`. Commit egg-info **only if** repo already tracks it; otherwise note regen step for Paul. |

Optional: `examples/networks/crm-metering/guide.md` — soften "CRM seed" wording to "bootstrap fixture" if misleading (one line).

---

## Scope boundaries (strict)

**May modify:**
- `src/main.py`, `src/mycelium_mcp/server.py`, `src/network/introspection.py`
- `src/models/state.py` (descriptions/docstrings only)
- `src/graphs/core.py`, `src/agents/dispatch.py`, `src/agents/supervisor.py`, `src/agents/context.py`
- `src/agents/entity_registry.py`, `src/agents/entity_resolution.py`
- `docs/full-code-walkthrough.md`, `docs/database-notes.md`
- `prompts/system/CORE_PROMPT.md`, `prompts/system/PROJECT_BRIEF.md`
- `examples/networks/crm/README.md` (optional)
- `examples/networks/empty-crm/` (new — P7)
- `tests/test_example_network.py` (empty-crm refresh smoke only)

**Out of scope:**
- `admin-ui/src/*` source changes — Slice 18 (P8 may **build** dist only, not edit TSX)
- `docs/architecture.md` — Slice 18 (root `README.md` one-line cross-link OK per P7)
- Renaming `SeedRecord` / `seed_records` state fields
- `TODO.md`
- `network create` without `--seed` (separate v2 track)

If a rename would touch MCP JSON schema or LangGraph state exports: **stop** and document in `output.md`.

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- In `output.md`, add **"For Grok + Paul"**: polish complete; `empty-crm` shipped; note to check off **Empty-seed network demo** + **Slices 14–18** on `TODO.md`; phase plan exit checkboxes; **batch commit** 17+18+polish together (Paul holding commits until polish approved); admin dist rebuild verified; any deferred renames.
- **No commit or push before review.**

### Stay in your lane (Cursor)

- **Deliver only:** in-scope files, `prompt.md` + `output.md`.
- **Do not create** `review.md`.
- **Do not** reopen seed-elimination architecture or queue new slices.

---

## Verify

```bash
uv run ruff check src tests
uv run pytest tests/test_example_network.py -m smoke -q
uv run pytest -m smoke -q
uv run pytest -q
rg 'agents\.seed|get_seed_data|find_by_key|seed_people_count' src/ tests/ admin-ui/src/ docs/full-code-walkthrough.md docs/database-notes.md prompts/system/
# expect no runtime-loader matches (bootstrap mentions of seed.json OK)
```

Report smoke **and full pytest** counts in `output.md` (phase sign-off depends on full green after polish).

---

## Deliverables

`prompts/cursor/done/2026-06-10-1815-entity-seed-elimination-polish/` with `prompt.md` and `output.md` **only**.

---

## Suggested commit message (after review)

```
Polish seed-elimination vocabulary, empty-crm, and review nits.

CLI/MCP/docstrings; list_entities; empty-crm; matched_records param;
admin dist build verified; PKG-INFO regen noted.
```