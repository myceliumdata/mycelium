# Fix provisional validation on step-2 deliver (Q5a)

> **READY** — Move to `in-progress/` before starting (see `prompts/cursor/WORKFLOW.md`).

**Context (Paul + Grok, June 2026):** Phase 5 Q5a locks: **validate on every query** when a registry row is `provisional` and MVR is satisfied — **including identity-only** step-2 deliver. Flow: `bind → validate → research (if attrs)`.

**Observed:** Andrea @ Wrong Corp (`confirm_new_entity` / create-on-deliver) stays `validation_state: provisional` indefinitely. Local repro:

- Identity-only step-2 create-on-deliver → `provisional` after step 2 (should be `validated`).
- Name-only lookup, 2 Andreas + attrs → Wrong Corp stays `provisional` (`validate_entity` skipped when `len(matched) > 1`).
- Control: single-match full MVR `name` + `employer` Wrong Corp + attrs → promotes to `validated`.

**Intentional exception (do not break):** Q5b — validation **failure** (e.g. employer `"A"`) → stay `provisional`, `found` + failure message.

**Prerequisite:** `main` with admin 1300–1305 + polish commits.

**Out of scope for this slice:** Multi-match step-2 returning only 1 row when research gate fires — slice `1410` (queue after this).

---

## Read first

- [`docs/plans/entity-validation-phase5.md`](../../docs/plans/entity-validation-phase5.md) — Q5a–Q5d
- [`src/agents/dispatch.py`](../../src/agents/dispatch.py) — `target_resolve_node` (step-2 short-circuit), `validate_entity_node`, `assemble_response_node`
- [`src/graphs/core.py`](../../src/graphs/core.py) — `_route_after_target_resolve`
- [`src/agents/target_deliver.py`](../../src/agents/target_deliver.py) — `hydrate_matches_for_deliver`, `bind_provisional_from_scope`
- [`tests/test_mvr_create_on_deliver.py`](../../tests/test_mvr_create_on_deliver.py) — extend `test_full_mvr_zero_matches_without_attrs_create_on_deliver`
- [`tests/test_entity_validation.py`](../../tests/test_entity_validation.py) — failure path must still pass

---

## Required fixes

### A. Step-2 identity-only deliver must run validation

Today step-2 deliver **without** `requested_attributes` presets `response` in `target_resolve_node` and routes straight to `assemble_response` — **`validate_entity` never runs**.

**Fix:** When step-2 deliver loads match row(s) and any registry row is `provisional`, **do not** preset final `response` in `target_resolve_node`. Route through `supervisor` → `validate_entity` → `assemble_response` (same graph as attrs path). Identity-only outcome remains `found` with N identity rows (preserve `test_batch_step2_identity_only_found` behavior for all-validated batches).

Create-on-deliver step 2 (no attrs on scope) must promote valid MVR rows to `validated`.

### B. Multi-match step-2 must validate each provisional row

Today `validate_entity_node` returns early when `len(matched) != 1`.

**Fix:** For each match where `is_provisional_registry_match(rec)`, run `run_mvr_validation` on that registry row and `promote_validated` when all fields pass. Update `matched_records` in state with promoted match dicts. Already-validated rows unchanged.

If **any** provisional in batch fails validation, apply Q5b for that row (do not promote); batch outcome policy: document in `output.md` if you return `found` + failure for whole batch vs per-row — prefer **not** blocking promotion of other rows that pass.

### C. Docs alignment

Update [`examples/networks/crm/README.md`](../../examples/networks/crm/README.md) step-2 bullet if implementation detail changed (validation on identity-only deliver).

---

## Tests (smoke — mandatory)

| Test | Assert |
|------|--------|
| Extend `test_full_mvr_zero_matches_without_attrs_create_on_deliver` | After step-2 identity-only create, `entities.json` row is `validation_state: validated` |
| New: `test_multi_match_step2_promotes_provisional_bind` | Seed CRM + `bind_provisional("Andrea Kalmans", "Wrong Corp")`; step1 `lookup: {name}` + `email`; step2 deliver; Wrong Corp row is `validated` |
| Existing `test_absurd_employer_fails_validation_stays_provisional` | Still passes |
| Existing `test_batch_step2_identity_only_found` | Still passes (3 rows, all seed-validated) |

Repro recipe (for `output.md` manual section):

```python
# After seed import: reg.bind_provisional("Andrea Kalmans", "Wrong Corp")
# step1 EntityQuery(lookup={"name":"Andrea Kalmans"}, requested_attributes=["email"])
# step2 EntityQuery(delivery_id=...)
# assert Wrong Corp validation_state == "validated"
```

---

## Verification

```bash
./bin/ci-local
```

**Paul manual (after Grok review + commit):**

```bash
./bin/restart-admin crm   # optional — admin not required for this slice
```

1. On live CRM (or fresh seed + bind): confirm Andrea @ Wrong Corp is `provisional` in `entities.json` **or** create via `confirm_new_entity` + step-2 identity deliver.
2. Re-run step-2 with full MVR single-match OR repeat create path after fix.
3. Confirm `validation_state: validated` for Wrong Corp; `network status` / MCP no longer reports research gate for that row alone.

---

## Governance

- Do not edit `TODO.md`.
- In `output.md` → **For Grok + Paul**: validation fix done; manual steps; note slice `1410` still queued for truncation.
- Do not commit or push.

## When finished

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-14-1400-provisional-validation-step2-deliver/`
3. Remove from `in-progress/` and `next/`
4. Tell Paul **slice ready for review** — Paul + Grok test validation before `1410`

---

## Exit criteria

- Identity-only step-2 create-on-deliver promotes valid MVR to `validated`
- Multi-match step-2 promotes each valid provisional row (Wrong Corp repro)
- Q5b failure path unchanged
- `./bin/ci-local` green

Suggested commit message:

```
fix(query): run validate_entity on step-2 deliver for provisional rows

Route identity-only deliver through validation; validate each provisional
match in multi-match scopes (Q5a). Identity-only create-on-deliver promotes.
```