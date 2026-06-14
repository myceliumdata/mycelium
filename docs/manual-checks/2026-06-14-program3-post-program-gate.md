# Manual checks — Program 3 post-program gate (entity protocol legacy cleanup)

**Status:** ✅ **CLEAR** (2026-06-14) — Paul manual gate passed; tag `program_3` (incl. polish **1560**)

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
# entities is a dict keyed by uuid — not an array
jq '.entities | to_entries[0].value | {id, bind_values}' ~/mycelium-networks/crm/entities.json
jq '{bind_index_entries: (.bind_index | length), sample: (.bind_index | to_entries[0])}' \
  ~/mycelium-networks/crm/entities.json
```

**Pass:**

- Row has `bind_values` object with `name` and `employer` (CRM)
- No top-level `name` / `employer` keys on the entity object (only inside `bind_values`)
- Top-level `bind_index` map present with compound keys (e.g. `name|employer` → uuid)

---

## Check 2 — Status inspect flags

```bash
# By lookup (exact AND) — resolve echoes lookup, not id (D2-b)
uv run mycelium network status --network crm \
  --lookup-json '{"name":"Andrea Kalmans","employer":"Lontra Ventures"}' --json | \
  jq '{resolve, resolve_matches, resolve_kind}'

# By id — uuid from Check 1 (.entities…id), bind_index, or step-1 query results[].id
ANDREA_ID=$(jq -r '.bind_index["andrea kalmans|lontra ventures"]' ~/mycelium-networks/crm/entities.json)
uv run mycelium network status --network crm --id "$ANDREA_ID" --json | jq '.resolve'
```

**Pass:**

- Lookup path: `resolve.lookup` mirrors `--lookup-json` input (**no** `resolve.id` — that is correct)
- Id path: `resolve.id` equals the uuid you passed; `resolve_matches >= 1`, `resolve_kind` is `exact`
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

1. ~~Change **Status** at top to **✅ CLEAR (YYYY-MM-DD)**~~ — done 2026-06-14.
2. ~~Grok + Paul: update `TODO.md` — Program 3 complete; tag `program_3`.~~ — done; tag includes **1560**.
3. ~~Run slice **1560** polish~~ — complete (`c408ebb`).

---

*Created: 2026-06-14 · Program 3 entity protocol legacy cleanup*
