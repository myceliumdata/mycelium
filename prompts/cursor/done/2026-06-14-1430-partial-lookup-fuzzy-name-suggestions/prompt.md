# Partial name lookup: fuzzy suggestions before lookup_incomplete

> **READY** — Move to `in-progress/` before starting (see `prompts/cursor/WORKFLOW.md`).

**Context (Paul + Grok, June 2026):** MCP/Claude sent `{"lookup": {"name": "Andrea Kalman"}}` (typo). Mycelium returned `lookup_incomplete` + `required_fields: ["employer"]`. User expected `lookup_suggested` with `Andrea Kalmans` (`sequence_ratio`) — same as full MVR fuzzy path.

**Today:** Fuzzy `_rank_suggestions` runs only when **full MVR** lookup has 0 exact index hits (`resolve_target_step1` returns `lookup_incomplete` immediately for partial lookups). Partial name-only 0-hit goes straight to `lookup_incomplete` even when near-miss names exist.

**Repro:**

```bash
MYCELIUM_NETWORK=crm uv run mycelium query --network crm \
  --lookup-json '{"name":"Andrea Kalman"}'
# Today: lookup_incomplete
# Want: lookup_suggested → suggestions[].name == "Andrea Kalmans"
```

**Prerequisite:** `main` with slices 1400–1420 approved.

---

## Read first

- [`src/agents/target_resolve.py`](../../src/agents/target_resolve.py) — `resolve_target_step1` partial vs full MVR branch (~lines 91–108)
- [`src/agents/entity_resolution.py`](../../src/agents/entity_resolution.py) — `_rank_suggestions`, `SUGGESTION_MIN_SCORE`
- [`tests/test_target_step1_lookup_clarity.py`](../../tests/test_target_step1_lookup_clarity.py) — `test_fuzzy_name_lookup_suggested` (full MVR), `test_partial_lookup_missing_employer_lookup_incomplete`
- [`docs/manual-checks/2026-06-13-program2-post-program-gate.md`](../../docs/manual-checks/2026-06-13-program2-post-program-gate.md) — step-1 outcomes table (Grok updates after review; note in `output.md`)

---

## Required fix

### A. Partial lookup 0-hit: try fuzzy name suggestions first

In `resolve_target_step1`, when `lookup_by_target_lookup` returns **empty** and `not is_full_mvr_lookup(...)`:

1. If normalized lookup includes a non-empty **`name`** value, call `_rank_suggestions(name)` (reuse existing helper from `entity_resolution` — do not duplicate fuzzy logic).
2. If suggestions non-empty → return `TargetResolveResult(kind="lookup_suggested", suggestions=...)`.
3. Else → existing `lookup_incomplete` with `missing_mvr_bind_fields` (unchanged).

**Do not** fuzzy-match on partial **employer-only** lookups in this slice (no employer typo spec). Name-only and any partial lookup that includes `name` with 0 AND hits should get the name fuzzy pass.

### B. Preserve existing outcomes

| Case | Outcome |
|------|---------|
| `{"name":"Andrea Kalmans"}` partial, ≥1 hit | `lookup_resolved` (unchanged) |
| `{"name":"Paul Murphy"}` partial, 0 hits, no fuzzy | `lookup_incomplete` (unchanged) |
| Full MVR `{"name":"Andrea Kalman","employer":"Acme Corp"}` 0 hits | `lookup_suggested` (unchanged) |
| Full MVR same-name different employer | `lookup_suggested` `same_name_different_employer` (unchanged) |

### C. Tests (smoke — mandatory)

Add to [`tests/test_target_step1_lookup_clarity.py`](../../tests/test_target_step1_lookup_clarity.py):

| Test | Assert |
|------|--------|
| **New:** `test_partial_fuzzy_name_lookup_suggested` | `lookup={"name":"Andrea Kalman"}` → `lookup_suggested`, `suggestions[0].entity_key == "Andrea Kalmans"`, `reason == "sequence_ratio"`, no `delivery` |
| Existing `test_partial_lookup_missing_employer_lookup_incomplete` | Still passes (`Paul Murphy`) |
| Existing `test_partial_lookup_name_hit_lookup_resolved` | Still passes |
| Existing `test_fuzzy_name_lookup_suggested` | Still passes (full MVR path) |

### D. Docs (brief)

Update step-1 outcome bullet in [`examples/networks/crm/README.md`](../../examples/networks/crm/README.md) if it lists partial 0-hit → only `lookup_incomplete`; add row for partial name typo → `lookup_suggested`.

Optional one-line note in [`src/network/introspection.py`](../../src/network/introspection.py) `_POLICY_MVR_REDESIGN_TARGET` if easy — partial name 0-hit may return suggestions.

---

## Out of scope

- Fuzzy employer-only partial lookups
- Lowering `SUGGESTION_MIN_SCORE`
- MCP / admin UI changes
- Changing full MVR suggestion logic

---

## Verification

```bash
./bin/ci-local
```

**Paul manual (after Grok review):**

```bash
MYCELIUM_NETWORK=crm uv run mycelium query --network crm \
  --lookup-json '{"name":"Andrea Kalman"}'
# lookup_suggested, suggestions include Andrea Kalmans
```

---

## Governance

- Do not edit `TODO.md`.
- In `output.md` → **For Grok + Paul**: note Program 2 gate table row update for partial fuzzy name.
- Do not commit or push.

## When finished

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-14-1430-partial-lookup-fuzzy-name-suggestions/`
3. Remove from `in-progress/` and `next/`
4. Tell Paul **slice ready for review**

---

## Exit criteria

- `{"name":"Andrea Kalman"}` partial → `lookup_suggested` (Paul/Claude repro)
- No fuzzy → still `lookup_incomplete`
- Full MVR fuzzy/suggested paths unchanged
- `./bin/ci-local` green

Suggested commit message:

```
fix(query): suggest fuzzy name matches on partial lookup 0-hit

When partial lookup has no exact index hits but name is near-miss,
return lookup_suggested instead of lookup_incomplete.
```