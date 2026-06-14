# Review: 2026-06-14-1430-partial-lookup-fuzzy-name-suggestions

**Verdict: Approved + polish nits**

## CI

| Step | Result |
|------|--------|
| `./bin/ci-local` (Grok, 2026-06-14) | **Pass** — 409 smoke passed, 26 deselected; ruff clean; admin-ui build ok |
| Cursor `output.md` claim | 409 passed — matches |

## Delivery

| Artifact | Present |
|----------|---------|
| Partial 0-hit name fuzzy before `lookup_incomplete` | ✅ |
| `test_partial_fuzzy_name_lookup_suggested` | ✅ |
| Existing partial/full MVR tests unchanged | ✅ (CI) |
| CRM README step-1 note | ✅ |
| `introspection.py` policy line | ✅ |
| `prompt.md` / `output.md` | ✅ |

## Diff reviewed

- `src/agents/target_resolve.py`
- `tests/test_target_step1_lookup_clarity.py`
- `examples/networks/crm/README.md`
- `src/network/introspection.py`
- `prompt.md`, `output.md`

## Spec compliance

| Exit criterion | Pass |
|----------------|------|
| `{"name":"Andrea Kalman"}` partial → `lookup_suggested` | ✅ |
| No fuzzy → still `lookup_incomplete` (`Paul Murphy`) | ✅ (CI) |
| Full MVR fuzzy paths unchanged | ✅ (CI) |
| `./bin/ci-local` green | ✅ |
| Employer fuzzy out of scope | ✅ (`1435` queued) |

## Legacy / dual-path

| Check | Pass |
|-------|------|
| Exact partial name hit → `lookup_resolved` | ✅ (CI) |
| Full MVR `lookup_suggested` / create paths | ✅ (CI) |

## Tests

| Test | Coverage |
|------|----------|
| `test_partial_fuzzy_name_lookup_suggested` | Claude repro — core proof |
| Gap | No test for partial lookup with both `name` + wrong `employer` 0-hit (name fuzzy wins first — OK until `1435`) |

## Design critique

**Strong:** Minimal fix in the right place — reuses `_rank_suggestions` on partial branch before `lookup_incomplete`; fixes MCP/Claude repro without touching full MVR logic. Docs/policy strings updated for `describe_network` consumers.

**Nit (non-blocking):** `name` is still the only bind field with fuzzy on partial 0-hit until `1435`; policy doc [`fuzzy-lookup-policy.md`](../../../docs/plans/fuzzy-lookup-policy.md) tracks generalization. Shorthand aliases (`645` → 645 Ventures) remain `lookup_incomplete` — tracked on TODO.

## Nits

| # | Nit | Severity |
|---|-----|----------|
| N1 | Employer bind-field fuzzy deferred to `1435` | Follow-up slice |
| N2 | Program 2 gate table row not updated in-repo (noted in `output.md`) | Doc — Grok/Paul on gate pass |

## For Paul

**Commit message:**

```
fix(query): suggest fuzzy name matches on partial lookup 0-hit

When partial lookup has no exact index hits but name is near-miss,
return lookup_suggested instead of lookup_incomplete.
```

**Manual test:**

```bash
MYCELIUM_NETWORK=crm uv run mycelium query --network crm \
  --lookup-json '{"name":"Andrea Kalman"}'
# lookup_suggested, Andrea Kalmans in suggestions[]
```

**Next:** Cursor `1435` employer fuzzy (queued). Program 2 gate table: add partial name typo row when you run the gate.

**Git:** Local commit only — no push until you ask.