# Manual checks — Baseball identity ship gate (June 2026)

**Status:** ⏳ **PENDING** — run after **Test 8c** bootstrap timing; mark **✅ CLEAR** when all required checks pass.

**Scope:** Ship **identity + query routing** on the full Lahman bootstrap. **Not** ontology, specialists, stats, or derivatives.

**Program:** [`docs/plans/baseball-example-program.md`](../plans/baseball-example-program.md) — slices through 2100 + 0800/0900 polish; **slice #5 (derived stat query) explicitly out of scope.**

**Owner:** Paul + Grok (not Cursor)

**Estimated time:** ~45–60 min (required checks 0–7); optional 8–10 add ~15 min.

---

## What this gate proves

- Full Lahman refresh completes at acceptable wall time (**Test 8c** ~test 7 ballpark).
- Bootstrap commits **~23,777** player + team identity rows with `source_keys` and warehouse.
- **Player grain** (default): step-1 resolve + step-2 deliver **identity only** (`name`, `team`, `id`).
- **Team grain**: resolve + deliver with explicit `grain=team` (city+name canonical labels).
- **Closed identity**: unknown binds do not offer `create_on_deliver` / `create_pending`.
- **Multi-team careers**: same `lahman.playerID` → same uuid across different `(name, team)` bind keys.
- Automated smoke gates stay green on the benchmark root.

## Explicit non-goals (do not fail the gate on these)

- Career stats, batting/pitching attrs, roster lists, franchise aggregation.
- Baseball-specific `categories.json` or specialist research.
- `requested_attributes: ["email"]` or any CRM-style deliver (CRM categories are a stub).
- CLI `--grain` flag (not shipped; use helper below or MCP JSON).

---

## Environment

```bash
cd /path/to/mycelium
uv sync
export ROOT="${ROOT:-/tmp/mycelium-baseball-benchmark}"
```

Use a **dedicated root** (benchmark or `~/mycelium-networks/baseball` after refresh). Do not test under `examples/networks/`.

**Refresh (if needed):**

```bash
/usr/bin/time -p ./bin/refresh-example-network baseball \
  --root "$ROOT" --yes --no-default
```

Record **Test 8c** `real` in [`2026-06-17-storage-evolution-timing-gates.md`](2026-06-17-storage-evolution-timing-gates.md).

---

## Helpers (copy once per shell)

```bash
export ROOT="${ROOT:-/tmp/mycelium-baseball-benchmark}"
export MYCELIUM_NETWORK_ROOT="$ROOT"
# Derived paths for this network layout:
eval "$(uv run python -c "
from network.paths import NetworkPaths, apply_network_paths
p = NetworkPaths.from_root(__import__('pathlib').Path('$ROOT'))
apply_network_paths(p)
for k, v in [('ENTITIES_PLAYER', p.entities_path.parent / 'player.json'),
             ('ENTITIES_TEAM', p.entities_path.parent / 'team.json'),
             ('WAREHOUSE', p.root / 'warehouse' / 'lahman.sqlite')]:
    print(f'export {k}={v!r}')
")"

# Step-1/2 query helper (supports grain= for team checks)
baseball_query() {
  uv run python -c "
import json, sys
from graphs.core import reset_core_graph, run_query
from models.state import EntityQuery
reset_core_graph()
payload = json.loads(sys.argv[1])
q = EntityQuery(**payload)
r = run_query(q)
print(json.dumps(r.public_dict(), indent=2))
" "$1"
}
```

---

## Check 0 — CI + fast smoke (required)

```bash
./bin/ci-local
./bin/smoke-baseball-e2e
./bin/smoke-crm-e2e
```

**Pass:** all green; baseball e2e **6** scenarios (minimal fixture, seconds).

---

## Check 1 — Bootstrap artifacts (required)

```bash
test -f "$ROOT/network.json"
test -f "$WAREHOUSE"
test -f "$ENTITIES_PLAYER"
test -f "$ENTITIES_TEAM"
test -f "$ROOT/seed/lahman_1871-2025_csv/People.csv" \
  -o -f "$ROOT/seed/lahman_1871-2025_csv.zip"
```

```bash
jq '{
  player_entities: (.entities | length),
  bind_index_entries: (.bind_index | length),
  source_key_index_entries: (.source_key_index | length)
}' "$ENTITIES_PLAYER"
```

```bash
jq '{team_entities: (.entities | length)}' "$ENTITIES_TEAM"
```

**Pass:**

- Warehouse + both entity stores exist.
- Player entities **≈ 23,777** (± small drift across Lahman tags).
- `source_key_index` non-empty on player store.
- Team entities **≈ 241** distinct canonical team names (order-of-magnitude).

---

## Check 2 — Warehouse ↔ registry sanity (required)

Discover Hank Aaron teams (adjust if seed tag differs):

```bash
sqlite3 "$WAREHOUSE" "
SELECT DISTINCT t.name AS team_label
FROM Appearances a
JOIN Teams t ON a.teamID = t.teamID AND a.yearID = t.yearID
JOIN People p ON a.playerID = p.playerID
WHERE p.playerID = 'aaronha01'
ORDER BY team_label
LIMIT 10;
"
```

Pick **two** distinct `team_label` values from output; set shell vars (example):

```bash
AARON_NAME="Hank Aaron"
TEAM_A="Milwaukee Braves"    # replace from SQL
TEAM_B="Atlanta Braves"      # replace from SQL — must differ from TEAM_A
```

**Pass:** at least **two** team labels for `aaronha01` on full Lahman (multi-team career).

---

## Check 3 — `source_keys` + bind aliases (required)

```bash
uv run python -c "
from network.paths import NetworkPaths, apply_network_paths
from agents.entity_registry import get_entity_registry, reset_entity_registry
import os
root = os.environ['ROOT']
apply_network_paths(NetworkPaths.from_root(__import__('pathlib').Path(root)))
reset_entity_registry()
reg = get_entity_registry(grain='player')
e1 = reg.lookup_by_source_key('lahman.playerID', 'aaronha01')
assert e1, 'missing player by source key'
e2 = reg.lookup_by_bind_values({'name': '$AARON_NAME', 'team': '$TEAM_A'})
e3 = reg.lookup_by_bind_values({'name': '$AARON_NAME', 'team': '$TEAM_B'})
assert e2 and e3, 'missing bind lookups'
assert e1.id == e2.id == e3.id, f'id mismatch: {e1.id} {e2.id} {e3.id}'
assert e1.source_keys.get('lahman.playerID') == 'aaronha01'
print('OK same uuid', e1.id, 'binds', len(reg._data.bind_index))
"
```

**Pass:** one uuid for Aaron; two+ bind_index keys; `lahman.playerID` on entity row.

---

## Check 4 — CLI player two-step (required)

Use vars from Check 2:

```bash
export MYCELIUM_NETWORK_ROOT="$ROOT"
STEP1=$(uv run mycelium query --network-dir "$ROOT" \
  --lookup-json "{\"name\":\"$AARON_NAME\",\"team\":\"$TEAM_A\"}")
echo "$STEP1" | jq '{outcome, total_matches, delivery_id: .delivery.delivery_id, grain: .delivery.grain}'

DELIVERY_ID=$(echo "$STEP1" | jq -r '.delivery.delivery_id')
uv run mycelium query --network-dir "$ROOT" --delivery-id "$DELIVERY_ID" | \
  jq '{outcome, results: .results}'
```

**Pass:**

- Step 1: `outcome` = `lookup_resolved`, `total_matches` = 1, `delivery.delivery_id` present.
- Step 2: `outcome` = `found`; `results[0]` has `id`, `name`, `team` matching lookup.
- **No** `create_on_deliver` on step 1 delivery scope.
- Response JSON has **no** `entity_key` / `binding` legacy fields.

---

## Check 5 — Team grain resolve + deliver (required)

Pick a team name that exists (from SQL or registry):

```bash
TEAM_NAME="Brooklyn Dodgers"   # or another row from: sqlite3 "$WAREHOUSE" "SELECT DISTINCT name FROM Teams LIMIT 5;"

baseball_query "{\"lookup\": {\"name\": \"$TEAM_NAME\"}, \"grain\": \"team\"}" | \
  jq '{outcome, total_matches, delivery_id: .delivery.delivery_id, grain: .delivery.grain}'
```

Copy `delivery_id`, then:

```bash
baseball_query "{\"delivery_id\": \"$DELIVERY_ID\"}" | \
  jq '{outcome, results: .results}'
```

**Pass:**

- Step 1: `lookup_resolved`, 1 match, `delivery.grain` = `team`.
- Step 2: `found`; `results[0].name` = canonical team string.

---

## Check 6 — Closed identity (required)

```bash
uv run mycelium query --network-dir "$ROOT" \
  --lookup-json '{"name":"Nobody Here","team":"Nowhere Nine"}' | \
  jq '{outcome, total_matches, create_on_deliver: .delivery.create_on_deliver}'
```

**Pass:**

- `outcome` is `not_found` or `lookup_suggested` (not `lookup_resolved` with 0 matches + create scope).
- `delivery` is null **or** `create_on_deliver` is false/absent.

---

## Check 7 — Registry public shape (required)

```bash
jq '.entities | to_entries[0].value | keys' "$ENTITIES_PLAYER" | jq 'inside(["id","bind_values","source_keys","source","validation_state"])'
jq '.entities | to_entries[0].value | {id, bind_values, source_keys}' "$ENTITIES_PLAYER" | head
```

**Pass:** entities use `bind_values` + `source_keys`; no top-level bare `name`/`team` outside `bind_values`.

---

## Check 8 — Multi-grain partial lookup (optional)

Name-only lookup on player default grain (may fan-out or suggest):

```bash
baseball_query '{"lookup": {"name": "Hank Aaron"}}' | \
  jq '{outcome, total_matches, suggestion_reasons}'
```

**Pass (lenient):** does not crash; outcome is one of `lookup_resolved`, `lookup_suggested`, `not_found`. Record behavior for ship notes.

---

## Check 9 — Nickname / field alias (optional — needs `OPENAI_API_KEY`)

Only if you want to validate lazy alias expansion on full data:

```bash
export OPENAI_API_KEY=…   # required for real expansion
baseball_query '{"lookup": {"name": "Dodgers"}, "grain": "team"}' | \
  jq '{outcome, total_matches}'
```

**Pass (optional):** `lookup_resolved` with `total_matches` ≥ 2 (Brooklyn + LA), or `lookup_suggested` with grain-tagged candidates. **Skip** if no API key — not blocking ship.

---

## Check 10 — Network status (optional)

```bash
uv run mycelium network status --network-dir "$ROOT" --json | \
  jq '{network_name, registry_entity_count, grains: .mvr_grains, ontology_present}'
```

**Pass:** baseball network; entity count > 0; grains include `player` and `team`. CRM-copy ontology present is **expected** (not blocking).

---

## Ship decision

| Result | Action |
|--------|--------|
| **All required checks 0–7 pass** | Mark this doc **✅ CLEAR (date)**; Paul may push `main` to `origin`; **then** queue ontology/specialists work. |
| **Test 8c >> ~15 min** | Ship anyway if identity checks pass, but log timing regression in timing-gates doc. |
| **Any required check fails** | Do **not** ship; file fix slice or diagnose before ontology work. |

---

## When CLEAR

1. Update **Status** at top of this file with date.
2. Record **Test 8c** timing in [`2026-06-17-storage-evolution-timing-gates.md`](2026-06-17-storage-evolution-timing-gates.md).
3. Grok + Paul: note in `TODO.md` / `HOLD.md` that baseball identity ship gate passed (Paul owns `TODO.md` edits).
4. Push to `origin` when Paul is ready.

---

*Created: 2026-06-17 · Baseball identity ship gate (pre-ontology/specialists)*