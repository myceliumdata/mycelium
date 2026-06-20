# Manual checks — Baseball M4b intent normalization gate (June 2026)

**Status:** ✅ **CLEAR** — Paul manual sign-off **2026-06-19**.

**Scope:** Synonym derive labels (`career_avg`, `batting_average`) normalize to one intent slug; storage/cache under slug; `results[]` and provenance `parameters.attribute` use the **requested** label; no second computation codegen on synonym deliver.

**Commit:** `5fdf865` — `baseball: intent normalization for derive cache dedup (M4b)`

**Design:** [`docs/plans/conversations/2026-06-20-baseball-m4b-intent-normalization.md`](../plans/conversations/2026-06-20-baseball-m4b-intent-normalization.md)

**Hand-test index:** [`2026-06-19-baseball-specialist-hand-test.md`](2026-06-19-baseball-specialist-hand-test.md) — M4b-1 row

**Owner:** Paul + Grok (not Cursor)

---

## Preconditions

Live root `~/mycelium-networks/baseball` with full Lahman bootstrap.

```bash
MYCELIUM_INTENT_NORMALIZATION_MODEL=gpt-4o-mini
MYCELIUM_COMPUTATION_CODEGEN_MODEL=gpt-4o
```

**Clear stale pre-M4b cache** when upgrading an existing root (legacy per-label rows still readable via intent-map alias scan after M-track polish):

```bash
rm -f ~/mycelium-networks/baseball/agents/batting/storage.json
rm -f ~/mycelium-networks/baseball/intent_map.json
./bin/refresh-example-network baseball --sync-only
# restart MCP if query_entity was already running
```

Recommended on first M4b validation; routine synonym delivers no longer require clearing between `career_avg` and `batting_average` when storage is already under the shared intent slug.

---

## Gate checks (Aaron `ba05e94b-e83c-4676-b646-64f0565e898f`)

| # | Check | Result |
|---|-------|--------|
| 1 | First deliver `career_avg` | `0.305`; derive + computation codegen |
| 2 | Second deliver `batting_average` | `0.305`; cache hit on shared intent |
| 3 | Same provenance timestamp | `2026-06-19T17:09:53.051774+00:00` on both |
| 4 | Same `computation.inline` | Identical `SUM(H)/SUM(AB)` codegen from step 1 |
| 5 | `intent_slug` | `career_batting_average` on both versions |
| 6 | Requested label in provenance | `parameters.attribute`: `career_avg` / `batting_average` respectively |
| 7 | `results[]` keys | Match client request (`career_avg` / `batting_average`) |
| 8 | Computation model | `gpt-4o` on first derive only |

---

## Step 1 prompts (partial lookup)

**Prompt 1 — derive:**

```json
{
  "lookup": {"player": "Hank Aaron"},
  "requested_attributes": ["career_avg"],
  "provenance": true
}
```

**Prompt 2 — synonym cache hit:**

```json
{
  "lookup": {"player": "Hank Aaron"},
  "requested_attributes": ["batting_average"],
  "provenance": true
}
```

Both returned `outcome: assembled` with value `0.305`.

---

## Known v1 caveats (non-blocking)

- **Legacy per-label cache** — Pre-M4b rows keyed by requested label (e.g. `career_avg`) are read when any label in `intent_map.json` maps to the same slug (M-track polish). Clear batting storage + `intent_map.json` only when validating a fresh upgrade.
- **Intent LLM on first synonym label** — Second synonym skips intent LLM when storage already holds the shared slug and map is warm (M-track polish P1).

---

## Next

- **LLM strict config** — Six required env vars; startup hard fail when unset ([`TODO.md`](../../TODO.md)).
- **M5 `EntityQuery.question`** — deferred unlikely ([`docs/plans/unlikely/README.md`](../../plans/unlikely/README.md)); NL stays in MCP host, not wire protocol.