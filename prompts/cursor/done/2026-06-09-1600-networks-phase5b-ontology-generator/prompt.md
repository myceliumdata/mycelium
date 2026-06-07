# Task: Networks Phase 5b — skeleton ontology generator (LLM)

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- `docs/plans/networks-phase5.md` (ontology vs classification, skeleton bootstrap)
- `src/agents/classification/engine.py` (LLM patterns, `_SEED_CATEGORIES`, validation)
- `src/agents/classification/models.py` (`CategoryTreeData`, `Category`)
- `src/agents/registry.py` (`RegisteredAgent`, `AgentRegistryData`)
- `docs/examples/sample-categories.json` (target JSON shape)

**Depends on:** Phase 5a (`2026-06-09-1500`) in `prompts/cursor/done/` — `MYCELIUM_SPECIALISTS_DIR` wired.

**Blocks:** slice `1700` (`network create` CLI).

---

## Objective

Implement **`src/network/ontology.py`**: given a user **creation prompt**, call the LLM once and return a validated **skeleton ontology**:

- `CategoryTreeData`-compatible categories (3–8 coarse domains)
- Minimal `attribute_map` built **only** from category `examples` (lowercased) — not exhaustive
- Companion registry entries (one generated specialist per category)

No CLI wiring in this slice. Callers (5c) will persist artifacts.

---

## Public API (suggested)

```python
def generate_skeleton_ontology(
    creation_prompt: str,
    *,
    model: str = "gpt-4o-mini",
) -> SkeletonOntologyResult:
    """LLM + validate + optional one retry. Raises OntologyGenerationError on failure."""
```

Return type should expose:

- `categories: CategoryTreeData` (or dict serializable to `categories.json`)
- `agents: list[RegisteredAgent]` ready for `agent_registry.json`
- `model_used: str`

---

## LLM design

### System prompt (embed in module or `prompts/system/` fragment)

- Mycelium network = scoped specialist graph
- User describes **what data the network manages** (people, vehicles, organisms, artifacts, … — not CRM-only)
- Output coarse **categories** with snake_case keys
- Each category gets one `assigned_agent` matching `^[a-z][a-z0-9_]*_specialist$`
- Provide 3–10 **example attribute names** per category (starter map only)
- Do **not** invent exhaustive attribute lists

### Structured output

Use Pydantic models + LangChain `with_structured_output` (mirror `classification/engine.py` patterns). Propose schema e.g.:

- `ProposedCategory`: `name`, `description`, `assigned_agent`, `examples: list[str]`
- `ProposedOntology`: `categories: list[ProposedCategory]`

### Post-processing

1. Normalize category keys (slugify: lowercase, spaces → `_`)
2. Validate agent names with existing factory regex
3. Build `attribute_map`: each example → its category (lowercase keys); skip duplicates (first wins)
4. Set `CategoryTreeData.last_updated` to now UTC; `model_used` from model arg
5. Build `RegisteredAgent` entries:
   - `module_path`: `agents.specialists.{name}` (loader uses file path via `MYCELIUM_SPECIALISTS_DIR`)
   - `storage_path` / `strategy_path`: under `MYCELIUM_AGENT_DATA_DIR` when set (use same helper as 5a factory fix)
   - `is_generated=True`, `created_at` now

### Retry

On validation failure, **one** retry with error context appended to the user message. Then raise `OntologyGenerationError` with a clear message (missing `OPENAI_API_KEY` → fail before LLM call with actionable text).

---

## Tests (`tests/test_network_ontology.py`)

**All tests mock the LLM** — no real API calls in CI.

| Test | Assert |
|------|--------|
| Happy path mock | Valid categories, attribute_map size == sum of examples, registry count matches |
| Invalid agent name mock | Retry then error |
| Empty prompt | `ValueError` before LLM |
| Missing API key | Clear error without network call |
| Diverse domain prompt string | Categories are not hardcoded CRM six (assert keys ≠ only contact/social/… OR count/slugs differ) |

Mark smoke tests `@pytest.mark.smoke`.

---

## Verification

```bash
uv run pytest -m smoke -q tests/test_network_ontology.py
uv run pytest -m smoke -q
uv run ruff check src tests
```

---

## Scope boundaries

**May modify:** new `src/network/ontology.py`, `src/network/__init__.py` (exports if useful), `tests/test_network_ontology.py`

**Out of scope:** `main.py` `network create`, writing files to disk, `AgentFactory.render_specialist_py`, MCP snippet, docs (slice `1800`)

---

## Deliverables

`prompts/cursor/done/2026-06-09-1600-networks-phase5b-ontology-generator/` with `prompt.md`, `output.md` (include example mock ontology JSON shape).