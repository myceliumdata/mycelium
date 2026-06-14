# Fuzzy lookup policy (bind fields → any field)

**Status:** In progress (slices `1430` name, `1435` employer).  
**Owners:** Grok + Paul.

## Scope today (MVR v1)

- Step-1 `lookup` searches **MVR bind fields only** (CRM: `name`, `employer`) via exact per-field indexes.
- **Fuzzy suggestions** (`lookup_suggested`, `sequence_ratio`, `SUGGESTION_MIN_SCORE = 0.85`) apply when exact index lookup returns 0 hits — first on partial/full paths for **names** (`1430`), then **employers** (`1435`).

## Policy (Paul, June 2026)

1. **All bind fields** — Any field in `mvr.bind_fields` should support fuzzy near-miss → `lookup_suggested` on 0 exact hits (partial and, where appropriate, full MVR). Implement per-field rankers or a shared `_rank_bind_field_suggestions(field, value)` helper; do not hardcode only `name` long-term.
2. **Any field (future)** — When [`TODO.md`](../../TODO.md) item *Query / search any field* ships, **fuzzy matching applies there too** (same outcome model: suggest before dead-end). Not only exact secondary indices.
3. **Typos vs aliases** — Current fuzzy is `difflib.SequenceMatcher` ratio on normalized strings — good for **typos** (missing letter, digit swap in longer strings), **not** for **short aliases** or prefix nicknames.

## SequenceMatcher expectations (CRM examples)

| Query | Candidate | Ratio | @ 0.85 |
|-------|-----------|-------|--------|
| `andrea kalman` | `andrea kalmans` | 0.96 | ✅ typo |
| `654 ventures` | `645 ventures` | 0.92 | ✅ digit typo |
| `645 venture` | `645 ventures` | 0.96 | ✅ plural typo |
| `645` | `645 ventures` | 0.40 | ❌ shorthand |
| `ibm` | `ibm corporation` | 0.33 | ❌ prefix nickname |

**Implication:** Searching `{"employer": "645"}` as a common name for **645 Ventures** will **not** fuzzy-match with the current algorithm. That needs a follow-up (prefix index, alias table, or token-overlap policy) — track under search-indices / any-field work.

## Slices

| Slice | Field | Status |
|-------|-------|--------|
| `1430` | `name` (partial 0-hit) | Cursor delivered — pending Grok review |
| `1435` | `employer` (partial 0-hit) | Queued |

## References

- [`src/agents/entity_resolution.py`](../../src/agents/entity_resolution.py) — `_rank_suggestions`, `SUGGESTION_MIN_SCORE`
- [`src/agents/target_resolve.py`](../../src/agents/target_resolve.py) — partial vs full MVR branch
- [`TODO.md`](../../TODO.md) — Search indices; Query / search any field