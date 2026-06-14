# Program 3 — Slice 1550: Policy, docs, and program close

## Summary

Scrubbed operator-facing docs and `describe_network` policy of legacy `entity_key` / `binding` negotiation language. Marked Program 3 complete in plan docs. Added Program 3 manual gate checklist.

## `describe_network` policy (`src/network/introspection.py`)

**Removed** from primary `policy` map:

- `entity_unknown`, `entity_bind`, `entity_key_unresolved`, `entity_validated`, `multi_match`

**Added:**

- `registry` — `bind_values` keyed by `mvr.bind_fields`, generic `bind_index`
- `status_inspect` — `--id` / `--lookup-json`, `resolve: { id, lookup }`, exact AND only
- `historical` — one-line pre-2026 protocol removal note

**Kept / expanded:** `_POLICY_MVR_REDESIGN_TARGET`, `entity_growth` (rewritten without `entity_key`)

## Docs updated

| File | Changes |
|------|---------|
| `docs/architecture.md` | `bind_values`, status `resolve` JSON; removed `MYCELIUM_ALLOW_LEGACY_ENTITY_KEY` and legacy graph path |
| `docs/full-code-walkthrough.md` | Target protocol only; `bind_values`; status inspect flags |
| `README.md` | Removed legacy `entity_key` / supervisor legacy path |
| `docs/onboarding.md` | Status inspect examples; `bind_values` in terminology |
| `examples/networks/crm/README.md` | `--lookup-json` instead of `--entity` |
| `docs/manual-checks/2026-06-13-program2-post-program-gate.md` | Superseded note + Program 3 gate link |
| `prompts/system/PROJECT_BRIEF.md` | Public API: `id` / `lookup` / `delivery_id` |
| `docs/plans/entity-protocol-legacy-cleanup-program.md` | **Complete** |
| `docs/plans/README.md` | Program 3 under completed programs |

## New manual gate

`docs/manual-checks/2026-06-14-program3-post-program-gate.md` — **PENDING**

## Tests

- **New:** `test_describe_network_policy_omits_legacy_entity_key_outcomes` in `tests/test_mcp_onboarding.py`

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 401 passed, 26 deselected
```

## For Grok + Paul

- **Program 3 ready for manual gate** — run `docs/manual-checks/2026-06-14-program3-post-program-gate.md`
- Suggest **`program_3` tag** after gate **CLEAR**
- **TODO:** mark Program 3 complete; Program 4 (operator write) next
- **Queue:** slice **1560** polish remains (`prompts/cursor/next/2026-06-14-1560-program3-polish.md`)

Suggested commit message:

```
docs: Program 3 protocol cleanup — bind_values, resolve status, policy hygiene
```

- **Committed** after Grok review (see `review.md`).
