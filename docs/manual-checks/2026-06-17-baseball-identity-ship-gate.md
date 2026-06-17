# Manual checks — Baseball identity ship gate (June 2026)

**Status:** ⏳ **PENDING** — run after **Test 8c** bootstrap timing; mark **✅ CLEAR** when all required checks pass.

**Scope:** Ship **identity + query routing** on the full Lahman bootstrap. **Not** ontology, specialists, stats, or derivatives.

**Program:** [`docs/plans/baseball-example-program.md`](../plans/baseball-example-program.md) — slices through 2100 + 0800/0900 polish; **slice #5 (derived stat query) explicitly out of scope.**

**Owner:** Paul + Grok (not Cursor)

**Estimated time:** ~45–60 min (required checks 0–7); optional 8–10 add ~15 min.

---

## What this gate proves

- Full Lahman refresh completes at acceptable wall time (**Test 8c:** **1,150 s** ~19 min — not test 7 ballpark but ship-acceptable per timing gate).
- Bootstrap commits **~23,777** player + team identity rows with `source_keys` and warehouse.
- **Player grain** (default): step-1 resolve + step-2 deliver **identity only** (`name`, `team`, `id`).
- **Team grain**: resolve + deliver via `{team: "…"}` lookup keys (no `grain` override).
- **Closed identity**: unknown binds do not offer `create_on_deliver` / `create_pending`.
- **Multi-team careers**: same `lahman.playerID` → same uuid across different `(name, team)` bind keys.
- Automated smoke gates stay green on the benchmark root.

## Explicit non-goals (do not fail the gate on these)

- Career stats, batting/pitching attrs, roster lists, franchise aggregation.
- Baseball-specific `categories.json` or specialist research.
- `requested_attributes: ["email"]` or any CRM-style deliver (CRM categories are a stub).
- `EntityQuery.grain` on step 1 (removed slice 1100; use lookup key shape).

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

Run this **whole block** before Checks 1–7 (`ENTITIES_*` empty → `jq` fails with “Could not open file”).

```bash
export ROOT="${ROOT:-/tmp/mycelium-baseball-benchmark}"
export MYCELIUM_NETWORK_ROOT="$ROOT"
export WAREHOUSE="$ROOT/warehouse/lahman.sqlite"
export ENTITIES_DIR="$ROOT/entities"
# Post–test 6 bootstrap migrates to minisql_v1 (sqlite), not player.json:
export ENTITIES_PLAYER_SQL="$ENTITIES_DIR/player.sqlite"
export ENTITIES_TEAM_SQL="$ENTITIES_DIR/team.sqlite"

cd /path/to/mycelium   # repo root — required for uv run python imports

# Step-1/2 query helper (lookup keys route grain — see docs/query-grain-router.md)
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

# Registry counts via framework (works for json or minisql_v1)
baseball_registry_counts() {
  uv run python -c "
import json, os
from pathlib import Path
from network.paths import NetworkPaths, apply_network_paths
from agents.entity_registry import get_entity_registry, reset_entity_registry
root = Path(os.environ['ROOT'])
apply_network_paths(NetworkPaths.from_root(root))
reset_entity_registry()
out = {}
for grain in ('player', 'team'):
    reg = get_entity_registry(grain=grain)
    out[grain] = {
        'entity_count': reg.entity_count(),
        'bind_index_entries': len(reg._data.bind_index),
        'source_key_index_entries': len(reg._data.source_key_index),
    }
print(json.dumps(out, indent=2))
"
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
test -f "$ENTITIES_PLAYER_SQL" -o -f "$ENTITIES_DIR/player.json"
test -f "$ENTITIES_TEAM_SQL" -o -f "$ENTITIES_DIR/team.json"
test -f "$ROOT/seed/lahman_1871-2025_csv/People.csv" \
  -o -f "$ROOT/seed/lahman_1871-2025_csv.zip"
```

```bash
baseball_registry_counts
```

**Pass:**

- Warehouse + both entity stores exist (`entities/player.sqlite` + `entities/team.sqlite` after full bootstrap).
- Player `entity_count` **≈ 23,500** (± drift; full Lahman v2025.1 ≈ **23,536**).
- Player `source_key_index_entries` **≈ 23,500** (non-empty).
- Player `bind_index_entries` **> entity_count** (multi-team aliases; ≈ **57k** bind rows).
- Team `entity_count` **≈ 241**.
- Bootstrap line `entities committed: 23777` = **players + teams** (not players alone).

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

Pick **two** distinct `team_label` values from output; set shell vars (**required before Checks 3–4**):

```bash
AARON_NAME="Hank Aaron"
TEAM_A="Milwaukee Braves"    # replace from SQL
TEAM_B="Atlanta Braves"      # replace from SQL — must differ from TEAM_A
echo "Aaron: $AARON_NAME | $TEAM_A | $TEAM_B"   # must not be empty
```

**Pass:** at least **two** team labels for `aaronha01` on full Lahman (multi-team career).

---

## Check 3 — `source_keys` + bind aliases (required)

Self-contained (no shell vars) — discovers two Aaron teams from warehouse:

```bash
uv run python -c "
import os, sqlite3
from pathlib import Path
from network.paths import NetworkPaths, apply_network_paths
from agents.entity_registry import get_entity_registry, reset_entity_registry

root = Path(os.environ['ROOT'])
apply_network_paths(NetworkPaths.from_root(root))
reset_entity_registry()
wh = root / 'warehouse' / 'lahman.sqlite'
teams = [
    row[0]
    for row in sqlite3.connect(wh).execute('''
        SELECT DISTINCT t.name
        FROM Appearances a
        JOIN Teams t ON a.teamID = t.teamID AND a.yearID = t.yearID
        JOIN People p ON a.playerID = p.playerID
        WHERE p.playerID = ?
        ORDER BY t.name
        LIMIT 2
    ''', ('aaronha01',))
]
assert len(teams) == 2, teams
name = 'Hank Aaron'
reg = get_entity_registry(grain='player')
e1 = reg.lookup_by_source_key('lahman.playerID', 'aaronha01')
assert e1, 'missing player by source key'
e2 = reg.lookup_by_bind_values({'player': name, 'team': teams[0]})
e3 = reg.lookup_by_bind_values({'player': name, 'team': teams[1]})
assert e2 and e3, f'missing bind lookups for {teams}'
assert e1.id == e2.id == e3.id, f'id mismatch: {e1.id} {e2.id} {e3.id}'
assert e1.source_keys.get('lahman.playerID') == 'aaronha01'
print('OK same uuid', e1.id, 'teams', teams, 'bind_index', len(reg._data.bind_index))
"
```

**Pass:** one uuid for Aaron; two+ bind_index keys; `lahman.playerID` on entity row.

---

## Check 4 — Player two-step (required)

**Do not pipe `mycelium query` into `jq`** — the CLI prints Rich-styled JSON (ANSI), not raw JSON.

Use `baseball_query` from Helpers (or vars from Check 2):

```bash
export AARON_NAME="Hank Aaron"
export TEAM_A="Milwaukee Braves"

STEP1=$(baseball_query "{\"lookup\": {\"player\": \"$AARON_NAME\", \"team\": \"$TEAM_A\"}}")
echo "$STEP1" | jq '{outcome, total_matches, delivery_id: .delivery.delivery_id, grain: .delivery.grain}'

DELIVERY_ID=$(echo "$STEP1" | jq -r '.delivery.delivery_id')
baseball_query "{\"delivery_id\": \"$DELIVERY_ID\"}" | jq '{outcome, results: .results}'
```

**Pass:**

- Step 1: `outcome` = `lookup_resolved`, `total_matches` = 1, `delivery.delivery_id` present.
- Step 2: `outcome` = `found`; `results[0]` has `id`, `player`, `team` matching lookup.
- **No** `create_on_deliver` on step 1 delivery scope.
- Response JSON has **no** `entity_key` / `binding` legacy fields.

**After slice `2026-06-18-1000` + `1100`:** Paul must **re-bootstrap** after merge. Then repeat with a second team from Check 2 (e.g. Milwaukee Braves):

```bash
./bin/baseball-query '{"lookup": {"player": "Hank Aaron", "team": "Milwaukee Braves"}}' | \
  jq '{outcome, total_matches, delivery_id: .delivery.delivery_id}'
```

**Pass:** `lookup_resolved`, `total_matches` = 1 (alias bind via `bind_index`).

**Optional smoke:** `uv run mycelium query --network-dir "$ROOT" --lookup-json '…'` — human-readable only; verify `lookup_resolved` in terminal output.

---

## Check 5 — Team grain resolve + deliver (required)

Pick a team name that exists (from SQL or registry):

```bash
TEAM_NAME="Brooklyn Dodgers"   # or another row from: sqlite3 "$WAREHOUSE" "SELECT DISTINCT name FROM Teams LIMIT 5;"

baseball_query "{\"lookup\": {\"team\": \"$TEAM_NAME\"}}" | \
  jq '{outcome, total_matches, delivery_id: .delivery.delivery_id, grain: .delivery.grain}'
```

Copy `delivery_id`, then:

```bash
baseball_query "{\"delivery_id\": \"$DELIVERY_ID\"}" | \
  jq '{outcome, results: .results}'
```

**Pass:**

- Step 1: `lookup_resolved`, 1 match, `delivery.grain` = `team`.
- Step 2: `found`; `results[0].team` = canonical team string.

---

## Check 6 — Closed identity (required)

```bash
baseball_query '{"lookup": {"player": "Nobody Here", "team": "Nowhere Nine"}}' | \
  jq '{outcome, total_matches, create_on_deliver: .delivery.create_on_deliver}'
```

**Pass:**

- `outcome` is `not_found` or `lookup_suggested` (not `lookup_resolved` with 0 matches + create scope).
- `delivery` is null **or** `create_on_deliver` is false/absent.

---

## Check 7 — Registry public shape (required)

```bash
uv run python -c "
import os
from pathlib import Path
from network.paths import NetworkPaths, apply_network_paths
from agents.entity_registry import get_entity_registry, reset_entity_registry
apply_network_paths(NetworkPaths.from_root(Path(os.environ['ROOT'])))
reset_entity_registry()
entity = next(iter(get_entity_registry(grain='player').list_entities()))
keys = set(entity.model_dump().keys())
required = {'id', 'bind_values', 'source_keys', 'source', 'validation_state'}
assert required <= keys, keys
assert 'name' not in keys or 'name' in entity.bind_values
print('OK sample entity', entity.id, entity.bind_values, entity.source_keys)
"
```

**Pass:** sample row has `bind_values` + `source_keys`; bind fields live under `bind_values`, not top-level.

---

## Check 8 — Multi-grain partial lookup (optional)

Name-only lookup on player default grain (may fan-out or suggest):

```bash
baseball_query '{"lookup": {"player": "Hank Aaron"}}' | \
  jq '{outcome, total_matches, suggestion_reasons}'
```

**Pass (lenient):** does not crash; outcome is one of `lookup_resolved`, `lookup_suggested`, `not_found`. Record behavior for ship notes.

---

## Check 9 — Nickname / field alias (optional — needs `OPENAI_API_KEY`)

Only if you want to validate lazy alias expansion on full data:

```bash
export OPENAI_API_KEY=…   # required for real expansion
baseball_query '{"lookup": {"team": "Dodgers"}}' | \
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