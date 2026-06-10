# Task: Seed elimination — Polish (vocabulary + code nits)

> **READY** — **Run after Slice 18 is reviewed and committed.** Move to `in-progress/` before starting.

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/entity-seed-elimination-phase.md`](../../docs/plans/entity-seed-elimination-phase.md) — phase context
- Slice 17 review nits: `prompts/cursor/done/2026-06-10-1700-entity-seed-elimination-slice17/review.md`
- Slice 16 review nits: `prompts/cursor/done/2026-06-10-1600-entity-seed-elimination-slice16/review.md`

**Depends on:** Slice 18 shipped (admin UI, `seed_people_count` removal, README/architecture pass, full pytest green).

**Do not redo Slice 18 work.** If `seed_people_count` is already gone from API/UI/tests, skip those items.

---

## Objective

Clean up **remaining seed-runtime vocabulary** and small code-quality nits after the seed-elimination phase. No behavior changes unless required for renamed public docstrings; smoke must stay green.

---

## P1 — CLI + MCP operator strings

Update user-facing help/docstrings that still imply query-time seed loading:

| File | Fix |
|------|-----|
| `src/main.py` | `query` / `network status` help: "entity" / "registry" not "seed record" |
| `src/mycelium_mcp/server.py` | `query_entity` docstring: entity lookup via registry |
| `src/network/introspection.py` | Demo/verbose strings; remove any leftover `Seed:` lines if Slice 18 missed them |

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

## P6 — Optional example README

| File | Fix |
|------|-----|
| `examples/networks/crm/README.md` | Clarify `seed.json` is bootstrap fixture; runtime uses `entities.json` |

Only if still misleading after Slice 18.

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

**Out of scope:**
- Admin UI (`admin-ui/`) — Slice 18
- `README.md`, `docs/architecture.md` — Slice 18
- Renaming `SeedRecord` / `seed_records` state fields
- `TODO.md`
- New features

If a rename would touch MCP JSON schema or LangGraph state exports: **stop** and document in `output.md`.

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- In `output.md`, add **"For Grok + Paul"**: polish complete; any deferred renames.
- **No commit or push before review.**

### Stay in your lane (Cursor)

- **Deliver only:** in-scope files, `prompt.md` + `output.md`.
- **Do not create** `review.md`.
- **Do not** reopen seed-elimination architecture or queue new slices.

---

## Verify

```bash
uv run ruff check src tests
uv run pytest -m smoke -q
rg 'agents\.seed|get_seed_data|find_by_key' src/ tests/ docs/full-code-walkthrough.md docs/database-notes.md prompts/system/
# expect no runtime-loader matches (bootstrap mentions of seed.json OK)
```

Report smoke count in `output.md`. Full pytest optional unless you touched full-marked tests.

---

## Deliverables

`prompts/cursor/done/2026-06-10-1815-entity-seed-elimination-polish/` with `prompt.md` and `output.md` **only**.

---

## Suggested commit message (after review)

```
Polish seed-elimination vocabulary and registry list_entities (post-18).

CLI/MCP/docstrings; full-code-walkthrough and system prompts;
context matched_records param; no schema field renames.
```