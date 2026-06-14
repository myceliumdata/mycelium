# Review: 2026-06-14-1410-multi-match-step2-deliver-truncation

**Verdict: Approved + polish nits**

## CI

| Step | Result |
|------|--------|
| `./bin/ci-local` (Grok, 2026-06-14) | **Pass** — 408 smoke passed, 26 deselected; ruff clean; admin-ui build ok |
| Cursor `output.md` claim | 408 passed — matches |

## Delivery

| Artifact | Present |
|----------|---------|
| `response_research_gated` accepts full `matched` list | ✅ |
| `assemble_response_node` passes `matched` not `matched[0]` | ✅ |
| Batch message: N records + M provisional count | ✅ |
| Single-match message avoids “provisional” when validated | ✅ |
| `test_multi_match_research_gate_returns_all_identity_rows` | ✅ |
| M8 batch tests unchanged (CI) | ✅ |
| `prompt.md` / `output.md` | ✅ |

## Diff reviewed

- `src/agents/dispatch.py`
- `src/agents/responses.py`
- `tests/test_mvr_batch_deliver.py`
- `prompt.md`, `output.md`

## Spec compliance

| Exit criterion | Pass |
|----------------|------|
| Research-gated multi-match step-2 returns N identity rows | ✅ |
| Message accurate for mixed validated/provisional batch | ✅ |
| M8 all-validated batch tests still green | ✅ |
| `./bin/ci-local` green | ✅ |
| Gate logic unchanged | ✅ |
| Provisional promotion out of scope (`1400`) | ✅ |

## Legacy / dual-path

| Check | Pass |
|-------|------|
| `test_batch_step2_deliver_with_attrs_researches_all_entities` | ✅ (CI) |
| Single-match `response_research_gated` preserved | ✅ |
| Empty `records` defensive branch | ✅ |

## Tests

| Test | Coverage |
|------|----------|
| `test_multi_match_research_gate_returns_all_identity_rows` | Core proof — `bind_provisional(..., "A")` stays provisional post-`1400`; 2 results; batch message |
| Gap | No explicit single-match gated message regression test (low risk; branch preserved in code) |

## Design critique

**Strong:** Minimal, correct fix — one call-site change plus `response_research_gated` generalized to M8 batch shape via identity row list comprehension. Test fixture adapts sensibly to post-`1400` reality (Wrong Corp would promote; employer `"A"` fails validation and keeps gate active). Batch message no longer mislabels validated `matched[0]` as provisional.

**Nit (non-blocking):** Batch message still appends generic `RESEARCH_GATE_MESSAGE` (“Record is provisionally bound…”) after the accurate “N records / M provisional” summary — slightly redundant for mixed batches. `debug.registry_id` still only references `matched[0]`.

## Nits

| # | Nit | Severity |
|---|-----|----------|
| N1 | Batch gated message + generic `RESEARCH_GATE_MESSAGE` overlap | Polish |
| N2 | `debug.registry_id` only first match in batch gate | Polish |

## For Paul

**Commit message:**

```
fix(query): return all matches when step-2 research gate blocks attrs

Multi-match deliver no longer truncates to matched[0]; fix gated
message for mixed validated/provisional batches.
```

**Manual test (1410 — not validation):**

Wrong Corp **provisional with valid employer** will **promote on step 2** (`1400`) and the research gate will **not** fire — you will get `assembled`, not the gated `found` path. To hit the **truncation fix**, you need a row that **stays provisional** after validation (employer `"A"` fails MVR).

**Setup (once):**

```bash
MYCELIUM_NETWORK=crm uv run mycelium query --network crm \
  --lookup-json '{"name":"Andrea Kalmans","employer":"A"}' \
  --confirm-new-entity

MYCELIUM_NETWORK=crm uv run mycelium query --network crm \
  --delivery-id d_PASTE_FROM_STEP1
```

Confirm Andrea @ `A` exists and is `provisional` in `entities.json`. Keep Wrong Corp demoted too if you like, but **`A` is the row that keeps the gate open**.

**Test:**

```bash
MYCELIUM_NETWORK=crm uv run mycelium query --network crm \
  --lookup-json '{"name":"Andrea Kalmans"}' --attributes email

MYCELIUM_NETWORK=crm uv run mycelium query --network crm \
  --delivery-id d_PASTE_HERE
```

**Pass:** `outcome: found`, `len(results) == 2` (or 3 if Wrong Corp + Lontra + A), message mentions `"2 records"` / provisional count, **no** `"provisional record for"` when Lontra is validated.

**Git:** Local commit only — no push until you ask.

**Next:** Program 2 manual gate when ready (`docs/manual-checks/2026-06-13-program2-post-program-gate.md`).