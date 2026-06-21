# Manual checks — Baseball identity ship gate (June 2026)

**Status:** ✅ **CLEAR (WIP)** — Paul manual sign-off **2026-06-18**. Identity + query routing verified (CLI, MCP, hand plan). **Ship this version** with WIP caveat below — not a finished baseball demo.

**Scope:** Ship **identity + query routing** on the full Lahman bootstrap. **Not** ontology, specialists, stats, or derivatives.

### WIP caveats (shipped anyway)

- **Example network** remains WIP per [`examples/networks/baseball/README.md`](../../examples/networks/baseball/README.md) — Lahman bootstrap + identity only.
- **CRM stub `categories.json`** — attribute requests route to CRM specialists (e.g. `professional_specialist` web research), not Lahman warehouse reads.
- **Provenance** — API works (`provenance=true` on step 1 → versioned attrs in step 2), but lineage today reflects **research sources** (URLs, confidence), not Lahman row refs. **Re-examine** when baseball ontology + warehouse specialists land ([`TODO.md`](../../TODO.md)).
- **Post-1800 player bind** — debut bind only; career teams are warehouse facts, not extra `bind_index` keys. Re-bootstrap required after merge.
- **MCP `health_check`** — `ping_query` may show `degraded` on baseball (hardcoded CRM ping); storage/graph ok.

**Program:** [`docs/plans/baseball-example-program.md`](../plans/baseball-example-program.md) — slices through 2100 + 0800/0900 polish; **slice #5 (derived stat query) explicitly out of scope.**

**Owner:** Paul + Grok (not Cursor)

**Estimated time:** ~45–60 min (required checks 0–7); optional 8–10 add ~15 min.

---

## What this gate proves

- Full Lahman refresh completes at acceptable wall time (**Test 8c:** **1,150 s** ~19 min — not test 7 ballpark but ship-acceptable per timing gate).
- Bootstrap commits **~23,777** player + team identity rows with `source_keys` and warehouse.
- **Player record type** (default): step-1 resolve + step-2 deliver **identity only** (`player`, `debut_team`, `debut_year`, `id`).
- **Team record type**: resolve + deliver via `{team: "…"}` lookup keys (no `record_type` override).
- **Closed identity** (`bootstrap_only`): unknown binds do not offer `create_on_deliver` / `create_pending`.
- **One bind per catalog row**: same `lahman.playerID` → one uuid with a single debut bind at bootstrap (post slice 1800).
- Automated smoke gates stay green on the benchmark root.

## Explicit non-goals (do not fail the gate on these)

- Career stats, batting/pitching attrs, roster lists, franchise aggregation.
- Baseball-specific `categories.json` or specialist research.
- `requested_attributes: ["email"]` or any CRM-style deliver (CRM categories are a stub).
- `EntityQuery.grain` / `EntityQuery.record_type` on step 1 (removed slice 1100; use lookup key shape).

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

# Step-1/2 query helper (lookup keys route record type — see docs/query-record-type-router.md)
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
for record_type in ('player', 'team'):
    reg = get_entity_registry(record_type=record_type)
    out[record_type] = {
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
./bin/smoke-crm-seeded-e2e
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
- Player `bind_index_entries` **≈ entity_count** (one debut bind per `playerID` post slice 1800).
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

**Pass:** at least **two** distinct team labels for `aaronha01` on full Lahman (multi-team **career** in warehouse — identity still uses one debut bind).

---

## Check 3 — `source_keys` + debut bind (required)

Self-contained — verifies one debut bind per `aaronha01`:

```bash
uv run python -c "
import os
from pathlib import Path
from network.paths import NetworkPaths, apply_network_paths
from agents.entity_registry import get_entity_registry, reset_entity_registry

root = Path(os.environ['ROOT'])
apply_network_paths(NetworkPaths.from_root(root))
reset_entity_registry()
reg = get_entity_registry(record_type='player')
e1 = reg.lookup_by_source_key('lahman.playerID', 'aaronha01')
assert e1, 'missing player by source key'
bind = e1.bind_values
assert {'player', 'debut_team', 'debut_year'} <= set(bind.keys()), bind
e2 = reg.lookup_by_bind_values(bind)
assert e2 and e2.id == e1.id, (e1.id, e2)
wrong = dict(bind)
wrong['debut_year'] = '9999'
assert reg.lookup_by_bind_values(wrong) is None
alias_keys = [k for k, eid in reg._data.bind_index.items() if eid == e1.id]
assert len(alias_keys) == 1, alias_keys
assert e1.source_keys.get('lahman.playerID') == 'aaronha01'
print('OK debut bind', bind, 'uuid', e1.id)
"
```

**Pass:** one uuid for Aaron; exactly one `bind_index` key for that entity; debut bind resolves; wrong year misses.

---

## Check 4 — Player two-step (required)

**Do not pipe `mycelium query` into `jq`** — the CLI prints Rich-styled JSON (ANSI), not raw JSON.

Discover Aaron's debut bind from the registry, then run two-step query:

```bash
DEBUT_JSON=$(uv run python -c "
import json, os
from pathlib import Path
from network.paths import NetworkPaths, apply_network_paths
from agents.entity_registry import get_entity_registry, reset_entity_registry
root = Path(os.environ['ROOT'])
apply_network_paths(NetworkPaths.from_root(root))
reset_entity_registry()
e = get_entity_registry(record_type='player').lookup_by_source_key('lahman.playerID', 'aaronha01')
assert e, 'missing aaronha01'
print(json.dumps(e.bind_values))
")

STEP1=$(baseball_query "{\"lookup\": $DEBUT_JSON}")
echo "$STEP1" | jq '{outcome, total_matches, delivery_id: .delivery.delivery_id, record_type: .delivery.record_type}'

DELIVERY_ID=$(echo "$STEP1" | jq -r '.delivery.delivery_id')
baseball_query "{\"delivery_id\": \"$DELIVERY_ID\"}" | jq '{outcome, results: .results}'
```

**Pass:**

- Step 1: `outcome` = `lookup_resolved`, `total_matches` = 1, `delivery.delivery_id` present.
- Step 2: `outcome` = `found`; `results[0]` has `id`, `player`, `debut_team`, `debut_year` matching the debut bind.
- **No** `create_on_deliver` on step 1 delivery scope.
- Response JSON has **no** `entity_key` / `binding` legacy fields.

**Legacy `{player, team}` lookup** must `not_found`:

```bash
./bin/baseball-query '{"lookup": {"player": "Hank Aaron", "team": "Milwaukee Braves"}}' | \
  jq '{outcome, total_matches}'
```

**Pass:** `not_found` (team is not a player bind field post slice 1800).

**Optional smoke:** `uv run mycelium query --network-dir "$ROOT" --lookup-json '…'` — human-readable only; verify `lookup_resolved` in terminal output.

---

## Check 5 — Team record type resolve + deliver (required)

Pick a team name that exists (from SQL or registry):

```bash
TEAM_NAME="Brooklyn Dodgers"   # or another row from: sqlite3 "$WAREHOUSE" "SELECT DISTINCT name FROM Teams LIMIT 5;"

baseball_query "{\"lookup\": {\"team\": \"$TEAM_NAME\"}}" | \
  jq '{outcome, total_matches, delivery_id: .delivery.delivery_id, record_type: .delivery.record_type}'
```

Copy `delivery_id`, then:

```bash
baseball_query "{\"delivery_id\": \"$DELIVERY_ID\"}" | \
  jq '{outcome, results: .results}'
```

**Pass:**

- Step 1: `lookup_resolved`, 1 match, `delivery.record_type` = `team` (when present on delivery scope).
- Step 2: `found`; `results[0].team` = canonical team string.

---

## Check 6 — Closed identity (required)

```bash
baseball_query '{"lookup": {"player": "Nobody Here", "debut_team": "Nowhere Nine", "debut_year": "2099"}}' | \
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
entity = next(iter(get_entity_registry(record_type='player').list_entities()))
keys = set(entity.model_dump().keys())
required = {'id', 'bind_values', 'source_keys', 'source', 'validation_state'}
assert required <= keys, keys
assert 'name' not in keys or 'name' in entity.bind_values
print('OK sample entity', entity.id, entity.bind_values, entity.source_keys)
"
```

**Pass:** sample row has `bind_values` + `source_keys`; bind fields live under `bind_values`, not top-level.

---

## Check 8 — Partial player lookup (optional)

Name-only lookup on default player record type:

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

**Pass (optional):** `lookup_resolved` with `total_matches` ≥ 2 (Brooklyn + LA), or `lookup_suggested` with record-type-tagged candidates. **Skip** if no API key — not blocking ship.

---

## Check 10 — Network status (optional)

```bash
uv run mycelium network status --network-dir "$ROOT" --json | \
  jq '{network_name, registry_entity_count, ontology_present}'
```

```bash
jq '.mvr.record_types | keys' "$ROOT/network.json"
```

**Pass:** baseball network; entity count > 0; `network.json` record types include `player` and `team`. CRM-copy ontology present is **expected** (not blocking).

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