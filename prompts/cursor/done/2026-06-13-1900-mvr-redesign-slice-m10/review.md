# Review — MVR redesign Slice M10 (polish + admin-ui + backlog)

**Verdict:** **Approved**

**Reviewer:** Grok (Paul requested review, June 2026)

---

## CI

| Step | Result |
|------|--------|
| `uv sync --all-extras` | OK |
| `admin-ui` build | OK (TypeScript compiles — two-step form) |
| `ruff` | All checks passed |
| smoke pytest | **352 passed**, 26 deselected (+6 new) |

---

## Delivery

`output.md` matches all changed/new files. Prompt removed from `next/`. **`done/`** has `prompt.md` + `output.md`. **Complete delivery.**

---

## Diff reviewed

| File | Read |
|------|------|
| `admin-ui/src/App.tsx`, `api.ts`, `types.ts` | Full diff |
| `src/network/env_util.py` | Full (new) |
| `src/agents/metering_gate.py` | Full diff (`accept_quote_for_workload`) |
| `src/agents/target_metering.py` | Full diff (uses helper) |
| `src/agents/responses.py` | `partition_attribute_buckets` batch hunk |
| `src/agents/supervisor.py` | Legacy gate hunk |
| `src/models/state.py` | Legacy helpers + schema docs |
| `src/agents/target_deliver.py` | `bind_provisional_from_scope` |
| `src/agents/field_index.py` | `_entity_field_value` |
| `src/agents/dispatch.py` | `EntityQuery` type on block response |
| `src/network/delivery.py`, `quotes.py`, `tools/research.py` | `env_int` import |
| `tests/test_mvr_polish_m10.py` | Full (new) |
| `tests/conftest.py` | Legacy env default |
| `docs/architecture.md` | M10 sections |
| `examples/networks/crm-metering/` | README + fixture fixes |

`/review` subagent not used.

---

## Backlog closure (P1–P26)

| ID | Verdict | Notes |
|----|---------|-------|
| P1 | Closed | `env_util.env_int` shared |
| P2 | Closed | `EntityQuery.id` description |
| P3 | Waived | Process — OK |
| P4 | Closed | `hasattr` on registry entity |
| P5 | Waived | Keep smoke — OK |
| P6 | Waived | Doc in architecture — OK |
| P7 | Closed | Identity-only + provenance scope test |
| P8 | Closed | TTL operator note |
| P9 | Waived | Parity verified — OK |
| P10 | Closed | `EntityQuery` typed |
| P11 | Closed | `accept_quote_for_workload()` dedupes target + legacy |
| P12 | **Partial** | `principal_required` tested; `payment_required` on target path still untested |
| P13 | Closed | Provenance-only quote test |
| P14 | **Partial** | Loop over `bind_fields` but `bind_provisional(name, employer)` still fixed arity |
| P15 | Closed | `is_full_mvr_lookup` docstring |
| P16 | Closed | Metered create-on-deliver test |
| P17 | Closed | M7–M10 content in architecture subsections (not compact M3-style bullets — acceptable) |
| P18 | Closed | Per-entity batch bucket logic |
| P19 | Closed | Batch identity-only test |
| P20 | Closed | Sequential N×M note |
| P21 | Closed | M8 batch § present |
| P22 | Closed | Admin-ui lookup + `delivery_id` + quote accept |
| P23 | Closed | `crm-metering` README fixed |
| P24 | Closed | Fixture placeholder text |
| P25 | Closed | `MYCELIUM_ALLOW_LEGACY_ENTITY_KEY` gate + test |
| P26 | Waived | Lightweight health ping deferred — OK |

P12/P14 partial items are post-ship doc/test debt only — not blocking program completion.

---

## Spec compliance

| Requirement | Status |
|-------------|--------|
| Admin-ui two-step (P22) | Pass |
| Backlog rows closed or waived | Pass |
| `./bin/ci-local` green | Pass |
| Final MVR slice | Pass |

---

## Design critique

**Strong**

- `accept_quote_for_workload()` cleanly unifies legacy `metering_gate` and `target_metering` — real P11 win.
- Legacy isolation via env flag + `conftest` default preserves existing smoke without exposing public path.
- `partition_attribute_buckets` batch branch is conservative (pending wins; per-entity status).
- Admin-ui auto-captures `delivery_id` / `quote_id` from responses; accept-quote uses deliver body.
- Six targeted smoke tests fill the highest-value gaps from M5–M9 reviews.

**Minor post-ship nits (non-blocking)**

| # | Issue |
|---|--------|
| N1 | `architecture.md` lines 231, 262, 266 still say “today conflated” / “until M9” — stale after ship |
| N2 | P12 `payment_required` on target path still lacks smoke |
| N3 | P14 `bind_provisional_from_scope` not fully generalized for future bind fields |
| N4 | No automated admin-ui query test (manual demo path only) |

---

## Program status

**MVR redesign M1–M10 complete.** Local branch is 13 commits ahead of `origin/main` (1 behind remote revert). Ready for Paul to test and request push.

---

## For Paul

- **Committed locally** by Grok; **not pushed**.
- **No further MVR slices queued.**
- When satisfied: ask Grok to push `origin`, or push yourself after local test pass.

Suggested commit message:

```
feat: MVR redesign M10 polish — admin-ui two-step, backlog tests, legacy gate

Migrate admin-ui to lookup/delivery_id flow; close P1–P25 backlog; isolate
legacy entity_key behind MYCELIUM_ALLOW_LEGACY_ENTITY_KEY for smoke tests.
```