# Review — MVR redesign Slice M7 (create-on-0 + retire name_source)

**Verdict:** **Approved + polish nits**

**Reviewer:** Grok (Paul requested review, June 2026)

---

## CI

| Step | Result |
|------|--------|
| `uv sync --all-extras` | OK |
| `admin-ui` build | OK |
| `ruff` | All checks passed |
| smoke pytest | **339 passed**, 26 deselected (+4 new) |

---

## Delivery

`output.md` matches all changed/new files. Prompt removed from `next/` (staged delete). **`done/`** has `prompt.md` + `output.md`. **Complete delivery.**

---

## Diff reviewed

| File | Read |
|------|------|
| `src/network/mvr.py` | Full diff |
| `src/network/delivery.py` | Full diff |
| `src/agents/target_resolve.py` | Full |
| `src/agents/target_deliver.py` | Full diff |
| `src/agents/dispatch.py` | Full diff (`target_resolve_node`, assemble) |
| `src/agents/target_metering.py` | Hunk |
| `src/network/quotes.py` | Full diff |
| `src/agents/responses.py` | `build_query_message` / `response_assembled` hunks |
| `src/models/state.py` | Hunk |
| `examples/networks/*/network.json` | All three |
| `docs/architecture.md` | Create-flow § |
| `tests/test_mvr_create_on_deliver.py` | Full (new) |
| Test cleanups | `test_entity_unknown_mvr`, `test_research`, `test_query_*`, `test_core_graph`, `test_network_integration` |

`/review` subagent not used.

---

## Spec compliance

| Requirement | Status |
|-------------|--------|
| Partial lookup, 0 matches → `not_found` | Pass |
| Full MVR, 0 matches, no attrs → `not_found` | Pass |
| Full MVR, 0 matches, attrs → step-1 `lookup_resolved` (`total_matches=0`) + `create_on_deliver` scope | Pass |
| Step-2 → `bind_provisional` + `assembled` + research | Pass |
| `name_source` removed from policy + examples | Pass — ignored if present in JSON |
| Legacy `entity_key` path unchanged | Pass — no graph change to supervisor resolve |
| No batch provenance (M8) / CLI migration (M9) | Pass |

---

## Legacy / dual-path

Target create-on-deliver is isolated in `target_resolve` / `target_deliver`. Legacy `entity_key` + `entity_resolution` + `name` from `entity_key` in `required_fields_for_binding` still work for CLI until M9.

---

## Tests

Four new smoke tests cover the create matrix and `name_source` ignore. Gaps: metered create-on-deliver (step-1 `quote_required` with `total_matches=0`); explicit legacy `entity_key` bind regression in this file.

---

## Design critique

**Strong**

- `create_on_deliver` on `DeliveryScope` is the right seam — step-1 issues token without binding; bind deferred to step-2 (matches program R10).
- `can_create_on_zero_matches` centralizes the full-MVR + attrs gate.
- `hydrate_matches_for_deliver` keeps step-2 node logic readable; `entity_resolution_kind=bind_provisional` reuses existing validation/specialist path.
- `response_assembled` / `build_query_message` accept delivery-scope attrs — fixes step-2 empty-attrs bug without polluting public `EntityQuery`.
- Quote batch count = 1 for create-pending scopes is correct.

**Sub-optimal (non-blocking)**

| # | Issue | Suggestion |
|---|--------|------------|
| N1 | `bind_provisional_from_scope` hard-codes `name` / `employer` | Generalize from `mvr.bind_fields` when networks add fields (M8/M10) |
| N2 | `is_full_mvr_lookup` checks key presence only via `normalized_lookup_values` | OK today; document that empty values fail via normalization |
| N3 | Metered create path untested | Add smoke on `crm-metering` fixture in M8 or M10 |
| N4 | `architecture.md` slice bullets (M3–M6) omit M7 line in header block | Add one-liner for consistency (polish) |

---

## Nits

N1–N4 above. None blocking.

---

## For Paul

- **Committed locally** by Grok; **not pushed**.
- **M8 unblocked** — batch deliver + `provenance.entities[]` shape.

Suggested commit message:

```
feat: create-on-deliver for full MVR zero-match lookups (MVR redesign M7)

Step-1 issues create_on_deliver delivery scope; step-2 bind_provisional;
remove name_source from MVR policy and example networks.
```