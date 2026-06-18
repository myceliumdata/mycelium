# Baseball query — hand test plan (CLI + MCP)

**Status:** ✅ Hand plan **CLEAR** (Paul, 2026-06-18). Parent ship gate **CLEAR (WIP)**. Use on a full Lahman root (post slice 1800 `player`/`debut_team`/`debut_year` bind keys).

**Purpose:** Copy-paste queries you run by hand. Same JSON works in `./bin/baseball-query` and MCP `query_entity`. Grok/CI already run automated tests — this doc is for **you**.

**Routing contract:** [`docs/query-record-type-router.md`](../query-record-type-router.md)

| Lookup keys | Record type | Typical step-1 outcome |
|-------------|-------------|------------------------|
| `{player, debut_team, debut_year}` | player | `lookup_resolved` (1) |
| `{player, debut_team}` | player (partial) | `lookup_resolved` or multi-match |
| `{player}` only | player (partial) | known name → `lookup_resolved`; unknown → `not_found` |
| `{team}` | team | `lookup_resolved` (1 or multi) or `not_found` |
| `{player, team}` (legacy) | — | `not_found` |
| `{name, …}` (old keys) | — | `not_found` |

---

## One-time setup

```bash
cd /path/to/mycelium
uv sync

export ROOT="${ROOT:-/tmp/mycelium-baseball-benchmark}"
export MYCELIUM_NETWORK_ROOT="$ROOT"

# If root still has pre-1100 data, refresh first:
# /usr/bin/time -p ./bin/refresh-example-network baseball --root "$ROOT" --yes --no-default
```

**CLI** (raw JSON for `jq`):

```bash
./bin/baseball-query '<JSON>'
```

**MCP** — start server with `MYCELIUM_NETWORK_ROOT="$ROOT"` (or register network name), then call tool `query_entity` with the **same JSON string** as the sole argument. Step 2 uses `{"delivery_id": "d_…"}` only.

**Record once** (from Q01 step 2): set these for later tests.

```bash
export AARON_ID="<uuid from results[0].id>"
```

---

## How to read expectations

Each test lists **check these fields** — not the full JSON blob. Use `jq` snippets or read MCP JSON.

| Field | Meaning |
|-------|---------|
| `outcome` | Primary pass/fail |
| `total_matches` | Step 1 match count |
| `delivery.delivery_id` | Present on successful step 1 resolve |
| `delivery.record_type` | `player` or `team` (on delivery scope; may be absent in minimal public dict — check step 2 `results` shape) |
| `required_fields` | On `lookup_incomplete` |
| `suggestions` | On `lookup_suggested` — non-empty array |
| `results` | Step 2 only — identity rows |

Step-1 success pattern: `outcome` = `lookup_resolved`, `total_matches` ≥ 1, `delivery.delivery_id` starts with `d_`, `results` = `[]`.

Step-2 success pattern: `outcome` = `found`, `results[0]` has `id`, `player`+`debut_team`+`debut_year` **or** `team` only.

**Discover Aaron debut bind** (run once per root; full Lahman typically Milwaukee Braves / 1954):

```bash
export DEBUT_JSON=$(uv run python -c "
import json, os
from pathlib import Path
from network.paths import NetworkPaths, apply_network_paths
from agents.entity_registry import get_entity_registry, reset_entity_registry
root = Path(os.environ['ROOT'])
apply_network_paths(NetworkPaths.from_root(root))
reset_entity_registry()
e = get_entity_registry(record_type='player').lookup_by_source_key('lahman.playerID', 'aaronha01')
assert e, 'missing aaronha01 — re-bootstrap post slice 1800'
print(json.dumps(e.bind_values))
")
echo "$DEBUT_JSON"
```

---

## A — Player record type (happy path)

### Q01 — Aaron, full debut bind

**Step 1** — use `DEBUT_JSON` from setup (example shape):

```json
{"lookup": {"player": "Hank Aaron", "debut_team": "Milwaukee Braves", "debut_year": "1954"}}
```

```bash
./bin/baseball-query "{\"lookup\": $DEBUT_JSON}" | \
  jq '{outcome, total_matches, delivery_id: .delivery.delivery_id}'
```

| Expect step 1 |
|---------------|
| `outcome` = `lookup_resolved` |
| `total_matches` = `1` |
| `delivery_id` present |

**Step 2** — paste `delivery_id` from step 1:

```bash
./bin/baseball-query '{"delivery_id": "PASTE_D_ID"}' | \
  jq '{outcome, id: .results[0].id, player: .results[0].player, debut_team: .results[0].debut_team, debut_year: .results[0].debut_year}'
```

| Expect step 2 |
|---------------|
| `outcome` = `found` |
| `player` = `Hank Aaron` |
| `debut_team` / `debut_year` match `DEBUT_JSON` |
| `id` = stable uuid → set `AARON_ID` |

**MCP:** `query_entity('{"lookup": …}')` with the same debut bind, then step 2 JSON.

---

### Q02 — Aaron, partial debut (missing year)

```json
{"lookup": {"player": "Hank Aaron", "debut_team": "Milwaukee Braves"}}
```

| Expect step 1 |
|---------------|
| `outcome` = `lookup_resolved` or `lookup_incomplete` (partial bind) |
| Record which on your root |

---

### Q03 — Aaron, wrong debut year (negative)

```json
{"lookup": {"player": "Hank Aaron", "debut_team": "Milwaukee Braves", "debut_year": "2099"}}
```

| Expect |
|--------|
| `not_found` |
| `total_matches` = `0` |

---

### Q04 — Two-step repeat (delivery_id workflow)

Run Q01 step 1, then step 2 twice with the same `delivery_id` (before expiry).

| Expect |
|--------|
| Both step 2 calls: `outcome` = `found`, same `id` |

---

### Q16 — UUID round-trip (player record type)

After Q01, `AARON_ID` is set. Proves step-1 `id` resolve → fresh `delivery_id` → step-2 deliver. **Step 2 never accepts a raw uuid** — only `delivery_id`.

**Step 1**

```json
{"id": "PASTE_AARON_ID"}
```

```bash
./bin/baseball-query "{\"id\": \"$AARON_ID\"}" | \
  jq '{outcome, total_matches, delivery_id: .delivery.delivery_id, results}'
```

| Expect step 1 |
|---------------|
| `outcome` = `lookup_resolved` |
| `total_matches` = `1` |
| `delivery_id` present (new `d_…`, not reused from Q01) |
| `results` = `[]` (no uuid in step-1 body) |

**Step 2** — paste `delivery_id` from Q16 step 1:

```bash
./bin/baseball-query '{"delivery_id": "PASTE_D_ID"}' | \
  jq '{outcome, id: .results[0].id, player: .results[0].player, debut_team: .results[0].debut_team, debut_year: .results[0].debut_year}'
```

| Expect step 2 |
|---------------|
| `outcome` = `found` |
| `id` = **same** as `AARON_ID` |
| `player` = `Hank Aaron` |
| debut fields match Q01 / `DEBUT_JSON` |

**Negative:** `{"delivery_id": "<uuid>"}` (uuid where `delivery_id` belongs) → `not_found` or validation error — not a valid step-2 payload.

**MCP:** same JSON as step 1 / step 2 in `query_entity`.

---

## B — Player record type (incomplete / negative)

### Q05 — Player only — unknown name

```json
{"lookup": {"player": "Nobody Here"}}
```

| Expect |
|--------|
| `outcome` = `not_found` (bootstrap-only player type) |
| `delivery` null |
| `total_matches` = `0` |

---

### Q17 — Player only — known unique name (CRM parity)

```json
{"lookup": {"player": "Hank Aaron"}}
```

| Expect |
|--------|
| `outcome` = `lookup_resolved` |
| `total_matches` = `1` |
| `delivery.delivery_id` present |
| Same uuid as Q01 when Aaron is a unique field-index hit |

Use any player with a unique `player` field index hit on your benchmark root (e.g. Hank Aaron, Ty Cobb).

---

### Q06 — Unknown full debut bind (`bootstrap_only`)

```json
{"lookup": {"player": "Nobody Here", "debut_team": "Nowhere Nine", "debut_year": "2099"}}
```

| Expect |
|--------|
| `outcome` = `not_found` **or** `lookup_suggested` |
| **Not** `lookup_resolved` with `create_on_deliver` |
| `delivery` null or no create scope |

---

### Q07 — Homonym with partial bind (if you have duplicate names)

Pick a common name from Lahman — or use a known homonym pair from warehouse SQL.

```json
{"lookup": {"player": "John Smith", "debut_team": "Boston Red Sox"}}
```

| Expect |
|--------|
| `lookup_resolved` (1) **or** `lookup_suggested` (many) **or** `not_found` |
| Record which — documents real data, not a fixed pass |

---

## C — Team record type (happy path)

### Q08 — Canonical team (Brooklyn Dodgers)

```json
{"lookup": {"team": "Brooklyn Dodgers"}}
```

| Expect step 1 |
|---------------|
| `outcome` = `lookup_resolved` |
| `total_matches` = `1` |

**Step 2**

| Expect step 2 |
|---------------|
| `outcome` = `found` |
| `results[0].team` = `Brooklyn Dodgers` |
| No `player` field (team record type identity) |

---

### Q09 — Second franchise identity (Los Angeles Dodgers)

```json
{"lookup": {"team": "Los Angeles Dodgers"}}
```

| Expect |
|--------|
| `lookup_resolved`, 1 match |
| Step 2: `team` = `Los Angeles Dodgers` |
| `id` **≠** Brooklyn Dodgers uuid (two fan-facing teams) |

---

### Q10 — id-only step 1 (team row)

Use `id` from Q08 step 2.

```json
{"id": "PASTE_BROOKLYN_TEAM_UUID"}
```

| Expect |
|--------|
| `outcome` = `lookup_resolved` |
| `total_matches` = `1` |

---

## D — Regression guards (old / wrong keys)

These should **fail cleanly** after 1100 — not return three random teams.

### Q11 — Old player keys (`name` not `player`)

```json
{"lookup": {"name": "Hank Aaron", "debut_team": "Milwaukee Braves", "debut_year": "1954"}}
```

| Expect |
|--------|
| `outcome` = `not_found` |
| `delivery` null |

---

### Q12 — Legacy `{name, team}` keys

Uses legacy keys **`name`** and **`team`**, not debut bind fields.

```json
{"lookup": {"name": "Hank Aaron", "team": "Milwaukee Braves"}}
```

| Expect |
|--------|
| `not_found` — pre-1800 `{player, team}` routing is gone |

---

### Q13 — Removed step-1 record type override (must error at parse)

```json
{"lookup": {"player": "Hank Aaron", "debut_team": "Milwaukee Braves", "debut_year": "1954"}, "record_type": "player"}
```

| Expect |
|--------|
| CLI/MCP: **validation error** — unknown field `record_type` on `EntityQuery` (routing is lookup-key only) |

---

### Q14 — Team lookup using old `name` key

```json
{"lookup": {"name": "Brooklyn Dodgers"}}
```

| Expect |
|--------|
| `not_found` (key `name` not in any record type bind_fields) |

---

## E — Team nicknames (optional — needs alias data or OPENAI_API_KEY)

Run only if you want lazy field-alias behavior on `bootstrap_only` team record type.

### Q15 — Nickname `Dodgers` (0-hit → expansion or suggest)

Requires `OPENAI_API_KEY` for real LLM expansion on first hit; otherwise immediate `not_found` (no LLM call).

```json
{"lookup": {"team": "Dodgers"}}
```

**Env:** `./bin/baseball-query` loads `mycelium/.env` at startup (same as MCP). Run from any cwd; keep `OPENAI_API_KEY` in repo `.env` for Q15 LLM alias expansion.

```bash
export MYCELIUM_NETWORK_ROOT="$ROOT"
./bin/baseball-query '{"lookup": {"team": "Dodgers"}}' | jq '{outcome, total_matches}'
```

| Expect (lenient) |
|------------------|
| Without `OPENAI_API_KEY` in repo `.env`: immediate `not_found` |
| With key + first run (no aliases yet): `lookup_resolved` after LLM writes `field_aliases` (may take a few seconds) |
| `total_matches` ≥ 2 (Brooklyn + LA; may be higher if aliases already polluted from prior runs) |
| Record outcome |

---

## F — MCP-specific (same queries, extra tools)

Use the same JSON as Q01–Q14 in `query_entity`. Additionally:

### M01 — `describe_network`

Call MCP tool `describe_network` (no args).

| Expect |
|--------|
| Parseable JSON; mentions baseball record types |
| Text describes `{player, debut_team, debut_year}` vs `{team}` routing |
| `guide.md` content or summary present |

---

### M02 — Health / ping

MCP `health_check` (or equivalent ping tool your server exposes).

| Expect |
|--------|
| JSON status ok; registry reachable under `MYCELIUM_NETWORK_ROOT` |

---

### M03 — MCP thread_id

```json
{"lookup": {"player": "Hank Aaron", "debut_team": "Milwaukee Braves", "debut_year": "1954"}, "thread_id": "hand-test-1"}
```

| Expect |
|--------|
| Same as Q01; response includes `thread_id`: `hand-test-1` |

---

## G — Quick matrix (checklist)

| ID | Query shape | Expected `outcome` (step 1) |
|----|-------------|-----------------------------|
| Q01 | full debut bind | `lookup_resolved` → `found` |
| Q02 | `{player, debut_team}` partial | `lookup_resolved` or `lookup_incomplete` |
| Q03 | wrong debut year | `not_found` |
| Q05 | `{player}` unknown | `not_found` |
| Q17 | `{player}` known unique | `lookup_resolved` |
| Q06 | unknown full bind | `not_found` / `lookup_suggested`, no create |
| Q08 | `{team}` Brooklyn | `lookup_resolved` → `found` |
| Q10 | `{id}` team uuid | `lookup_resolved` → `found` |
| Q11 | `{name, …}` old keys | `not_found` |
| Q12 | `{name, team}` legacy | `not_found` |
| Q13 | `record_type` field | parse error |
| Q14 | `{name}` team old | `not_found` |
| Q16 | `{id}` player uuid (`AARON_ID`) | `lookup_resolved` → `found`, same uuid |

---

## H — Career teams (out of query protocol)

**Not a ship-gate pass/fail row.** The two-step identity API returns **one** canonical player row per deliver (debut bind in `bind_values`). It does **not** list every team a player appeared for. No `requested_attributes` path for roster or career-team lists in identity scope.

Use these when you need “what teams did Hank Aaron play on?”:

### H1 — Warehouse SQL (authoritative Lahman)

Same pattern as ship gate Check 2 — [`2026-06-17-baseball-identity-ship-gate.md`](2026-06-17-baseball-identity-ship-gate.md):

```bash
export WAREHOUSE="${WAREHOUSE:-$ROOT/warehouse/lahman.sqlite}"

sqlite3 "$WAREHOUSE" "
SELECT DISTINCT t.name AS team_label
FROM Appearances a
JOIN Teams t ON a.teamID = t.teamID AND a.yearID = t.yearID
JOIN People p ON a.playerID = p.playerID
WHERE p.playerID = 'aaronha01'
ORDER BY team_label;
"
```

On full Lahman you should see **three** fan-facing names (e.g. Indianapolis Clowns, Milwaukee Braves, Milwaukee Brewers) — distinct from the single debut bind on step-2 deliver.

### H2 — Registry debut bind (one per player)

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
e = reg.lookup_by_source_key('lahman.playerID', 'aaronha01')
assert e, 'missing aaronha01'
alias_keys = sorted(k for k, eid in reg._data.bind_index.items() if eid == e.id)
print('uuid', e.id)
print('bind_index keys for entity', len(alias_keys))
print('debut bind', e.bind_values)
"
```

**Expect:** exactly **one** `bind_index` key for Aaron; `debut_team` / `debut_year` match Q01.

### H3 — Legacy `{player, team}` lookups (negative)

`{"lookup": {"player": "Hank Aaron", "team": "<each team from H1>"}}` should **`not_found`** post slice 1800 — career teams are not player bind fields.

---

## jq one-liners (optional)

```bash
# Step 1 summary
alias bq1='./bin/baseball-query "$1" | jq "{outcome, total_matches, delivery_id: .delivery.delivery_id}"'

# Step 2 identity
alias bq2='./bin/baseball-query "$1" | jq "{outcome, results: .results}"'
```

---

## Notes

### Open design / manual findings (June 2026)

| Topic | Status |
|-------|--------|
| **Debut bind only** | Player identity is one debut tuple per `playerID`; warehouse lists career teams (H1). |
| **Q12 vs Q01** | Q12 uses legacy `{name, team}` → `not_found`. Q01 uses debut bind keys. |
| **Q15 + `.env`** | `baseball-query` loads repo `.env`; Q15 needs `OPENAI_API_KEY` there. |
| **Provenance on attrs** | `provenance=true` works; baseball bio/stats lineage is CRM research today — re-examine with warehouse specialists ([`TODO.md`](../../TODO.md)). |

- **Do not** pipe `uv run mycelium query` into `jq` — Rich ANSI output breaks JSON parsing. Use `./bin/baseball-query` or MCP.
- **CRM** is out of scope; run `./bin/smoke-crm-e2e` separately if needed.
- Parent ship gate (timing, SQL, registry counts): [`2026-06-17-baseball-identity-ship-gate.md`](2026-06-17-baseball-identity-ship-gate.md)
- **Career teams:** use **H1** or **H2** — not the public query protocol (see § H).
- Ship gate query sections **CLEAR** (2026-06-18). Checks 1–3 / 7 on ship gate doc: confirm separately if not already logged.