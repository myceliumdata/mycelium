# Baseball query — hand test plan (CLI + MCP)

**Status:** Use after **re-bootstrap** on a full Lahman root (post slice 1100 `player`/`team` bind keys).

**Purpose:** Copy-paste queries you run by hand. Same JSON works in `./bin/baseball-query` and MCP `query_entity`. Grok/CI already run automated tests — this doc is for **you**.

**Routing contract:** [`docs/query-grain-router.md`](../query-grain-router.md)

| Lookup keys | Grain | Typical step-1 outcome |
|-------------|-------|------------------------|
| `{player, team}` | player | `lookup_resolved` (1) or `lookup_suggested` / `not_found` |
| `{team}` | team | `lookup_resolved` (1 or multi) or `not_found` |
| `{player}` only | player (partial) | known name → `lookup_resolved`; unknown → `lookup_incomplete` (`team`) |
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
| `delivery.grain` | `player` or `team` (on delivery scope; may be absent in minimal public dict — check step 2 `results` shape) |
| `required_fields` | On `lookup_incomplete` |
| `suggestions` | On `lookup_suggested` — non-empty array |
| `results` | Step 2 only — identity rows |

Step-1 success pattern: `outcome` = `lookup_resolved`, `total_matches` ≥ 1, `delivery.delivery_id` starts with `d_`, `results` = `[]`.

Step-2 success pattern: `outcome` = `found`, `results[0]` has `id`, `player`+`team` **or** `team` only.

---

## A — Player grain (happy path)

### Q01 — Aaron, primary team (Atlanta Braves)

**Step 1**

```json
{"lookup": {"player": "Hank Aaron", "team": "Atlanta Braves"}}
```

```bash
./bin/baseball-query '{"lookup": {"player": "Hank Aaron", "team": "Atlanta Braves"}}' | \
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
  jq '{outcome, id: .results[0].id, player: .results[0].player, team: .results[0].team}'
```

| Expect step 2 |
|---------------|
| `outcome` = `found` |
| `player` = `Hank Aaron` |
| `team` = `Atlanta Braves` (canonical primary bind) |
| `id` = stable uuid → set `AARON_ID` |

**MCP:** `query_entity('{"lookup": {"player": "Hank Aaron", "team": "Atlanta Braves"}}')` then step 2 JSON.

---

### Q02 — Aaron, alias team (Milwaukee Braves) — bind_index

Proves slice 1000: Milwaukee is not primary `bind_values` but is in `bind_index`.

**Step 1**

```json
{"lookup": {"player": "Hank Aaron", "team": "Milwaukee Braves"}}
```

| Expect step 1 |
|---------------|
| `outcome` = `lookup_resolved` |
| `total_matches` = `1` |

**Step 2**

| Expect step 2 |
|---------------|
| `outcome` = `found` |
| `id` = **same** as `AARON_ID` |
| `player` = `Hank Aaron` |
| `team` = `Atlanta Braves` in `results[0].team` (canonical row; lookup used alias bind) |

**UX note (open design):** Step 1 used Milwaukee Braves; step 2 returns **primary** `bind_values.team` (Atlanta), not the team from the lookup. Registry-correct (same uuid), but **feels wrong** (“I asked for Milwaukee”). Backlog: echo lookup team, `matched_bind`, or scope for specialists — TBD.

---

### Q03 — Aaron, another alias (Milwaukee Brewers)

If Lahman bootstrap committed this bind for `aaronha01`:

```json
{"lookup": {"player": "Hank Aaron", "team": "Milwaukee Brewers"}}
```

| Expect |
|--------|
| Same as Q02: one uuid, `lookup_resolved` |

If `not_found`: note in log — bind may be missing on your root (not a routing failure).

---

### Q04 — Two-step repeat (delivery_id workflow)

Run Q01 step 1, then step 2 twice with the same `delivery_id` (before expiry).

| Expect |
|--------|
| Both step 2 calls: `outcome` = `found`, same `id` |

---

### Q16 — UUID round-trip (player grain)

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
  jq '{outcome, id: .results[0].id, player: .results[0].player, team: .results[0].team}'
```

| Expect step 2 |
|---------------|
| `outcome` = `found` |
| `id` = **same** as `AARON_ID` |
| `player` = `Hank Aaron` |
| `team` = `Atlanta Braves` (canonical primary bind — not “all career teams”) |

**Negative:** `{"delivery_id": "<uuid>"}` (uuid where `delivery_id` belongs) → `not_found` or validation error — not a valid step-2 payload.

**MCP:** same JSON as step 1 / step 2 in `query_entity`.

---

## B — Player grain (incomplete / negative)

### Q05 — Player only (no team) — unknown name

```json
{"lookup": {"player": "Nobody Here"}}
```

| Expect |
|--------|
| `outcome` = `lookup_incomplete` |
| `required_fields` includes `team` |
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
| Same uuid as Q01 when full `{player, team}` bind exists |

Use any player with a unique `player` field index hit on your benchmark root (e.g. Hank Aaron, Ty Cobb).

---

### Q06 — Unknown player + team (closed grain)

```json
{"lookup": {"player": "Nobody Here", "team": "Nowhere Nine"}}
```

| Expect |
|--------|
| `outcome` = `not_found` **or** `lookup_suggested` |
| **Not** `lookup_resolved` with `create_on_deliver` |
| `delivery` null or no create scope |

---

### Q07 — Wrong homonym without team (if you have duplicate names)

Pick a common name from Lahman without team — or use a known homonym pair from warehouse SQL.

```json
{"lookup": {"player": "John Smith", "team": "Boston Red Sox"}}
```

| Expect |
|--------|
| `lookup_resolved` (1) **or** `lookup_suggested` (many) **or** `not_found` |
| Record which — documents real data, not a fixed pass |

---

## C — Team grain (happy path)

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
| No `player` field (team grain identity) |

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
{"lookup": {"name": "Hank Aaron", "team": "Atlanta Braves"}}
```

| Expect |
|--------|
| `outcome` = `not_found` |
| `delivery` null |

---

### Q12 — Old keys + Milwaukee (pre-1100 failure mode)

Uses legacy key **`name`**, not `player`. Do not confuse with **Q02** (`player` + Milwaukee), which should resolve.

```json
{"lookup": {"name": "Hank Aaron", "team": "Milwaukee Braves"}}
```

| Expect |
|--------|
| `not_found` — **not** `lookup_resolved` with 3 team entities |

If you get `lookup_resolved` + Hank Aaron / Atlanta, you likely ran **Q02** (`player` key) by mistake.

---

### Q13 — Removed `grain` override (must error at parse)

```json
{"lookup": {"player": "Hank Aaron", "team": "Atlanta Braves"}, "grain": "player"}
```

| Expect |
|--------|
| CLI/MCP: **validation error** — unknown field `grain` on `EntityQuery` |

---

### Q14 — Team lookup using old `name` key

```json
{"lookup": {"name": "Brooklyn Dodgers"}}
```

| Expect |
|--------|
| `not_found` (key `name` not in any grain bind_fields) |

---

## E — Team nicknames (optional — needs alias data or OPENAI_API_KEY)

Run only if you want lazy field-alias behavior on closed team grain.

### Q15 — Nickname `Dodgers` (0-hit → expansion or suggest)

Requires `OPENAI_API_KEY` for real LLM expansion on first hit; otherwise immediate `not_found` (no LLM call).

```json
{"lookup": {"team": "Dodgers"}}
```

**Important:** `./bin/baseball-query` does **not** call `load_dotenv()` — a key only in repo `.env` is invisible unless exported. MCP server **does** load `.env`.

```bash
# Before Q15 via baseball-query (from repo root):
set -a && source .env && set +a
export MYCELIUM_NETWORK_ROOT="$ROOT"

./bin/baseball-query '{"lookup": {"team": "Dodgers"}}' | jq '{outcome, total_matches}'
```

| Expect (lenient) |
|------------------|
| Without API key in **process env**: immediate `not_found` |
| With key + first run (no aliases yet): `lookup_resolved` after LLM writes `field_aliases` (may take a few seconds) |
| `total_matches` ≥ 2 (Brooklyn + LA; may be higher if aliases already polluted from prior runs) |
| Record outcome |

**Backlog:** `bin/baseball-query` should `load_dotenv()` like MCP/CLI main — slice TBD.

---

## F — MCP-specific (same queries, extra tools)

Use the same JSON as Q01–Q14 in `query_entity`. Additionally:

### M01 — `describe_network`

Call MCP tool `describe_network` (no args).

| Expect |
|--------|
| Parseable JSON; mentions baseball grains |
| Text describes `{player, team}` vs `{team}` routing |
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
{"lookup": {"player": "Hank Aaron", "team": "Atlanta Braves"}, "thread_id": "hand-test-1"}
```

| Expect |
|--------|
| Same as Q01; response includes `thread_id`: `hand-test-1` |

---

## G — Quick matrix (checklist)

| ID | Query shape | Expected `outcome` (step 1) |
|----|-------------|-----------------------------|
| Q01 | `{player, team}` Atlanta | `lookup_resolved` → `found` |
| Q02 | `{player, team}` Milwaukee Braves | `lookup_resolved`, same uuid |
| Q05 | `{player}` unknown | `lookup_incomplete` |
| Q17 | `{player}` known unique | `lookup_resolved` |
| Q06 | unknown bind | `not_found` / `lookup_suggested`, no create |
| Q08 | `{team}` Brooklyn | `lookup_resolved` → `found` |
| Q10 | `{id}` team uuid | `lookup_resolved` → `found` |
| Q11 | `{name, team}` old | `not_found` |
| Q12 | `{name, team}` Milwaukee old | `not_found` |
| Q13 | `grain` field | parse error |
| Q14 | `{name}` team old | `not_found` |
| Q16 | `{id}` player uuid (`AARON_ID`) | `lookup_resolved` → `found`, same uuid |

---

## H — Career teams (out of query protocol)

**Not a ship-gate pass/fail row.** The two-step identity API returns **one** canonical player row per deliver (`team` = primary bind in `bind_values`, e.g. Atlanta Braves). It does **not** list every team a player appeared for. No `requested_attributes` path for roster or career-team lists in identity scope.

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

On full Lahman you should see **three** fan-facing names (e.g. Indianapolis Clowns, Milwaukee Braves, Milwaukee Brewers) — distinct from the single `team` on step-2 deliver.

### H2 — Registry `bind_index` scan (bootstrap aliases)

Lists every `(player, team)` bind key committed for Aaron’s uuid (should align with warehouse teams bootstrap indexed):

```bash
uv run python -c "
import os
from pathlib import Path
from network.paths import NetworkPaths, apply_network_paths
from agents.entity_registry import get_entity_registry, reset_entity_registry

root = Path(os.environ['ROOT'])
apply_network_paths(NetworkPaths.from_root(root))
reset_entity_registry()
reg = get_entity_registry(grain='player')
e = reg.lookup_by_source_key('lahman.playerID', 'aaronha01')
assert e, 'missing aaronha01'
alias_keys = sorted(k for k, eid in reg._data.bind_index.items() if eid == e.id)
print('uuid', e.id)
print('bind_index keys for entity', len(alias_keys))
print('sample keys', alias_keys[:5])
print('primary bind team', e.bind_values.get('team'))
"
```

**Expect:** `bind_index keys for entity` ≥ number of distinct teams from H1 (normalized `player|team` strings — use H1 for readable labels); `primary bind team` matches Q01/Q16 step-2 `results[0].team`.

### H3 — Per-team lookups (proof, not enumeration)

`{"lookup": {"player": "Hank Aaron", "team": "<each team from H1>"}}` should each `lookup_resolved` to the **same** uuid (Q02/Q03 pattern). That proves a team was a valid bind alias; it does **not** discover unknown teams without trying every franchise name.

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
| **Alias lookup → canonical team on deliver** (Q02) | Step 1 accepts `{player, team: Milwaukee}`; step 2 `results[0].team` is **primary** bind (e.g. Atlanta). Same uuid — correct for registry — but **odd UX**. Decide before specialist assembly: surface `lookup` echo, `matched_bind`, or scope team for downstream reads. |
| **Q12 vs Q02** | Q12 uses `{name, …}` → `not_found`. Q02 uses `{player, team: Milwaukee}` → resolve + canonical Atlanta on deliver. |
| **Q15 + `.env`** | `OPENAI_API_KEY` in `.env` alone is not enough for `./bin/baseball-query`; export or use MCP. |

- **Do not** pipe `uv run mycelium query` into `jq` — Rich ANSI output breaks JSON parsing. Use `./bin/baseball-query` or MCP.
- **CRM** is out of scope; run `./bin/smoke-crm-e2e` separately if needed.
- Parent ship gate (timing, SQL, registry counts): [`2026-06-17-baseball-identity-ship-gate.md`](2026-06-17-baseball-identity-ship-gate.md)
- **Career teams:** use **H1** or **H2** — not the public query protocol (see § H).
- After all **G** rows pass on your re-bootstrapped root, mark ship gate query sections **CLEAR** and continue checks 1–3 / 7 if not already done.