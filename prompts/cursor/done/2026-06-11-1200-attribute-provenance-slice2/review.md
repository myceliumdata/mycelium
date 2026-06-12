# Review — Program 1 Attribute provenance Slice 2

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
| smoke pytest | **286 passed**, 26 deselected |

Extra: `LANGCHAIN_TRACING_V2=false uv run pytest -q` → **312 passed**

---

## Spec compliance

| Requirement | Status |
|-------------|--------|
| Jinja template uses `specialist_fields` | Pass — imports, `_mark_fields_pending` via `append_version`, `pending_last_error` |
| Four framework specialists regenned + committed | Pass — `AUTO-GENERATED` headers 2026-06-12; canonical from template |
| `introspection.py` versioned reads | Pass — `EntityFieldStatus.versions`, `validate_versioned_field`, `current_*` |
| `_analyze_storage` versioned counts | Pass — uses `current_status` for versioned entries |
| Admin `types.ts` + `App.tsx` version UI | Pass — `<details>` per extended field; bind rows omit versions |
| Tests | Pass — `test_status_entity_fields_include_versions_json`, admin daemon versions assert |
| `docs/architecture.md` admin note | Pass |
| Out of scope untouched | Pass — no `QueryResponse.provenance` response field, no MVR/registry changes |

---

## Scope note (accepted)

Replaces Slice 1 hand-bridge on framework specialists with jinja-regen — correct outcome. Working tree may still include Slice 1 write-path files if not yet committed separately; review both slices together on commit.

---

## Non-blocking nits → polish slice P

Added to [`attribute-provenance-program1-polish.md`](../../../docs/plans/attribute-provenance-program1-polish.md):

| # | Nit |
|---|-----|
| P7 | `_analyze_storage` still counts legacy flat v1 blobs (no `validate_versioned_field`) |
| P8 | No smoke test: flat v1 storage on entity drill-down fails loud via status/introspection |
| P9 | `_entity_field_statuses` no-op `if status == "empty": status = "empty"` |
| P10 | Admin `.version-history` class has no CSS (functional but unstyled) |

(P1–P5 from Slice 1 remain on polish backlog.)

---

## For Paul

- **Safe to commit** Slice 2 (and Slice 1 if still uncommitted) + this `review.md`.
- **Slice 3 unblocked** — `2026-06-11-1300-attribute-provenance-slice3`.
- **Hands-on:** admin entity drill-down should show version `<details>` on extended fields after refresh + research.

Suggested commit message (slices 1+2 combined):

```
feat: attribute provenance Program 1 slices 1–2

Versioned specialist storage writes, jinja regen read path, introspection
versions[], admin field history.
```