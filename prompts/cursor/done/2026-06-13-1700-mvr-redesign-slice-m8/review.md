# Review — MVR redesign Slice M8 (batch deliver + batch provenance)

**Verdict:** **Approved + polish nits**

**Reviewer:** Grok (Paul requested review, June 2026)

---

## CI

| Step | Result |
|------|--------|
| `uv sync --all-extras` | OK |
| `admin-ui` build | OK |
| `ruff` | All checks passed |
| smoke pytest | **342 passed**, 26 deselected (+3 new) |

---

## Delivery

`output.md` matches all changed/new files. Prompt removed from `next/` (staged delete). **`done/`** has `prompt.md` + `output.md`. **Complete delivery.**

---

## Diff reviewed

| File | Read |
|------|------|
| `src/agents/dispatch.py` | Full diff (`_entity_ids_from_state`, `_context_for_entity`, `invoke_specialists_node`, `_attach_provenance` context) |
| `src/agents/responses.py` | Full diff (`_specialist_value_for_attr`, `merge_requested_record`, `_contrib_status_for_attr`) |
| `src/agents/entity_growth.py` | Full diff (entity filter in attribution) |
| `docs/architecture.md` | Batch deliver § |
| `tests/test_mvr_batch_deliver.py` | Full (new) |
| `src/agents/query_provenance.py` | Read (unchanged — already emits `provenance.entities[]`) |
| `src/agents/supervisor.py` | Read (batch `ids[]` in `planner_context` — pre-existing, M8 consumes) |

`/review` subagent not used.

---

## Spec compliance

| Requirement | Status |
|-------------|--------|
| N-entity step-2 deliver returns N `results[]` rows with attrs | Pass |
| Specialists invoked for all N entities (R9) | Pass |
| Batch `provenance.entities[]` when step-1 `provenance=true` | Pass |
| Create-on-deliver remains N=1; documented | Pass |
| No CLI/MCP migration | Pass |
| Smoke green | Pass |

---

## Legacy / dual-path

Single-entity paths unchanged: `_entity_ids_from_state` falls back to `current_id` / single match. Legacy `entity_key` supervisor resolve untouched. Batch fix is isolated to per-entity specialist loop + contribution merge.

---

## Tests

Three new smoke tests cover batch attrs (3 entities), batch provenance shape, and metered batch quote roundtrip. Gaps: batch identity-only step-2 (no attrs); partial batch failure (one entity research fails); `partition_attribute_buckets` accuracy under mixed per-entity statuses.

---

## Design critique

**Strong**

- Nested `entity_ids × specialists` loop in `invoke_specialists_node` is the right seam — supervisor already passes all `ids` in `_meta`; M8 completes the graph side.
- `_context_for_entity` narrows bind per row without duplicating `build_context` specialist storage (still loads all ids in one pass).
- `entity_id` on contributions + filter in `merge_requested_record` and `apply_registry_research_attribution` prevents cross-entity value bleed.
- `_attach_provenance` + existing `build_query_provenance` already produce `entities[]` — no duplicate provenance builder.
- Architecture doc paragraph is accurate and scoped.

**Sub-optimal (non-blocking)**

| # | Issue | Suggestion |
|---|--------|------------|
| N1 | `partition_attribute_buckets` / `build_query_message` call `_contrib_status_for_attr` without `entity_id` | Batch assembled `message` may mis-report attr status when entities differ — scope by entity or aggregate conservatively (M10) |
| N2 | Sequential N×M specialist invocations | Acceptable for smoke scale; note in ops doc or parallelize later if needed |
| N3 | No smoke for batch step-2 without attrs (`found` + N identity rows) | Low risk (unchanged path); optional M10 |
| N4 | `architecture.md` slice header bullets (M4–M6) still omit M7/M8 one-liners | Doc sync in M10 (extends P17) |

---

## Nits

N1–N4 above → backlog **P18–P21** in `mvr-redesign-polish-m10.md`. None blocking.

---

## For Paul

- **Committed locally** by Grok; **not pushed**.
- **M9 queued** — CLI, MCP, admin, example JSON, README migration.

Suggested commit message:

```
feat: batch step-2 deliver and provenance for N entities (MVR redesign M8)

Invoke specialists per entity in multi-match delivery scopes; merge
contributions per row; attach provenance.entities[] for batch deliver.
```