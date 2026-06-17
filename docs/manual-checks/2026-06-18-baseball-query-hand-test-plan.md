# Baseball query — hand test plan (CLI + MCP)

**Status:** Use after **re-bootstrap** on a full Lahman root (post slice 1100 `player`/`team` bind keys).

**Purpose:** Copy-paste queries you run by hand. Same JSON works in `./bin/baseball-query` and MCP `query_entity`. Grok/CI already run automated tests — this doc is for **you**.

**Routing contract:** [`docs/query-grain-router.md`](../query-grain-router.md)

| Lookup keys | Grain | Typical step-1 outcome |
|-------------|-------|------------------------|
| `{player, team}` | player | `lookup_resolved` (1) or `lookup_suggested` / `not_found` |
| `{team}` | team | `lookup_resolved` (1 or multi) or `not_found` |
| `{player}` only | — | `lookup_incomplete` (`required_fields: ["team"]`) |
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

## B — Player grain (incomplete / negative)

### Q05 — Player only (no team)

```json
{"lookup": {"player": "Hank Aaron"}}
```

| Expect |
|--------|
| `outcome` = `lookup_incomplete` |
| `required_fields` includes `team` |
| `delivery` null |
| `total_matches` = `0` |

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

```json
{"lookup": {"name": "Hank Aaron", "team": "Milwaukee Braves"}}
```

| Expect |
|--------|
| `not_found` — **not** `lookup_resolved` with 3 team entities |

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

Requires `OPENAI_API_KEY` for real LLM expansion on first hit; otherwise `not_found` or pre-seeded `field_aliases`.

```json
{"lookup": {"team": "Dodgers"}}
```

| Expect (lenient) |
|------------------|
| First run without aliases: `not_found` or `lookup_suggested` |
| After expansion / seeded aliases: `lookup_resolved`, `total_matches` = 2 (Brooklyn + LA) |
| Record outcome |

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
| Q05 | `{player}` only | `lookup_incomplete` |
| Q06 | unknown bind | `not_found` / `lookup_suggested`, no create |
| Q08 | `{team}` Brooklyn | `lookup_resolved` → `found` |
| Q11 | `{name, team}` old | `not_found` |
| Q12 | `{name, team}` Milwaukee old | `not_found` |
| Q13 | `grain` field | parse error |
| Q14 | `{name}` team old | `not_found` |

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

- **Do not** pipe `uv run mycelium query` into `jq` — Rich ANSI output breaks JSON parsing. Use `./bin/baseball-query` or MCP.
- **CRM** is out of scope; run `./bin/smoke-crm-e2e` separately if needed.
- Parent ship gate (timing, SQL, registry counts): [`2026-06-17-baseball-identity-ship-gate.md`](2026-06-17-baseball-identity-ship-gate.md)
- After all **G** rows pass on your re-bootstrapped root, mark ship gate query sections **CLEAR** and continue checks 1–3 / 7 if not already done.