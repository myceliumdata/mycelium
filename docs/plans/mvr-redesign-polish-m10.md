# MVR redesign — polish backlog (slice M10)

**Status:** **Closed** (M10 reviewed, June 2026)  
**Program:** [`mvr-redesign-program.md`](mvr-redesign-program.md)

---

## Purpose

Non-blocking nits from Grok review of MVR slices **M1–M9** were logged here **and** in each slice `review.md`. **M10** addressed this backlog.

---

## Backlog (final)

| # | Source | Nit | Resolution |
|---|--------|-----|------------|
| P1 | M2 | Duplicate `_env_int` | **Closed** — `network/env_util.py` |
| P2 | M3 | `EntityQuery.id` naming | **Closed** — description |
| P3 | M3 | Cursor incomplete delivery | **Waived** |
| P4 | M4 | `_entity_field_value` hard-coded | **Closed** — `hasattr` |
| P5 | M4 | M4 tests borderline full | **Waived** |
| P6 | M5 | Specialist jinja churn | **Waived** — doc |
| P7 | M5 | Step-2 provenance identity-only | **Closed** — smoke |
| P8 | M6 | Orphan `delivery_id` | **Closed** — operator note |
| P9 | M6 | `response_quote_required` wrapper | **Waived** |
| P10 | M6 | Untyped `query` in block response | **Closed** |
| P11 | M6 | Metering accept duplication | **Closed** — `accept_quote_for_workload()` |
| P12 | M6 | `principal_required` / `payment_required` tests | **Partial** — principal only |
| P13 | M6 | Provenance-only step-1 quote | **Closed** — smoke |
| P14 | M7 | `bind_provisional_from_scope` hard-coded | **Partial** — loop; still name/employer bind |
| P15 | M7 | `is_full_mvr_lookup` empty values | **Closed** — docstring |
| P16 | M7 | Metered create-on-deliver | **Closed** — smoke |
| P17 | M7 | Architecture slice bullets | **Closed** — subsections |
| P18 | M8 | `partition_attribute_buckets` batch | **Closed** |
| P19 | M8 | Batch identity-only smoke | **Closed** |
| P20 | M8 | Sequential N×M | **Closed** — doc |
| P21 | M8 | Architecture M8 line | **Closed** |
| P22 | M9 | admin-ui legacy | **Closed** — two-step UI |
| P23 | M9 | crm-metering README step 2 | **Closed** |
| P24 | M9 | Fixture placeholder text | **Closed** |
| P25 | M9 | Supervisor legacy path | **Closed** — env gate |
| P26 | M9 | `health_check` two queries | **Waived** |

Post-ship debt folded into **Program 2** — see [`next-chunk-prep.md`](next-chunk-prep.md) (P12 payment smoke, P14 bind generalization, admin-ui e2e, P26 health ping). Architecture doc tense updated June 2026.

### Post vocabulary slice (2026-06-18)

| # | Source | Nit | Status |
|---|--------|-----|--------|
| P27 | vocabulary | `supervisor._identity_records_from_match` drops non-CRM bind keys | **Closed** — `responses._identity_records_from_match` |
| P28 | vocabulary | Message builders hardcode `employer` phrasing | **Closed** — `_identity_message_label` |
| P29 | vocabulary | `_rank_employer_suggestions` alias | **Closed** — removed |
| P30 | vocabulary | admin-ui `LookupSuggestion` TS types | **Closed** — `suggested_lookup` only |
| P31 | vocabulary | Smoke: identity-only `results[]` keys match grain MVR | **Closed** — `test_identity_records_from_match_preserves_mvr_bind_fields` |

---

## Exit criteria (M10)

- [x] All open rows addressed or explicitly waived
- [x] `./bin/ci-local` green
- [x] `review.md` for M10 references closed row ids