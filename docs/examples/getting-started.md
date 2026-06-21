# Example networks — shared getting started

One-time framework setup shared by **all** committed examples (`crm-seeded`, `crm-empty`, `crm-metering`, `baseball`). Per-network bootstrap, keys, and feature walkthroughs live under [`docs/examples/<network>/`](README.md).

---

## 1. Clone and install

```bash
git clone https://github.com/myceliumdata/mycelium.git
cd mycelium
uv sync --all-extras
cp .env.example .env
```

---

## 2. Framework `.env` (not per-network)

Credentials live at the **repo root** — shared across every network on this machine. They are **not** copied into `network_root`.

| Variable | Required when | Notes |
|----------|---------------|-------|
| `OPENAI_API_KEY` | Research, derive, alias expansion, ontology | **Required** for all LLM-backed example paths (framework uses `ChatOpenAI` only) |
| `SEARCH_PROVIDER` + active search key | Research on cache miss | `tavily` (default), `exa`, or `brave` — validated on live gates |
| `MYCELIUM_*_MODEL` | Optional tuning | See [`.env.example`](../../.env.example); unset → `gpt-4o-mini` |
| `ANTHROPIC_API_KEY`, `GROK_API_KEY` | — | **Not wired** — placeholders in `.env.example` for future multi-provider; do not substitute for `OPENAI_API_KEY` today |
| `LANGCHAIN_TRACING_V2` | Optional | `false` to disable cloud tracing |

Multi-provider LLM (Anthropic, Grok, etc.) is planned; v1 examples and `./bin/gate-live` assume **OpenAI only**.

See [`.env.example`](../../.env.example) for derive models (`MYCELIUM_COMPUTATION_CODEGEN_MODEL`, `MYCELIUM_INTENT_NORMALIZATION_MODEL`), research tuning, and LangSmith.

**Baseball-only keys** (derive + intent dedup): documented in [baseball/getting-started.md](baseball/getting-started.md).

---

## 3. Bootstrap an example network

```bash
./bin/refresh-example-network <name> --yes
```

Default live root: `~/mycelium-networks/<name>`. Registered in `~/.config/mycelium/networks.json`.

| Network | Bootstrap time (typical) |
|---------|--------------------------|
| `crm-seeded`, `crm-metering`, `crm-empty` | Seconds |
| `baseball` | **~3–4 min** full Lahman (warehouse + registries) |

**Pack-only sync** (no re-bootstrap): `./bin/refresh-example-network <name> --sync-only`

---

## 4. Two-step query protocol (all networks)

Mycelium uses a **target protocol**: step 1 resolves lookup → `delivery_id`; step 2 delivers attributes.

```bash
# Step 1 — copy delivery_id from JSON (stderr prints step-2 hint with --network)
uv run mycelium query --network <name> \
  --lookup-json '{"…": "…"}'

# Step 2 — same --network as step 1
uv run mycelium query --network <name> --delivery-id d_…
```

Optional on step 1: `--requested-attributes attr1,attr2` (or MCP `requested_attributes` array) to bind attrs into the delivery scope for step 2.

Branch on `outcome` before step 2: `lookup_resolved`, `lookup_incomplete`, `lookup_suggested`, `quote_required`, etc. See [architecture.md](../architecture.md) and [mvr-redesign entity query examples](../plans/mvr-redesign-entity-query-examples.md).

---

## 5. MCP (one server per network)

MCP is a **long-lived stdio process** — configure **one server entry per network**. The server `cwd` must be the **framework repo** (so `uv run mycelium-mcp` finds the project). API keys come from the framework `.env` at that path — not from the client `env` block.

**Claude Desktop** — merge into `claude_desktop_config.json` (macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`). Replace `/absolute/path/to/mycelium` with your clone:

```json
{
  "mcpServers": {
    "mycelium-crm-seeded": {
      "command": "uv",
      "args": ["run", "mycelium-mcp"],
      "cwd": "/absolute/path/to/mycelium",
      "env": {
        "MYCELIUM_NETWORK": "crm-seeded"
      }
    }
  }
}
```

(`MYCELIUM_NETWORK` resolves via `~/.config/mycelium/networks.json` after `./bin/refresh-example-network crm-seeded`. Or set `MYCELIUM_NETWORK_ROOT` to an absolute live root instead.)

Other examples: use the same shape with `"MYCELIUM_NETWORK": "baseball"`, `"crm-empty"`, or `"crm-metering"`.

**Tools:** `describe_network` (connect time), `query_entity` (same JSON as CLI `EntityQuery`), `health_check`, `pay_quote` (metering).

**After refresh:** restart Claude Desktop (or your MCP client) so the server reloads wiped artifacts.

**Research demos:** use a fresh `thread_id` per attribute on first research hit.

---

## 6. Admin UI (optional)

One **network per daemon** — same binding model as MCP. No in-UI network switcher; restart with a different name to change examples.

```bash
./bin/restart-admin              # default: crm-seeded
./bin/restart-admin baseball     # or crm-empty, crm-metering, …
```

Open `http://127.0.0.1:5173` — **Run query** mirrors the two-step protocol (user clicks Run for each step). Header shows the bound network from `GET /health`.

---

## 7. Regression gates

| Gate | Scope |
|------|--------|
| `./bin/ci-local` | Smoke tests + ruff + admin-ui build (CI) |
| `./bin/smoke-*-e2e` | Fast fixture E2E per network |
| `./bin/gate-live <name>` | Real `~/mycelium-networks/<name>` + `.env`; **never CI** |

Live gate program: [manual-checks/2026-06-20-live-gate-program.md](../manual-checks/2026-06-20-live-gate-program.md).

---

## Next

| Network | Getting started | Feature walkthroughs |
|---------|-----------------|----------------------|
| CRM (seeded) | [crm-seeded/getting-started.md](crm-seeded/getting-started.md) | [crm-seeded/explore/](crm-seeded/explore/README.md) |
| CRM (empty) | [crm-empty/getting-started.md](crm-empty/getting-started.md) | [crm-empty/explore/](crm-empty/explore/README.md) |
| CRM metering | [crm-metering/getting-started.md](crm-metering/getting-started.md) | [crm-metering/explore/](crm-metering/explore/README.md) |
| Baseball | [baseball/getting-started.md](baseball/getting-started.md) | [baseball/explore/](baseball/explore/README.md) |

How walkthroughs are structured: [exploration-walkthroughs.md](exploration-walkthroughs.md).