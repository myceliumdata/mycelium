# Baseball partial player lookup — CRM parity on multi-grain routing

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting).

**Priority:** Small routing fix after slice 1100 strict grain routing. Unblocks name-only player resolve (e.g. Ty Cobb) without changing entity stores or bootstrap.

**Parent:** [`docs/plans/baseball-example-program.md`](../../docs/plans/baseball-example-program.md); [`docs/query-grain-router.md`](../../docs/query-grain-router.md).

**Principles:**

- **Reuse existing resolver** — `_resolve_single_grain_step1` already implements partial field-index resolve, fuzzy suggest, and `lookup_incomplete` fallback (CRM behavior). Do **not** duplicate logic in `infer_grain_from_lookup`.
- **Framework generic** — no baseball/Lahman strings in `src/`. Fix applies to any multi-grain network with partial bind subsets.
- **CRM unchanged** — single-grain path (`len(config.grains) == 1`) must behave identically.
- **Closed grains** — baseball player grain stays `closed`; partial 0-hit must **not** offer `create_pending`.

---

## Problem

CRM allows partial `{"name": "…"}` lookups because single-grain networks call `_resolve_single_grain_step1` directly.

Baseball multi-grain routing stops early: when `infer_grain_from_lookup` returns `lookup_incomplete` (e.g. `{player}` missing `team`), `resolve_target_step1` **returns incomplete immediately** without trying the field index.

```python
# src/agents/target_resolve.py — today (~354–361)
if inference.kind == "lookup_incomplete":
    return TargetResolveResult(kind="lookup_incomplete", ...)
```

Slice 1100 locked this; Paul + Grok now want **CRM parity**: partial player lookup should try resolve first, same code path.

---

## Locked behavior (do not reinterpret)

### Grain inference (unchanged)

- `{player, team}` → player grain (exact match).
- `{team}` → team grain (exact match).
- `{player}` only → inference still reports **partial** player grain + missing `team` (for docs/diagnostics). **Do not** change `infer_grain_from_lookup` to treat partial as exact grain match unless you also update its docstring/tests consistently — preferred fix is below.

### Resolve (new)

When multi-grain step-1 lookup yields `inference.kind == "lookup_incomplete"` **and** `inference.grain` is set (unambiguous partial subset of exactly one grain):

1. **Delegate** to `_resolve_single_grain_step1(query, grain=inference.grain, alias_expander=…)` instead of returning incomplete immediately.
2. Let existing logic decide outcome:

| Case | Outcome |
|------|---------|
| Field index hit (1+ entity ids) | `lookup_resolved` (`total_matches` = hit count) |
| 0 hits, fuzzy near-miss on provided bind field(s) | `lookup_suggested` (`_rank_bind_field_fuzzy_suggestions` — works for `player` generically) |
| 0 hits, no fuzzy | `lookup_incomplete` + `required_fields` (e.g. `["team"]`) |
| Closed grain, 0 hits after alias expansion | `not_found` / `lookup_suggested` per slice 2000 — **never** `create_pending` |

### Preserve

- `{team}` only → team grain exact path (unchanged).
- Unknown keys (e.g. `{name}` on baseball) → `not_found` (unchanged).
- `inference.kind == "ambiguous"` → still terminal `lookup_incomplete` with empty `required_fields` (unchanged).
- Full `{player, team}` + `bind_index` alias fallback (slice 1000) — unchanged.
- `id`-only step 1 — unchanged.

### Examples (document in router doc)

| Lookup | Step-1 outcome (typical) |
|--------|--------------------------|
| `{"player": "Ty Cobb"}` — unique, in registry | `lookup_resolved`, `total_matches: 1` |
| `{"player": "John Smith"}` — homonyms | `lookup_resolved`, `total_matches: N` (same as CRM `645 Ventures`) |
| `{"player": "Nobody"}` — 0 hits | `lookup_incomplete`, `required_fields: ["team"]` |
| `{"player": "Hank Aarn"}` — typo | `lookup_suggested` if fuzzy ranks a hit |
| `{"player": "Hank Aaron"}` — in registry | `lookup_resolved` (1 uuid; primary bind indexed) |

**Note:** Partial lookup uses **field index** on primary `bind_values` only — not `bind_index` team aliases. That is correct: one index entry per player name per uuid.

---

## Implement

### A. `resolve_target_step1` (primary change)

In [`src/agents/target_resolve.py`](../../src/agents/target_resolve.py), multi-grain branch:

Replace terminal return on `inference.kind == "lookup_incomplete"` when `inference.grain` is non-empty with delegation to `_resolve_single_grain_step1`.

Keep terminal incomplete only when `inference.grain` is `None` (defensive).

### B. Tests (smoke — mandatory)

Update [`tests/test_strict_grain_routing.py`](../../tests/test_strict_grain_routing.py):

| Test | Change |
|------|--------|
| `test_player_only_lookup_incomplete` | Use a player name **not** in registry (e.g. `"Nobody Here"`) → still `lookup_incomplete`, `team` in `required_fields` |
| **New:** `test_player_only_lookup_resolved_unique` | `{"player": "Washington"}` (fixture row) → `resolved`, `entity_ids == ["player-wash"]`, `grain == "player"` |
| **New:** `test_player_only_homonym_multi_match` (optional if easy) | Two player rows same `player` string, different teams → `resolved`, `total_matches == 2` via `run_query` or `resolve_target_step1` |

Add one integration test in [`tests/test_target_step1_lookup_clarity.py`](../../tests/test_target_step1_lookup_clarity.py) **or** strict grain file proving CRM single-grain tests still pass (run full file — no regressions).

Run `./bin/ci-local` and `./bin/smoke-baseball-e2e`.

### C. Docs (mandatory)

1. [`docs/query-grain-router.md`](../../docs/query-grain-router.md) — update baseball contract table row for `{player}` only: try partial resolve on player grain (CRM parity), not immediate incomplete.
2. [`docs/manual-checks/2026-06-18-baseball-query-hand-test-plan.md`](../../docs/manual-checks/2026-06-18-baseball-query-hand-test-plan.md):
   - Revise Q05 expectations (split: unknown name → incomplete; known unique name → resolved — add **Q17** Ty Cobb / Washington-style case).
   - Update matrix **G**.
3. [`examples/networks/baseball/guide.md`](../../examples/networks/baseball/guide.md) — one sentence: `{player}` alone resolves when name hits registry; homonyms return multiple matches; unknown names ask for `team`.

### D. `bin/baseball-query` / MCP

No code changes expected — same JSON payloads.

---

## Out of scope

- Changing `infer_grain_from_lookup` semantics beyond doc alignment (optional).
- `bind_index` fallback for partial lookups (only full MVR today — keep).
- Specialist / `requested_attributes` assembly (“what can you tell me about Ty Cobb?”).
- Re-bootstrap or entity store migration.
- `EntityQuery.grain` revival.

---

## Entity store — no refresh required

Paul's freshly bootstrapped root (post-1100 `player`/`team` keys) is **fine**. This slice only changes step-1 routing in memory. Field indexes are rebuilt on registry load from existing `bind_values`. **No** warehouse re-import, **no** `refresh-example-network` unless the root still has pre-1100 `{name, team}` data.

After slice lands: `uv sync`, run hand tests on existing `$ROOT` — e.g. `{"lookup": {"player": "Hank Aaron"}}` should `lookup_resolved` to Aaron's uuid without team.

---

## Verification

```bash
./bin/ci-local
./bin/smoke-baseball-e2e
./bin/smoke-crm-e2e

# Manual (existing benchmark root — no refresh)
export ROOT="${ROOT:-/tmp/mycelium-baseball-benchmark}"
export MYCELIUM_NETWORK_ROOT="$ROOT"
./bin/baseball-query '{"lookup": {"player": "Hank Aaron"}}' | jq '{outcome, total_matches, delivery_id: .delivery.delivery_id}'
# Expect: lookup_resolved, total_matches: 1

./bin/baseball-query '{"lookup": {"player": "Nobody Here"}}' | jq '{outcome, required_fields}'
# Expect: lookup_incomplete, required_fields includes "team"
```

---

## Deliverables

Per `prompts/cursor/WORKFLOW.md`:

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-18-1200-baseball-partial-player-lookup/` with `prompt.md` + `output.md`
3. **Do not commit** — Grok reviews and commits
4. `output.md` **For Grok + Paul:** note router contract change; hand test plan Q05/Q17; HOLD.md queue entry

**Suggested commit message:**

```
fix: delegate partial multi-grain lookups to single-grain resolver (CRM parity)

{player}-only baseball lookups now hit the field index before
lookup_incomplete, matching CRM partial name behavior.
```
