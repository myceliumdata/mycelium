# Manual checks — gate before next code (Program 1 post-push)

**Status:** ⛔ **BLOCKED** — Paul must complete these three checks before Grok queues Cursor prompts or we write more implementation code.

**Context:** Program 1 (extended attribute provenance) shipped June 2026. Core hands-on (CLI `--provenance`, admin version history) is done. These three optional checks close the integration surface area.

**When all three pass:** Paul marks this file **CLEAR** (change status line below) or tells Grok “manual gate clear.” Grok may then lock Program 2 / queue the next slice.

---

## Check 1 — `network status --json` entity drill-down

Confirms slice 2 introspection: `entity_fields[].versions[]` on CLI status.

```bash
uv run mycelium network status --network crm --entity "Paul Murphy" --json
```

**Pass criteria:**

- `entity_matches` = 1
- `entity_fields` includes `linkedin` (extended)
- `linkedin` entry has `versions` array with at least one version (`pending` and/or `na`)
- Bind fields (`name`, `employer`) have no `versions` (or omit history)

---

## Check 2 — `crm-metering` + `--provenance` quote line

Confirms metering promise: `query_provenance` meter when `provenance=true`.

```bash
# Refresh if needed
./bin/refresh-example-network crm-metering --yes

# Quote step — expect quote_required (or inspect quote in response)
uv run mycelium query --network crm-metering \
  --entity-key "Paul Murphy" --employer "Ormi Labs" \
  --attributes linkedin --provenance
```

If `outcome` is `quote_required`, accept and re-run with `--quote-id`:

```bash
uv run mycelium query --network crm-metering \
  --entity-key "Paul Murphy" --employer "Ormi Labs" \
  --attributes linkedin --provenance \
  --quote-id <paste from quote.quote_id>
```

**Pass criteria:**

- Quote `line_items` includes a row with meter `query_provenance` (may appear alongside `query_value` / production meters)
- Accepted query returns non-null `provenance` when linkedin has versioned storage (same shape as CRM manual test)

---

## Check 3 — MCP `query_entity` with `provenance: true`

Confirms MCP schema + serialization path (slice 3).

Use your configured MCP server for **crm** (e.g. `mycelium-crm`). Payload:

```json
{
  "entity_key": "Paul Murphy",
  "requested_attributes": ["linkedin"],
  "provenance": true
}
```

**Pass criteria:**

- Tool returns valid `QueryResponse` JSON
- `outcome` is `assembled` (or `found`)
- `provenance.entities[].attributes.linkedin.versions` present when storage has history
- `results[].linkedin` remains flat (`"N/A"` or value) — provenance not merged into results

---

## After clearing the gate

1. Update **Status** at top of this file to `✅ CLEAR (YYYY-MM-DD)`.
2. Grok + Paul: read [`docs/plans/next-chunk-prep.md`](../plans/next-chunk-prep.md) for Program 2 decisions.
3. No new Cursor prompts in `prompts/cursor/next/` until gate is clear.

---

*Created: 2026-06-12 (post Program 1 push)*