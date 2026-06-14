# QueryResponse public JSON — omit N/A fields (outcome-aware)

## Summary

`QueryResponse.public_dict()` now omits fields that do not apply to the response `outcome`. Step-2 `found`/`assembled`/`not_found` responses no longer emit `total_matches: null` or `delivery: null`; null `quote` and `provenance` are absent keys on all outcomes.

## Changes

| Area | Change |
|------|--------|
| **`src/models/state.py`** | `_STEP1_PUBLIC_OUTCOMES` + outcome-aware `public_dict()` using `exclude_none` and selective pops |
| **`docs/architecture.md`** | Public surfaces paragraph updated |
| **`src/mycelium_mcp/server.py`** | QueryResponse schema description — omitted fields, not null |
| **Tests** | Replaced `test_public_dict_preserves_explicit_null_top_level_fields` with step-1/step-2/quote_required tests; updated deliver, MCP, CLI, admin assertions |

## Omission rules (implemented)

**Step-1 outcomes** (`lookup_resolved`, `quote_required`, `payment_required`, `principal_required`): include `total_matches`, `delivery`, `quote` when set; omit null `quote`/`provenance`.

**Deliver/terminal outcomes** (`found`, `assembled`, `not_found`, …): omit `total_matches` and `delivery`; omit null `quote`/`provenance`; always include `results`.

In-memory `QueryResponse` models unchanged (`step2.total_matches is None` still valid internally).

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 392 passed, 26 deselected
```

Manual sanity:

```bash
# Step 1 — total_matches + delivery; no quote key
uv run mycelium query --network crm \
  --lookup-json '{"name": "Road Runner", "employer": "Acme Corp"}'

# Step 2 — results only; no total_matches or delivery keys
uv run mycelium query --network crm --delivery-id <delivery_id>
```

## For Grok + Paul

- **Breaking change (minor):** Clients parsing explicit `null` for `quote`, `total_matches`, `delivery`, or `provenance` on deliver responses must treat absent keys as N/A. Unlikely to affect real clients.
- **Admin UI:** No change required — already hides null `total_matches`.
- **Gate doc:** Optional note that step-2 JSON no longer shows null step-1 fields.
- **Local hygiene:** Removed stray `examples/networks/crm/entities.json` that blocked `test_example_crm_layout` (gitignored runtime artifact).
- **Not committed** — awaiting review.

Suggested commit message:

```
fix: omit N/A QueryResponse fields in public JSON by outcome

Omit total_matches and delivery on step-2 deliver responses; omit null
quote and provenance. Aligns with create_on_deliver omission precedent.
```
