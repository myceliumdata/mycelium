# Onboarding — new contributors

**Read this first.** Runtime truth lives in [`architecture.md`](architecture.md), not in older slice plans under `docs/plans/`.

---

## 1. What Mycelium is (today)

- **Framework repo** (this project): LangGraph supervisor + specialist agents, query-only CLI/MCP, entity registry.
- **Networks**: isolated directories you choose (`network_root`). Each holds `entities.json`, ontology, specialist storage, checkpoints.
- **Public API**: `query` / `query_entity` only. Callers do **not** submit ingest payloads.

---

## 2. Terminology (avoid confusion)

| Term | Meaning |
|------|---------|
| **`entities.json`** | Canonical identity store at runtime (UUID, bind keys, validation state). |
| **`seed.json`** | Optional **bootstrap fixture** — imported at `refresh-example-network` or `network create --seed` only. Not read on query. |
| **`IdentityRecord`** | Graph/MCP model for a matched registry row (renamed from `SeedRecord`, June 2026). |
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
```

Optional: `./bin/restart-admin` → `http://127.0.0.1:5173` for the admin UI (`POST /query` **Run query** panel mirrors the same two-step flow).

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
- Expecting a public ingest API (removed June 2026; internal data addition is future design).
- Editing website copy in this repo (use **mycelium-website**).

---

*Last updated: June 2026 (post legacy ingest/storage removal, post identity rename).*