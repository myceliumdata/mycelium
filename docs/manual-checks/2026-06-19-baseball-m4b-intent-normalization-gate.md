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

**Clear stale pre-M4b cache** (per-label rows bypass intent slug until cleared):

```bash
rm -f ~/mycelium-networks/baseball/agents/batting/storage.json
rm -f ~/mycelium-networks/baseball/intent_map.json
./bin/refresh-example-network baseball --sync-only
# restart MCP if query_entity was already running
```

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

- **Legacy per-label cache** — If `storage.json` still has pre-M4b rows keyed by requested label, early `record.get(requested_key)` can return before intent resolution. Clear batting storage + `intent_map.json` when validating M4b on an existing root.
- **Intent LLM on each new label** — Second synonym still calls intent normalization to warm `intent_map.json`; only computation codegen is deduped.

---

## Next

- **M5** — NL `question` → intent slug → same derive path (framework lift).
- **LLM strict config** — Six required env vars; startup hard fail when unset ([`TODO.md`](../../TODO.md)).