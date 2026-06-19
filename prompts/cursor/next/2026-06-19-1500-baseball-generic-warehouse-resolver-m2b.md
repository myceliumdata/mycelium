# Baseball generic warehouse resolver (M2b)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md`. **Depends on M2a** (`2026-06-19-1400-baseball-warehouse-manifest-m2a`) merged or present in tree.

**Priority:** Layer 3 execution — one manifest-driven code path for career counting stats and raw People columns, without per-attr `if key == "career_hr"` branches.

**Parent:** [`docs/plans/conversations/2026-06-19-warehouse-factory-layer3-specialist-emergence.md`](../../docs/plans/conversations/2026-06-19-warehouse-factory-layer3-specialist-emergence.md)

**Principles:**

- **Reuse M1 framework** — `write_computed_field`, `write_na_field`, `inspect.getsource` for provenance inline, dataset pin from manifest.
- **Manifest is source of truth** for domain tables, conventions, aliases — read `warehouse_manifest.json` (M2a).
- **Behavior:** `career_hr==3` on minimal fixture unchanged; full Lahman Aaron `career_hr==755`, `birth_date==1934-02-05`.
- **No web research** on batting/bio warehouse paths.
- **Do not edit `TODO.md`.**

---

## Objective

Replace hardcoded per-attr branches in pack `batting_specialist.py` and `bio_specialist.py` with a **generic resolver** driven by manifest conventions:

| Request | Resolution |
|---------|------------|
| `career_hr`, `career_rbi`, `career_hits` | `career_sum` on `Batting` column (`HR`, `RBI`, `H`) |
| `birth_date` | Raw People compose (existing logic, wired via manifest) |
| `debut`, `bats`, `throws`, `birth_city`, … | Raw People column map when column exists |
| Unknown / rate stats (`career_avg`, `ops`) | `N/A` for M2b (recipes deferred) |

---

## Locked conventions (v1)

### Batting `career_sum`

Attr name → column:

| Attribute | Column |
|-----------|--------|
| `career_hr` | `HR` |
| `career_rbi` | `RBI` |
| `career_hits` | `H` |

SQL pattern (player grain, all stints):

```sql
SELECT COALESCE(SUM(CAST("{col}" AS INTEGER)), 0)
FROM "Batting" WHERE "playerID" = ?
```

Provenance: single Python function per convention; `inspect.getsource` for inline.

### Bio raw column

Manifest lists `People` columns. Map attrs:

| Attribute | People column(s) |
|-----------|------------------|
| `birth_date` | `birthYear`, `birthMonth`, `birthDay` → `YYYY-MM-DD` |
| `debut` | `debut` (pass through or normalize ISO date if present) |
| `bats` | `bats` |
| `throws` | `throws` |
| `birth_city` | `birthCity` |

Missing column or null parts → `write_na_field`.

### Parameters (provenance)

Include **all** runtime values:

```json
{
  "lahman.playerID": "aaronha01",
  "warehouse": "warehouse/lahman.sqlite"
}
```

---

## Implement

### 1 — Shared pack helper (optional)

**File:** `examples/networks/baseball/specialists/lahman_common.py` (extend) or `warehouse_resolve.py` in pack:

- `load_warehouse_manifest(paths) -> dict`
- `resolve_career_sum(attr, player_id, warehouse) -> int`
- `resolve_people_field(attr, player_id, warehouse) -> str | None`

Keep Lahman logic **pack-only**.

### 2 — Refactor `batting_specialist.py`

- Loop owned fields; for each, consult manifest + alias table.
- `career_*` counting stats → `career_sum` convention.
- Cache / provenance unchanged envelope.
- Remove per-attr `if key == "career_hr"` only branches replaced by generic path.

### 3 — Refactor `bio_specialist.py`

- Same pattern for People raw fields.
- `birth_date` stays `1934-02-05` on fixture.

### 4 — Manifest aliases (pack)

In `warehouse_domains.json` or manifest `aliases`:

```json
"aliases": {
  "career_hr": {"convention": "career_sum", "column": "HR"}
}
```

### 5 — Tests

Extend `tests/test_baseball_batting_specialist.py`:

- `career_rbi`, `career_hits` deliver on minimal fixture (compute expected from fixture `Batting.csv`)
- Provenance: `parameters.warehouse` present; inline contains `SUM`

Extend `tests/test_baseball_bio_specialist.py` if adding `bats`/`debut` — optional one raw column smoke.

Regression: existing M1b/M1c tests green.

### 6 — Smoke

`bin/smoke-baseball-e2e`: optional scenario for `career_rbi` on fixture, or extend batting scenario asserts.

---

## Non-goals

- `career_avg`, OPS, rate recipes (M2b+)
- LLM codegen / derive API (M3)
- `player_identity` bind-field fix (M2c)
- Franchise / cross-domain specialists
- `TODO.md` edits

---

## Verification

```bash
./bin/ci-local
uv run pytest tests/test_baseball_batting_specialist.py tests/test_baseball_bio_specialist.py -q
./bin/smoke-baseball-e2e
```

---

## For Grok + Paul (output.md)

- M2b done; queue **M2c** (bind fields + any remaining provenance gaps).
- Note fixture expected values for new career stats.

**Suggested commit message:**

```
baseball: manifest-driven warehouse resolver for career stats (M2b)
```