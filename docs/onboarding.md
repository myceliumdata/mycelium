# Onboarding — new contributors

**Read this first.** Runtime truth lives in [`architecture.md`](architecture.md), not in older slice plans under `docs/plans/`.

---

## 1. What Mycelium is (today)

- **Framework repo** (this project): LangGraph supervisor + specialist agents, query-only CLI/MCP, entity registry.
- **Networks**: isolated directories you choose (`network_root`). Each holds per-record-type entity stores under `entities/<record_type>.json` (default query record type for CRM: `person`), ontology, specialist storage, checkpoints.
- **Public API**: `query` / `query_entity` only. Callers do **not** submit ingest payloads.

---

## 2. Terminology (avoid confusion)

| Term | Meaning |
|------|---------|
| **`entities/<record_type>.json`** | Canonical identity store per MVR record type at runtime (UUID, `bind_values`, generic `bind_index`, validation state). CRM queries use the **`person`** record type by default. Requires explicit `mvr.record_types` and `mvr.default_record_type` in `network.json`. MVR bind values are cached here; canonical history is in specialist `versions[]` (Program 2). |
| **`seed.json`** | Optional **bootstrap fixture** — `rows[]` read by the declared bootstrap handler (CRM: `DefaultSeedHandler`) at `refresh-example-network` or `network create --seed` only. Not read on query. See [seed-bootstrap.md](seed-bootstrap.md). |
| **`network.json` → `bootstrap`** | Required bootstrap handler declaration: **`module`**, **`handler`**, optional **`seed_record_type`**. Framework modules (`network.*`) ship with the repo; pack modules live under `<network_root>/bootstrap_handlers/`. See [architecture.md](architecture.md) § Seed bootstrap and [seed-bootstrap.md](seed-bootstrap.md). |
| **`IdentityRecord`** | Graph/MCP model for a matched registry row: `id` + `bind_values` keyed by active MVR bind fields (renamed from `SeedRecord`, June 2026). |
| **`network create`** | Scaffold ontology + register name. `--seed` is optional; empty registry + first-query bind is valid (`empty-crm`). |
| **Slice plans** | Point-in-time specs in `docs/plans/`. May describe removed code — check **Active backlogs** in [`plans/README.md`](plans/README.md). |

Removed (do not revive): `agents.seed`, `core_data`, unwired `enrich`/`validator`, SQLite `people` table. See [`legacy-ingest-and-storage-reference.md`](legacy-ingest-and-storage-reference.md).

---

## 3. Read order (~30 minutes)

You are here (step 1). Then:

1. [`README.md`](../README.md) — quick start commands, CLI, examples (`crm`, `empty-crm`, `crm-metering`).
2. [`architecture.md`](architecture.md) — graph, registry, research, metering.
3. [`full-code-walkthrough.md`](full-code-walkthrough.md) — where code lives.
4. [`plans/README.md`](plans/README.md) — which design docs are historical vs active.

[myceliumdata.org](https://myceliumdata.org) links the same path: onboarding → README quick start → architecture.

---

## 4. Run it locally

```bash
uv sync --all-extras
cp .env.example .env   # OPENAI_API_KEY + TAVILY_API_KEY for research demos
./bin/refresh-example-network crm
# Step 1 — copy delivery_id from JSON
uv run mycelium query --network crm \
  --lookup-json '{"name": "Nichanan Kesonpat", "employer": "1k(x)"}'
# Step 2 — paste delivery_id
uv run mycelium query --network crm --delivery-id d_…
./bin/ci-local         # same gate as GitHub CI before you open a PR
./bin/smoke-crm-e2e    # CRM end-to-end: refresh + two-step query scenarios (~3s)
```

Optional: `./bin/restart-admin` → `http://127.0.0.1:5173` for the admin UI (`POST /query` **Run query** panel mirrors the same two-step flow).

**Status inspect:** Exact match only — no fuzzy suggestions on status.

```bash
uv run mycelium network status --network crm --lookup-json '{"name":"Andrea Kalmans"}' --json
uv run mycelium network status --network crm --id <uuid> --json
```

JSON includes `resolve: { id, lookup }` mirroring the inspect input, plus `entity_fields[]` with versioned storage.

**Step-1 negotiation (June 2026):** Branch on `outcome` before step 2. Partial lookup missing MVR fields → `lookup_incomplete` + `required_fields`. Near-miss typos or bind-field conflicts → `lookup_suggested` + `suggestions[].suggested_lookup` (merge into retry `lookup`, or use `suggestions[].id`). Suggestion `reason` values: `sequence_ratio`, `bind_field_fuzzy_match`, `same_bind_field_conflict`. Intentional create after a warning → re-run step 1 with `confirm_new_entity: true`. Policy: [`plans/fuzzy-lookup-policy.md`](plans/fuzzy-lookup-policy.md). **Restart MCP** after pulling suggestion-shape changes.

---

## 5. How we work

| Repo | Role |
|------|------|
| **mycelium** (here) | Framework code, tests, `docs/`, Cursor prompts in `prompts/cursor/` |
| **mycelium-website** | [myceliumdata.org](https://myceliumdata.org) — separate repo; website Cursor prompts live **there** |

- **Grok + Paul**: architecture, `TODO.md`, plans, reviews.
- **Cursor**: implementation from `prompts/cursor/next/` — see [`prompts/cursor/WORKFLOW.md`](../prompts/cursor/WORKFLOW.md).
- **Do not edit `TODO.md` from Cursor** unless a prompt explicitly allows it (default: never).

---

## 6. Common mistakes

- Treating `docs/plans/entity-seed-elimination-*.md` as current runtime behavior.
- Assuming `mycelium.db` holds identity (it does not; optional empty bootstrap file only).
- Omitting `bootstrap` in `network.json` — bootstrap fails on refresh/create; re-copy from a committed example or add the block (CRM: `network.bootstrap.handlers.default_seed` + `DefaultSeedHandler`).
- Expecting a public ingest API (removed June 2026; internal data addition is future design).
- Editing website copy in this repo (use **mycelium-website**).

---

*Last updated: June 2026 (framework MVR generic vocabulary; `./bin/smoke-crm-e2e`).*