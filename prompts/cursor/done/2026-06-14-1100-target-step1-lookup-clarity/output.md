# Target step-1 lookup clarity — outcomes, suggestions, confirm_new_entity

## Summary

Step-1 target resolution now distinguishes partial lookup gaps (`lookup_incomplete`), same-name/fuzzy near-misses (`lookup_suggested`), and intentional new binds (`confirm_new_entity`). Silent `create_on_deliver` when the same name exists under a different employer is blocked unless the agent explicitly confirms.

## Outcome table

| Case | Example | Outcome | `delivery` | Key fields |
|------|---------|---------|------------|------------|
| Partial lookup, 0 hits | `{"name":"Paul Murphy"}` | `lookup_incomplete` | none | `required_fields: ["employer"]` |
| Partial lookup, ≥1 hit | `{"name":"Andrea Kalmans"}` | `lookup_resolved` | yes | `total_matches: N` |
| Full MVR, same name elsewhere | Andrea @ Wrong Corp | `lookup_suggested` | none | `suggestions[]` (`same_name_different_employer`) |
| Full MVR, fuzzy name | Kalman @ Acme | `lookup_suggested` | none | `suggestions[]` (`sequence_ratio`) |
| Full MVR, safe create | Road Runner @ Acme | `lookup_resolved` | yes | `create_on_deliver: true` |
| Full MVR, confirm after warning | Andrea @ Wrong + `confirm_new_entity` | `lookup_resolved` | yes | `create_on_deliver: true` |
| True dead end | unknown `id`, expired `delivery_id` | `not_found` | none | unchanged |

## Example JSON

**lookup_incomplete**

```json
{
  "outcome": "lookup_incomplete",
  "total_matches": 0,
  "required_fields": ["employer"],
  "message": "No records found for partial lookup. Include employer to create a new entity."
}
```

**lookup_suggested (same name, different employer)**

```json
{
  "outcome": "lookup_suggested",
  "total_matches": 0,
  "suggestions": [
    {
      "id": "…",
      "entity_key": "Andrea Kalmans",
      "employer": "Lontra Ventures",
      "reason": "same_name_different_employer"
    }
  ],
  "message": "Name matches existing row(s) with a different employer. Retry with id or corrected lookup, or set confirm_new_entity to create a new row."
}
```

**lookup_resolved create (after confirm)**

```json
{
  "outcome": "lookup_resolved",
  "total_matches": 0,
  "delivery": { "delivery_id": "…", "create_on_deliver": true }
}
```

## Changes

| Area | Change |
|------|--------|
| `src/agents/target_resolve.py` | Step-1 decision tree: incomplete / suggested / confirm / safe create |
| `src/network/mvr.py` | `missing_mvr_bind_fields()` helper |
| `src/models/state.py` | `confirm_new_entity` on `EntityQuery`; extended `public_dict()` omission |
| `src/agents/responses.py` | `response_lookup_incomplete`, `response_lookup_suggested` |
| `src/agents/dispatch.py` | Wire new outcomes in `target_resolve_node` |
| `src/main.py` | `--confirm-new-entity` CLI flag |
| `src/network/introspection.py` | Updated policy strings |
| `src/mycelium_mcp/server.py` | Schema descriptions for new outcomes + confirm flag |
| `docs/architecture.md` | M9 paragraph |
| `examples/networks/crm/README.md` | One-line note |
| `admin-ui/` | Badges, confirm checkbox, optional chaining |
| **Tests** | `test_target_step1_lookup_clarity.py` (8 tests); updated `test_mvr_create_on_deliver.py`, `test_admin_daemon.py`, `test_mvr_entity_query_models.py` |

## Admin UI

- Outcome badges for `lookup_incomplete` and `lookup_suggested`.
- **Confirm new entity** checkbox appears after `lookup_suggested`; sets `confirm_new_entity` on next step-1 Run.
- `required_fields` / `suggestions` shown when present in response.

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 403 passed, 26 deselected
```

Manual:

```bash
uv run mycelium query --network crm --lookup-json '{"name":"Paul Murphy"}'
uv run mycelium query --network crm --lookup-json '{"name":"Andrea Kalmans","employer":"Wrong Corp"}'
uv run mycelium query --network crm --lookup-json '{"name":"Andrea Kalmans","employer":"Wrong Corp"}' --confirm-new-entity
```

## For Grok + Paul

- **Breaking change (minor):** Partial lookup with 0 hits now returns `lookup_incomplete` instead of `not_found`. Full MVR with same-name collision returns `lookup_suggested` instead of silent `create_on_deliver`.
- **Gate doc:** Consider noting new step-1 outcomes and `confirm_new_entity` in agent onboarding examples.
- **Local hygiene:** Removed stray `examples/networks/crm/entities.json` (runtime artifact) that blocked `test_example_crm_layout`.
- **Not committed** — awaiting review.

Suggested commit message:

```
feat: clarify target step-1 lookup with suggestions and confirm_new_entity

Add lookup_incomplete and lookup_suggested outcomes; require confirm_new_entity
for create when same name exists under different employer; omit empty negotiation
fields in public JSON; update onboarding policy.
```
