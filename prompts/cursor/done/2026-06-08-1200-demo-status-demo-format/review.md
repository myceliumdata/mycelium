# Review: Demo status output — scannable default + `--verbose` (1200)

**Reviewer:** Grok  
**Date:** 2026-06-08  
**Verdict:** **Approved** — matches Paul’s spec; ready for hands-on demo.

---

## Scope check

| Requirement | Status |
|-------------|--------|
| Default demo layout (`Seed: ✅ (N)`, ontology ❌/list, specialists ❌/`category (count)`) | ✅ |
| No `Root:` in demo mode | ✅ |
| `category (e.g., email, phone, …)` abbreviation (first 2 + ellipsis) | ✅ |
| Domain-agnostic seed count (no “people”) | ✅ |
| `--verbose` preserves debug layout | ✅ |
| `--json` full struct (+ additive `CategorySummary.examples`) | ✅ |
| `--person` appends verbose drill-down under demo summary | ✅ |
| Tests: demo, verbose, category examples, CLI verbose | ✅ |
| README + CRM README | ✅ |
| `TODO.md` slice done | ✅ |

---

## Verification (Grok re-run)

```text
uv run pytest -m smoke -q tests/test_network_status.py  → 10 passed
uv run pytest -m smoke -q                               → 124 passed
uv run ruff check …                                     → clean
```

**Fresh network** (after `refresh-example-network crm --yes`):

```text
Network: crm (CRM example)
Seed: ✅ (15)
Current ontology: ❌
Existing specialists: ❌
```

**Running network** (post-query live CRM): demo shows ontology lines + `contact (1)`; `--verbose` shows full agent table; `jq` on `--json` works.

---

## What looks good

- **`format_status_demo` / `format_status_verbose` split** is clean; `format_status_human` → verbose alias preserves callers.
- **`format_category_examples`** unit-tested for 0/1/2/3+ cases.
- **Specialist lines use category slug + count** — exactly the demo story Paul wanted.
- **Person drill-down deferred** sensibly: verbose block appended only when `--person` set.

---

## Non-blocking nits

1. **Unicode ellipsis** (`…`) in output — fine for terminal; use ASCII `...` only if Paul prefers plain ASCII in recordings.
2. **`--person` demo styling** — still verbose (`Person lookup:` / agent names); follow-up task when Paul reviews drill-down.

---

## Next step

Paul hands-on demo with updated runbook (default status before/after query; `--verbose` if debugging). Then slice 3 or commit demo batch.