# Manual checks — Program 3 post-program gate (entity protocol legacy cleanup)

**Status:** **PENDING**

**Context:** Program 3 (Slices 1500–1550 + polish 1560) removes legacy `entity_key` / `binding` from public surfaces, migrates registry rows to `bind_values`, and aligns status inspect with query step-1 (`id` / `lookup` + `resolve` JSON). Run after code is on your branch and `./bin/ci-local` is green.

**Prereqs:** Framework repo root; `uv sync` done. Live roots under `~/mycelium-networks/` (never test in-place under `examples/networks/…`).

**Estimated time:** ~30–45 min (required checks 0–5).

---

## What Program 3 proves

- `entities.json` rows use **`bind_values`** keyed by `mvr.bind_fields` (no top-level `name` / `employer` columns)
- Status inspect accepts **`--id`** / **`--lookup-json`** only (no `--entity`)
- Status JSON includes **`resolve: { id, lookup }`** mirroring inspect input
- Public query/MCP/admin JSON has no `entity_key` / `binding` negotiation fields
- `describe_network` policy documents target protocol only (no legacy outcome keys)

---

## Pre-flight

```bash
cd /path/to/mycelium
./bin/ci-local
```

**Pass:** all steps green (~400+ smoke tests).

Refresh CRM to pick up `bind_values` shape:

```bash
./bin/refresh-example-network crm --yes
```

---

## Check 1 — Registry `bind_values`

```bash
jq '.entities[0] | {id, bind_values, bind_index}' ~/mycelium-networks/crm/entities.json
```

**Pass:**

- Row has `bind_values` object with `name` and `employer` (CRM)
- No top-level `name` / `employer` keys on the entity object
- `bind_index` present (compound key)

---

## Check 2 — Status inspect flags

```bash
# By lookup (exact AND)
uv run mycelium network status --network crm \
  --lookup-json '{"name":"Andrea Kalmans","employer":"Lontra Ventures"}' --json | \
  jq '{resolve, resolve_matches, resolve_kind}'

# By id (paste uuid from check 1 or query results)
uv run mycelium network status --network crm --id <uuid> --json | jq '.resolve'
```

**Pass:**

- `resolve.lookup` mirrors the `--lookup-json` input (or `resolve.id` when using `--id`)
- `resolve_matches >= 1`, `resolve_kind` is `exact` for known rows
- `--entity` flag is rejected or absent from help (`mycelium network status --help`)

---

## Check 3 — Query unchanged (target protocol)

```bash
uv run mycelium query --network crm \
  --lookup-json '{"name":"Nichanan Kesonpat","employer":"1k(x)"}'
```

Copy `delivery_id`, then:

```bash
uv run mycelium query --network crm --delivery-id d_…
```

**Pass:** step 1 `lookup_resolved`; step 2 `found` or `assembled`; no `entity_key` in request or response JSON.

---

## Check 4 — `describe_network` policy hygiene

Restart MCP if needed, then:

```bash
# MCP tool or:
uv run python -c "
import json, os
os.environ.setdefault('MYCELIUM_NETWORK_ROOT', os.path.expanduser('~/mycelium-networks/crm'))
from network.introspection import build_network_capabilities
p = build_network_capabilities()['policy']
assert 'entity_unknown' not in p
assert 'entity_bind' not in p
assert 'entity_key_unresolved' not in p
assert 'registry' in p
assert 'status_inspect' in p
print('policy keys OK:', sorted(p.keys()))
"
```

**Pass:** legacy policy keys absent; `registry`, `status_inspect`, `query.target_protocol` present.

---

## Check 5 — Admin status (optional)

With admin running (`MYCELIUM_NETWORK=crm uv run mycelium-admin`):

```bash
curl -s 'http://127.0.0.1:8741/status?lookup={"name":"Andrea%20Kalmans","employer":"Lontra%20Ventures"}' | jq '.resolve'
```

**Pass:** same `resolve` shape as CLI.

---

## When done

1. Change **Status** at top to **✅ CLEAR (YYYY-MM-DD)** — or tell Grok **"Program 3 gate clear."**
2. Grok + Paul: update `TODO.md` — Program 3 complete; suggest `program_3` tag.
3. Run slice **1560** polish / full integration gate if not already done.

---

*Created: 2026-06-14 · Program 3 entity protocol legacy cleanup*
