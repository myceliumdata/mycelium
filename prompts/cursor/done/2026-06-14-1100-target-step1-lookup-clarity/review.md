# Review: 2026-06-14-1100-target-step1-lookup-clarity

**Verdict: Approved**

## CI

| Step | Result |
|------|--------|
| `./bin/ci-local` (Grok, 2026-06-14) | **Pass** — 403 smoke passed, 26 deselected; ruff clean; admin-ui build ok |
| Cursor `output.md` claim | 403 passed — matches |

**Pre-commit hygiene:** Deleted stray `examples/networks/crm/entities.json` before CI (runtime artifact; not in slice diff).

## Delivery

| Artifact | Present |
|----------|---------|
| `src/agents/target_resolve.py` — decision tree | ✅ |
| `src/agents/dispatch.py` — wire new outcomes | ✅ |
| `src/agents/responses.py` — builders | ✅ |
| `src/models/state.py` — `confirm_new_entity`, `public_dict` | ✅ |
| `src/network/mvr.py` — `missing_mvr_bind_fields` | ✅ |
| `src/main.py` — `--confirm-new-entity` | ✅ |
| `src/network/introspection.py` — target policy | ✅ |
| `src/mycelium_mcp/server.py` — schema descriptions | ✅ |
| `admin-ui/` — badges, checkbox, optional fields | ✅ |
| `docs/architecture.md` M9 | ✅ |
| `examples/networks/crm/README.md` | ✅ |
| `tests/test_target_step1_lookup_clarity.py` (8 tests) | ✅ |
| Updated smoke tests | ✅ |
| `output.md` / `prompt.md` | ✅ |

## Diff reviewed

- `src/agents/target_resolve.py`
- `src/agents/dispatch.py`
- `src/agents/responses.py`
- `src/models/state.py`
- `src/network/mvr.py`
- `src/network/introspection.py`
- `src/main.py`
- `src/mycelium_mcp/server.py`
- `admin-ui/src/App.tsx`, `admin-ui/src/api.ts`, `admin-ui/src/types.ts`
- `docs/architecture.md`
- `examples/networks/crm/README.md`
- `tests/test_target_step1_lookup_clarity.py`
- `tests/test_mvr_create_on_deliver.py`
- `tests/test_mvr_entity_query_models.py`
- `tests/test_admin_daemon.py`
- `prompt.md`, `output.md`

## Spec compliance

| Exit criterion | Pass |
|----------------|------|
| Step-1 outcomes disambiguate partial / suggested / create / match | ✅ |
| `confirm_new_entity` wired CLI + MCP + admin | ✅ |
| Same-name different-employer blocks silent create | ✅ |
| Fuzzy name suggestions on target path | ✅ |
| Empty `required_fields`/`suggestions` omitted in public JSON | ✅ |
| `describe_network` policy updated | ✅ |
| `./bin/ci-local` green | ✅ |
| Tests per prompt matrix | ✅ (8 dedicated + 3 updated) |

## Legacy / dual-path

- Legacy `entity_key` graph unchanged.
- `can_create_on_zero_matches` retained in `mvr.py` (unused by new tree; harmless).
- `not_found` still used for unknown `id` and empty step-1 query.

## Tests

Strong coverage: incomplete, partial hit, same-name collision, confirm create, safe create, fuzzy, empty-crm capstone path, step-2 confirm rejection, admin wire shape, `public_dict` omission/inclusion.

**Gap (non-blocking):** No dedicated test that `confirm_new_entity` on first request (without prior `lookup_suggested`) bypasses fuzzy collision — acceptable; locked behavior is intentional opt-in.

## Design critique

**Strong:** Decision tree in `target_resolve.py` matches the locked spec exactly. Reuses `_rank_suggestions` and registry `lookup_by_name` without duplicating fuzzy logic. `confirm_new_entity` validator rejects step 2 and id-only paths. Admin suggestion click fills employer — good UX for same-name case.

**Sub-optimal (non-blocking):**

- `QueryResponse.required_fields` / `suggestions` field descriptions still reference legacy `entity_key` outcomes — agents reading OpenAPI may miss target-protocol semantics.
- Admin badges use `badge metering` for `lookup_incomplete` / `lookup_suggested` — works visually but semantically odd (not a metering state).

## Nits

| Severity | Item |
|----------|------|
| Non-blocking | Update `QueryResponse` field descriptions for `required_fields` / `suggestions` to mention `lookup_incomplete` / `lookup_suggested` (M10 polish backlog). |
| Non-blocking | Consider distinct admin badge class for negotiation outcomes vs metering. |

## For Paul

**Commit message:**

```
feat: clarify target step-1 lookup with suggestions and confirm_new_entity

Add lookup_incomplete and lookup_suggested outcomes; require confirm_new_entity
for create when same name exists under different employer; omit empty negotiation
fields in public JSON; update onboarding policy.
```

**Breaking change (minor):** Partial lookup with 0 hits → `lookup_incomplete` (was `not_found`). Full MVR same-name collision → `lookup_suggested` (was silent `create_on_deliver`).

**Manual gate:** Updated testing doc at `docs/manual-checks/2026-06-13-program2-post-program-gate.md` — new **Check 0c** for step-1 lookup clarity.

**Push:** Local only until Program 2 gate CLEAR.