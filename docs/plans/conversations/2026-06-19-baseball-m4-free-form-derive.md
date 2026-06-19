# Baseball M4 — free-form derive (manifest miss → LLM)

**Date:** 2026-06-19  
**Participants:** Paul + Grok  
**Status:** Design lock for first M4 slice; not implemented  
**Builds on:** tag `first_llm_computed_result` (M3–M3c), [`2026-06-19-warehouse-factory-layer3-specialist-emergence.md`](2026-06-19-warehouse-factory-layer3-specialist-emergence.md)

---

## What M3 shipped (training wheels)

| Mechanism | M3 behavior |
|-----------|-------------|
| Client label | Named attr in `requested_attributes` (e.g. `career_avg`) |
| Derive gate | **Whitelist** `derive_candidates: ["career_avg"]` only |
| Cache | Specialist storage field key = normalized attr name |
| Execution | M3c: manifest context + semantic review + retry |

`career_hr` and other aliased attrs never touch derive. `batting_average`, `ops`, etc. → `N/A` today.

---

## What M4 means (Paul direction)

**Client still uses `requested_attributes`** with a **free-form label** — not a new NL `question` field (that is **M5**).

| Phase | Client asks | Execution |
|-------|-------------|-----------|
| M3 (done) | `career_avg` (whitelisted derive candidate) | LLM codegen on cache miss |
| **M4** | Any batting label ontology routes (e.g. `ops`, `slugging_pct`) | Manifest alias miss → **derive** (no whitelist) |
| M5 (later) | Natural language `question` | Classify intent → derive |

**Constant:** computation-centric provenance envelope; two-step protocol; specialist-owned cache.

---

## Locked behavior (M4 v1)

1. **Domain derive gate** — `warehouse_domains.json` batting domain: `derive_on_miss: true` (name TBD). When `resolve_domain_attribute` returns `None` for an owned field, invoke `generate_and_run_derive()` — same M3c pipeline (context, review, retry).
2. **Remove attr whitelist** — `derive_candidates` list removed or ignored when `derive_on_miss` is true. M3 guinea pig `career_avg` continues to work via miss path (no alias).
3. **Cache key** — v1: normalized requested label as storage field key (same as M3). **Intent hash** for synonym dedup (`career_avg` vs `batting_average`) deferred to M4b/M5.
4. **Classification** — free-form labels must route to `batting_specialist` via existing `categories.json` / `attribute_map` or supervisor `classify()`. v1 guinea pig: add `ops` to `attribute_map` → batting (already in category examples).
5. **No research stub** on baseball warehouse categories — derive miss must not spawn CRM-style research specialist for batting attrs.
6. **End user** — value or `N/A`; operator `operator_audit` unchanged.

---

## Guinea pig

| Attr | Why |
|------|-----|
| **`ops`** | Multi-column rate; not in manifest aliases; in batting category examples; tests can mock formula |

Secondary regression: `career_avg` still works (cache + derive path without whitelist).

---

## Wire protocol (no EntityQuery change in v1)

Step 1:

```json
{
  "lookup": {"player": "Hank Aaron"},
  "requested_attributes": ["ops"],
  "provenance": true
}
```

Step 2: `delivery_id` only.

Optional later: `derive: { "label": "...", "intent": "..." }` — **not** M4 v1.

---

## Non-goals (M4 v1)

- NL `question` field (M5)
- Intent-hash synonym cache across labels
- Pitching / bio derive domains (batting only unless trivial to generalize flag)
- Deep provenance
- Specialist promotion automation
- Postgres / non-SQLite warehouse

---

## Risks

| Risk | Mitigation |
|------|------------|
| LLM derive on every obscure label | Ontology + `N/A` after max attempts; metering later |
| Research stub on unknown attr | Assert baseball batting path; no factory create for warehouse categories |
| Token cost | Cache hits on repeat; same as M3 |

---

## Verification

- Mocked LLM: `ops` on minimal fixture → non-`N/A` numeric string
- `career_avg` regression tests unchanged
- `./bin/ci-local`, `./bin/smoke-baseball-e2e`
- Manual (Paul): Aaron `ops` on live Lahman when API key set — order-of-magnitude sanity only

---

*Archived June 2026.*