# Review: Networks Phase 5b — skeleton ontology generator

**Reviewer:** Grok  
**Date:** 2026-06-07  
**Verdict:** **Approved** — merge-quality; queue `1700`.

---

## Scope check

| Requirement | Status |
|-------------|--------|
| `src/network/ontology.py` + `generate_skeleton_ontology()` | ✅ |
| Structured LLM output (`ProposedOntology`) | ✅ |
| Skeleton: 3–8 categories, examples-only `attribute_map` | ✅ |
| Agent name regex + 1:1 category↔specialist | ✅ |
| One retry on validation failure | ✅ |
| `SkeletonOntologyResult` → `CategoryTreeData` + `RegisteredAgent` list | ✅ |
| Registry paths via `_registry_storage_paths` (5a) | ✅ |
| Domain-agnostic system prompt (not CRM-only) | ✅ |
| All tests mocked — no real API calls | ✅ |
| No CLI / file writes | ✅ |

Independent verification: `pytest -m smoke tests/test_network_ontology.py` — 5 passed; ruff clean.

---

## What looks good

- **`llm=` injection** keeps 5c testable without network calls; mock wrapper is minimal and clear.
- **Validation is thorough:** slugify, duplicates, bounds, empty description, agent regex.
- **System prompt** explicitly covers wheat/bacteria/clocks and warns against defaulting to CRM six — matches Paul’s domain-agnostic direction.
- **Exports** in `network/__init__.py` give 5c a clean import surface.

---

## Non-blocking niggles → **`1750` polish**

1. **`OPENAI_API_KEY` required even when `llm=` is injected** → `1750` item 4.
2. **Imports private `_registry_storage_paths`** → `1750` item 3 (public helper).
3. **No test for duplicate category keys / >8 categories** → `1750` item 5.

---

## Next step

Proceed with **`2026-06-09-1700-networks-phase5c-network-create-cli`**.