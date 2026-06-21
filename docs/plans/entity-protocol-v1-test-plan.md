# Entity protocol v1 — test plan

> **Superseded for public clients (June 2026):** Target two-step protocol + `lookup_suggested` / `suggested_lookup` replaced legacy `entity_key` / `binding` negotiation on CLI, MCP, and admin. Keep this plan for historical Slice 1–8 regression context only.

**Scope:** Slices 1–8 + polish (`1800`) — negotiation, registry, validation, research gate, growth.  
**Metering (Slices 9–10):** out of scope for this plan.  
**Branch for testing:** `entity-protocol-v1-rc` (pushed to `origin`; delete after main is promoted).  
**Baseline commit:** `6cb7426` — *Entity protocol polish post Slice 8 (1800)*

---

## Before you start

```bash
cd /path/to/mycelium
git fetch origin
git checkout entity-protocol-v1-rc   # or stay on local main (same commits)
uv sync
```

**Pass criteria (automated):** all commands in §1 exit 0 with expected counts.  
**Pass criteria (manual):** every scenario in §2 matches the expected `outcome` and behavior notes.

---

## 1. Automated test plan (run now)

Grok or CI can run these immediately — no API keys required for the entity-protocol smokes (research is mocked in growth tests).

### 1.1 Full smoke suite (gate)

```bash
uv run pytest -m smoke -q
```

**Expected:** `213 passed` (±0; deselected count may vary).

### 1.2 Entity protocol focused (fast regression)

```bash
uv run pytest \
  tests/test_entity_key_suggestions.py \
  tests/test_entity_unknown_mvr.py \
  tests/test_entity_registry_bind.py \
  tests/test_entity_validation.py \
  tests/test_entity_research_gate.py \
  tests/test_entity_boundary.py \
  tests/test_entity_growth.py \
  tests/test_mcp_onboarding.py \
  tests/test_query_response_outcomes.py \
  -m smoke -q
```

**Expected:** `59 passed` (verified 2026-06-09 on `entity-protocol-v1-rc`).

### 1.3 Per-slice file groups

Run any group after touching that slice’s code.

| Slice | Focus | Command |
|-------|--------|---------|
| 1 | Key suggestions | `uv run pytest tests/test_entity_key_suggestions.py -m smoke -q` |
| 2 | Outcomes + MCP schema | `uv run pytest tests/test_query_response_outcomes.py tests/test_mcp_onboarding.py -m smoke -q` |
| 3 | Unknown + MVR | `uv run pytest tests/test_entity_unknown_mvr.py -m smoke -q` |
| 4 | Registry bind | `uv run pytest tests/test_entity_registry_bind.py -m smoke -q` |
| 5 | Validation | `uv run pytest tests/test_entity_validation.py -m smoke -q` |
| 6 | Research gate | `uv run pytest tests/test_entity_research_gate.py -m smoke -q` |
| 7 | Boundary / context | `uv run pytest tests/test_entity_boundary.py tests/test_specialist_entity_vocab.py -m smoke -q` |
| 8 | Growth + attribution | `uv run pytest tests/test_entity_growth.py -m smoke -q` |
| P | Polish cross-cuts | Re-run §1.2 |

### 1.4 Adjacent smokes (recommended before promoting `main`)

These exercise supervisor → specialists → assemble paths that entity protocol depends on:

```bash
uv run pytest \
  tests/test_supervisor_routing.py \
  tests/test_specialist_research_integration.py \
  tests/test_specialist_sync_research.py \
  tests/test_query_messages.py \
  tests/test_network_integration.py \
  -m smoke -q
```

### 1.5 Lint (optional)

```bash
uv run ruff check src tests
```

### 1.6 Full non-smoke suite (slow; pre-release)

```bash
uv run pytest -q
```

Run when you have time before pushing `main` to `origin`.

---

## 2. Manual test plan (Paul — when you have time)

Manual checks validate **live network behavior**, MCP onboarding, and optional real research (Tavily). Automated smokes use isolated temp dirs; manual tests use your registered CRM network.

### 2.1 Setup (once per session)

```bash
./bin/refresh-example-network crm-seeded --yes
```

Confirm network:

```bash
uv run mycelium network list
uv run mycelium network status --network crm-seeded
```

**Note:** CLI `mycelium query` does not yet expose `--binding`. Binding flows below use **MCP `query_entity`** (JSON) or the **Python helper** in §2.2. Plain CLI covers seed hits and near-misses without binding.

Restart MCP after refresh if you use Cursor MCP tools against CRM.

Use a **fresh `thread_id`** per scenario (or omit it) so checkpoints do not bleed across tests.

### 2.2 Python helper (binding + attributes)

From repo root, after refresh:

```bash
uv run python - <<'PY'
import json, os, sys, uuid
sys.path.insert(0, "src")
# Required before importing graphs.core — multiple run_query() in one process
# otherwise hits: asyncio lock bound to a different event loop.
os.environ["MYCELIUM_USE_SYNC_CHECKPOINTER"] = "1"
os.environ.setdefault("MYCELIUM_NETWORK", "crm-seeded")
from graphs.core import run_query
from models.state import EntityQuery

def q(entity_key, attrs=None, binding=None):
    thread_id = f"manual-{uuid.uuid4()}"
    r = run_query(EntityQuery(
        entity_key=entity_key,
        requested_attributes=attrs or [],
        binding=binding or {},
    ), thread_id=thread_id)
    print(json.dumps({
        "outcome": r.outcome,
        "required_fields": r.required_fields,
        "suggestions": [s.entity_key for s in (r.suggestions or [])],
        "results": r.results,
        "message": r.message[:200] if r.message else None,
    }, indent=2))

# --- edit and call q(...) per scenario below ---
PY
```

Copy `q(...)` calls from each scenario into the heredoc, or run interactively.

### 2.3 MCP checks (optional but recommended)

1. **`describe_network`** — confirm policy includes:
   - `entity_key_unresolved`, `entity_unknown`, MVR / `required_fields`
   - `optional_fields` contains **`binding`**
   - `entity_growth` / attribution notes
2. **`query_entity`** — same JSON as `EntityQuery` (see scenarios). Example:

```json
{
  "entity_key": "Andrea Kalman",
  "requested_attributes": ["email"]
}
```

### 2.4 Query outcomes (reference)

Read `outcome` before `results`. Full program table: [`entity-protocol-and-registry-program.md`](entity-protocol-and-registry-program.md) (§ Outcome enum). Runtime policy prose: MCP `describe_network` → `policy.*`. Field definitions: `QueryResponse.outcome` in `src/models/state.py`.

| `outcome` | Meaning |
|-----------|---------|
| `entity_key_unresolved` | Near-miss on `entity_key` — check `suggestions[]`, re-query with a suggested `entity_key`; no attribute research yet |
| `assembled` | Match found; requested attributes merged into `results` (research may be pending or complete) |
| `entity_unknown` | No seed/registry match (or ambiguous name) — supply `binding` per `required_fields` before research |
| `found` | Identity-only hit, duplicate bind, or validation failed (stays provisional) — read `message` for which |
| `entity_validated` | New registry row passed MVR checks — attribute research may proceed on a follow-up query |
| `entity_under_specified` | Partial `binding` — more MVR fields still needed |
| `entity_bound_provisional` | Bind accepted; core validation not finished yet |
| `not_found` | Generic miss (legacy path; most CRM flows use protocol outcomes above) |
| `error` | Graph finished without a proper response payload |

**Manual scenario map:** M1 → `entity_key_unresolved`; M2/M5/M6/M10/M12 → `assembled`; M3/M9 → `entity_unknown`; M4/M8 → `entity_validated`; M7/M11 → `found`.

### 2.5 Scenarios

| ID | Scenario | Input | Expected `outcome` | Notes |
|----|----------|-------|-------------------|-------|
| M1 | Near-miss key (A) | `entity_key`: `"Andrea Kalman"`, `requested_attributes`: `["email"]` | `entity_key_unresolved` | `suggestions` includes `Andrea Kalmans`; **no** specialist research |
| M2 | Confirm suggestion | `entity_key`: `"Andrea Kalmans"`, `requested_attributes`: `["email"]` | `assembled` (or `found` if cached) | Normal seed path; may need API keys for live email |
| M3 | Unknown entity (B) | `entity_key`: `"Paul Murphy"`, `requested_attributes`: `["email"]` | `entity_unknown` | `required_fields` includes `employer`; empty `results` |
| M4 | Bind + validate (C→D) | `entity_key`: `"Paul Murphy"`, `binding`: `{"employer": "Acme Corp"}` | `entity_validated` | Creates registry row; no email yet |
| M5 | Research after bind | Same as M4 + `requested_attributes`: `["email"]` | `assembled` | With Tavily/API: email in `results`; without: pending/message only |
| M6 | Re-query bind key | `entity_key`: `"Paul Murphy"`, `binding`: `{"employer": "Acme Corp"}`, `requested_attributes`: `["email"]` | `assembled` | Same `id` as M4; email value present if M5 researched |
| M7 | Duplicate bind | Repeat M4 without new employer | `found` | Message mentions already bound (validated) |
| M8 | Two employers | Bind Murphy @ Acme, then Murphy @ Beta LLC | `entity_validated` each | Two distinct `id`s in registry |
| M9 | Name-only ambiguity | After M8, `Paul Murphy` + email, **no** binding | `entity_unknown` | `required_fields`: `["employer"]` |
| M10 | Seed unchanged | `entity_key`: `"Andrea Kalmans"`, `requested_attributes`: `["email"]` | `assembled` | Registry growth must not corrupt seed row |
| M11 | Provisional gate | Bind with invalid employer (e.g. `"X"`) + email | validation fail or under-specified | No specialist invoke before validation passes |
| M12 | Aaron Holiday (seed only) | `entity_key`: `"Aaron Holiday"`, `requested_attributes`: `["email"]` | `assembled` | No `entities.json` write for pure seed hit |

### 2.6 Operator verification (after M4–M6)

```bash
uv run mycelium network status --network crm-seeded --entity "Paul Murphy"
```

Check:

- Registry row exists with `validation_state: validated`
- After email research: attribution fields reflected in status output (where implemented)
- `entities.json` under your CRM root contains `attr_sources` / `last_researched_at` for researched attrs

Inspect files (paths depend on your registered root):

```bash
# Default live root — adjust if you used --root
cat ~/mycelium-networks/crm/entities.json | python -m json.tool
```

### 2.7 Admin UI (optional)

```bash
MYCELIUM_NETWORK=crm uv run mycelium-admin
# or: ./bin/restart-admin
```

Search **Andrea Kalmans** and **Paul Murphy** after growth scenarios; confirm entity fields render.

### 2.8 CLI-only quick smoke (no binding)

```bash
uv run mycelium query --network crm-seeded --entity-key "Andrea Kalman" --attributes email
uv run mycelium query --network crm-seeded --entity-key "Andrea Kalmans" --attributes email
uv run mycelium query --network crm-seeded --entity-key "Nichanan Kesonpat"
```

Inspect JSON: first should show unresolved/suggestions; second and third should succeed on seed.

---

## 3. Sign-off checklist

- [ ] §1.1 full smoke green (`213 passed`)
- [ ] §1.2 entity bundle green (`59 passed`)
- [ ] §2.5 scenarios M1–M12 pass (or documented env limitation for live research)
- [ ] `describe_network` policy matches §2.3
- [ ] Ready to `git push origin main` and delete `entity-protocol-v1-rc`

---

## 4. Known limitations (not failures)

- **Metering / `quote_required`:** not implemented (Slices 9–10 deferred).
- **CLI `--binding`:** not implemented; use MCP or Python helper for bind flows.
- **Empty-seed demo, seed export, seed/grown linking:** deferred (`TODO.md`).
- **Live email research:** requires API keys; without them, expect `pending` / classify messages, not hard errors.

---

*Last verified: 2026-06-09 — automated counts on branch `entity-protocol-v1-rc`.*