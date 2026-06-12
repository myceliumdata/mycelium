# Review — Program 1 Attribute provenance Slice 3

**Verdict:** **Approved**

**Reviewer:** Grok (Paul requested review, June 2026)

---

## CI (mandatory)

```bash
./bin/ci-local
```

| Step | Result |
|------|--------|
| `uv sync --all-extras` | OK |
| `admin-ui` build | OK |
| `ruff` | All checks passed |
| smoke pytest | **292 passed**, 26 deselected |

Extra: `LANGCHAIN_TRACING_V2=false uv run pytest -q` → **318 passed**  
Metering: `test_provenance_meter_on_quote` → 1 passed

---

## Spec compliance

| Requirement | Status |
|-------------|--------|
| `QueryResponse.provenance` field | Pass — distinct from `EntityQuery.provenance` request flag |
| `query_provenance.py` builder | Pass — `attr_sources` + category map; skips bind fields; deep-copies `versions[]` |
| Wire from `assemble_response` | Pass — `_attach_provenance` on `assembled`, `found`, research-gated (`found`) paths |
| Outcomes gated to delivered results | Pass — `assembled` / `found` only in `apply_query_provenance` |
| MCP schema documents `provenance` | Pass — `_neutral_json_schema(QueryResponse)` |
| `describe_network` / capabilities | Pass — `policy.query.response_provenance` + example JSON; MCP instructions updated |
| Tests | Pass — 6 smoke in `test_query_provenance.py`; onboarding asserts `response_provenance` |
| `docs/architecture.md` | Pass — request vs response flag + shape documented |
| Out of scope untouched | Pass — no operator write, no MVR/Program 2; flat `results[]` unchanged |

---

## Metering promise

`EntityQuery.provenance=true` now populates `QueryResponse.provenance` when versioned extended storage exists. Meter charges on request flag (existing behavior); response may be `null` when storage empty — acceptable.

---

## Non-blocking nits → polish slice P

| # | Nit |
|---|-----|
| P11 | `_category_for_attribute` reads `CategoryTree._data` / `_load()` (private API) — add public read-only map accessor or document |
| P12 | No multi-match provenance smoke test (`provenance.entities` length > 1) |

(P1–P10 from Slices 1–2 remain on polish backlog.)

---

## For Paul

- **Safe to commit** Program 1 slices 1–3 implementation + reviews (working tree is cumulative if not yet committed).
- **Polish slice P (`1400`) unblocked** — run after this commit lands.
- **Manual:** `uv run mycelium query --network crm --entity-key "Paul Murphy" --attributes linkedin --provenance` → check `provenance.entities[].attributes.linkedin.versions`.
- **TODO:** After polish approved, mark Program 1 complete; operator correction unblocked.

Suggested commit message (full Program 1):

```
feat: extended attribute provenance Program 1 (slices 1–3)

Versioned specialist storage, admin version history, QueryResponse.provenance
when EntityQuery.provenance=true.
```