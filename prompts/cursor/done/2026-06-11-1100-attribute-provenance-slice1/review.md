# Review — Program 1 Attribute provenance Slice 1

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
| smoke pytest | **285 passed**, 26 deselected |

Extra (not substitute): `LANGCHAIN_TRACING_V2=false uv run pytest -q` → **311 passed**

---

## Spec compliance

| Requirement | Status |
|-------------|--------|
| `specialist_fields.py` helpers | Pass — append, current_*, P1-11 `update_current_pending`, flat rejection |
| `research.py` version bodies + actor | Pass — `sources: [{url}]`, `_write_pending`, `_persist_field_version` |
| P1-11 pending in-place / transition append | Pass — `_write_pending`, `_persist_field_version` |
| Found preserved on partial errors | Pass — `field_has_value` guard in `_mark_pending` / `_persist_field_version` |
| P1-10 `entity_growth` uses current version `at` | Pass |
| `base.py` `versioned_provenance_v1` strategy | Pass |
| Tests + fixtures | Pass — `test_specialist_fields.py`, `versioned_storage_fixtures.py`, `test_research.py` updated |
| `docs/architecture.md` storage note | Pass |
| Out of scope untouched | Pass — no jinja, introspection, `QueryResponse`, admin-ui, registry/MVR |

---

## Scope note (accepted)

Four committed `*_specialist.py` modules were **bridged** to import `specialist_fields` (~58 lines each). This exceeds the “≤10 lines” escape hatch but is **documented** in `output.md` and necessary for green pytest with versioned writes before Slice 2 regen. **Slice 2 must regen from `specialist_agent.py.j2`** — do not treat hand-edits as canonical.

---

## Non-blocking nits → polish slice P

Queued in [`attribute-provenance-program1-polish.md`](../../../docs/plans/attribute-provenance-program1-polish.md) (Cursor `1400`, after Slice 3):

| # | Nit |
|---|-----|
| P1 | `ensure_versioned_for_write` flat-pending wrap — document + test |
| P2 | `entity_growth` flat `researched_at` fallback — remove |
| P3 | `_persist_field_version` duplicate pending branch — remove |
| P4 | P1-11 in-place pending retry test — add |
| P5 | `specialist_fields` flat read fallbacks — remove after Slices 2–3 |

---

## For Paul

- **Safe to commit** slice 1 implementation + this `review.md`.
- **Operator:** `refresh-example-network crm` (or wipe `agents/*/storage.json`) before hands-on — flat found storage will error on research write.
- **Cursor:** Slice 2 (`1200`) unblocked — regen specialists from jinja; do not extend hand-bridge further.
- **TODO:** No change for Slice 1 alone; mark Program 1 progress after Slice 3.

Suggested commit message:

```
feat: versioned provenance for specialist storage (Program 1 slice 1)

Append-only versions[] on research write; flat v1 fails loud; P1-10/11 locked.
```