# Plan: Classification Engine - Phase 1 (Supervisor Intelligence)

**Status:** Approved (2026-06-03). This is the published version of the working plan developed in the Grok session. Cursor tasks must follow the scope, steps, and design exactly (with the lightweight priority note from approval).

> **Historical note (June 2026):** The "Current state" section below reflects the codebase at plan time. The live public API uses `EntityQuery` / `entity_key` / `query_entity` / `QueryResponse`; `core_data` and `PersonQuery` were removed in later redesigns. See `docs/architecture.md`.

> **Lightweight priority (from approval):** Keep implementation as lightweight as possible in early steps. Prioritize getting `classify()` + supervisor injection working cleanly before polishing `refresh_from_llm` and atomic saves. Err on the side of simplicity for Phase 1. (E.g. start with plain `.write_text` for save; add tempfile atomic in a later polish step only if it fits small changes.)

## Context
This plan is for **Phase 1 only** of the overall Supervisor Intelligence work, as defined in the authoritative high-level plan at `docs/plans/supervisor-intelligence-v1.md` (read and internalized first).

From that v1 plan:
- The Supervisor must evolve from a hardcoded router (`always "core_data"`) into an intelligent system that uses LLM for classification of data categories/domains.
- "Intelligent Classification: Use an LLM to analyze incoming data/requests and determine the correct category/domain."
- "Category Knowledge Base: Persistent store of known categories + examples."
- "Start with Phase 1 (Classification)."
- Full dynamic agent creation is Phase 2+ (explicitly out of scope here).
- Must align with architecture: supervisor remains narrow/thin coordinator (no storage access, no response building); no pre-defined derivatives in core storage; specialists (future) own domains; query-only public interface preserved; small/reviewable changes; explicit everything; LangSmith observability; reference `docs/architecture.md` + `prompts/system/CORE_PROMPT.md`.

**Current state (from codebase exploration):**
- `src/agents/supervisor.py`: Extremely thin (~30 lines). Defines local `_coerce` (handles dict or model) + `supervisor_agent` that does `_ = _coerce(state)` then **always** returns hardcoded `{"route": "core_data", "audit_log": ["Supervisor: evaluating query.", "Supervisor: routing to core_data specialist."]}`. Docstring says "classify the query and route to specialists" but performs zero inspection of `query` or attributes today. (This is the primary injection point for Phase 1.)
- `src/graphs/core.py`: `START → supervisor → _route_after_supervisor` (hardcoded `if current.route == "core_data"`) → `core_data_agent` or END. Uses both sync (MCP) and async (Studio) paths with env-driven SqliteSaver choice. `run_query` is the public entry that builds initial `MyceliumGraphState(query=PersonQuery(...))`.
- `src/models/state.py`: `PersonQuery` has `person_key` + `requested_attributes: list[str]`. `MyceliumGraphState` has `route: Literal["core_data"] | None`, `persons: list[Person]`, `person: Person | None` (compat for len==1), `response`, `audit_log: Annotated[list[str], operator.add]`, `non_core_attributes(requested)` helper (core-field filter). No classifications field yet. CORE_PERSON_FIELDS = {"id", "name", "employer"}.
- `src/agents/core_data.py`: Owns the non-core decision today inside `_build_lookup_response` (calls `non_core_attributes`, chooses `response_non_core` vs `response_found`). Builds payload dict with "response", "persons", conditional "person", "audit_log", "route": None. Calls into `CoreIdentity.find_by_key` + response builders. Synchronous node.
- `src/agents/responses.py`: `debug_for_query(query, **extra: str)` builds the flat debug str (includes requested_attributes + outcome + num_matches + non_core_requested). Builders: `response_found`, `response_non_core`, `response_not_found`, `_make_response`. All return PersonResponse; debug is the extension point for metadata.
- `src/agents/routing.py` (legacy, still imported in some tests): old `evaluate_supervisor_turn` + `SupervisorDecision` that duplicated the non-core logic (kept for test compat during transition).
- `src/agents/core_identity.py`: Thin wrapper over storage; `get_core_identity()` singleton + `reset_core_identity()`. Used only by core_data.
- `src/mycelium_mcp/server.py`: `list_specialist_routing()` Phase-1 stub. `query_person` JSON in/out calls `run_query`. Health check present. Forces sync checkpointer.
- `src/main.py`: `uv run mycelium query --person-key X --attributes a,b` builds PersonQuery and calls run_query.
- `src/storage/core.py`: `get_storage()` singleton, env MYCELIUM_DB_PATH / MYCELIUM_SEED_PATH, `find_by_key` (now returns list for ambiguity), seeding from seed_crm.json. Pattern to emulate for categories (env var + default data/ path + reset_).
- `tests/`: smoke tests (test_core_data_agent.py, test_supervisor_routing.py) use stubs/monkeypatch, no real IO. Full tests (test_core_graph.py) use `temp_storage` fixture with env overrides + resets + real run_query. `conftest.py` does session autouse cleanup of singletons.
- No category tree, no LLM classification at runtime (langchain + langchain-openai present in pyproject.toml for future structured output).
- `data/` has seed_crm.json + mycelium.db + checkpoints (no categories.json yet). `docs/plans/supervisor-intelligence-v1.md` is the high-level phased vision (Phase 1 = this).
- Audit_log (appended via Annotated add) + response.debug are the primary explainability channels (visible in Studio, CLI JSON, MCP, LangSmith).

**Phase 1 Goal (Classification Engine only):** Give the Supervisor the ability to *look up* (never LLM on hot path) a persistent category for each non-core `requested_attribute`, and inject that metadata (category, assigned_agent, description, confidence) into the result (via audit_log + state + debug). LLM is used *only* off the hot path for occasional tree evolution. Cache starts as simple JSON (data/categories.json). This sets up future routing to real specialists without changing public API or core behavior today.

All design must be lightweight/Pythonic/explicit/Pydantic-where-sensible/extensible (for embeddings, dynamic agents, SQLite later).

## Proposed Final File/Folder Structure
Keep changes localized and aligned with existing layout (`src/agents/`, `data/`, `docs/`, `tests/`). All modifications are small and reviewable.

**Files that will be created or modified (exact list for scope boxes in Cursor prompt):**

```
mycelium/  (project root)
├── data/
│   └── categories.json                 # NEW: Persistent cache (committed with initial seed; git-tracked like seed_crm.json). Contains categories dict + attribute_map + metadata.
├── src/
│   ├── agents/
│   │   ├── __init__.py                 # (optional) re-export get_category_tree for convenience
│   │   ├── supervisor.py               # MINIMAL: import + ~12 lines inside supervisor_agent to classify requested_attributes and inject audit + "classifications"
│   │   ├── core_data.py                # MINOR: read classifications from incoming state; pass through to payload for final graph state; optionally thread into response builders
│   │   ├── classification/             # NEW self-contained subpackage (colocated for now; easy to promote later)
│   │   │   ├── __init__.py             # from .engine import get_category_tree, CategoryTree, reset_category_tree
│   │   │   ├── engine.py               # CategoryTree + get_/reset_ + _load/_save/classify/refresh_from_llm (the core logic)
│   │   │   └── models.py               # Pydantic models only: Category, CategoryTreeData, ClassificationResult, CategoryProposal
│   │   └── responses.py                # MINOR: make debug_for_query robust to non-str values; update calls in core_data or builders to surface classifications in debug str when present
│   └── models/
│       └── state.py                    # ADD: classifications: list[dict[str, Any]] = Field(default_factory=list)  (plus doc + import Any if needed)
├── tests/
│   ├── test_core_data_agent.py         # (light) ensure direct core_data tests still pass (they construct states without classifications)
│   ├── test_supervisor_routing.py      # Update existing supervisor smoke + add one asserting classifications list + correct category for known non-core attr (smoke-safe)
│   ├── test_core_graph.py              # Update temp_storage fixture (add reset_category_tree + monkeypatch MYCELIUM_CATEGORIES_PATH); enhance non-core full test to assert classification metadata in debug/audit
│   └── conftest.py                     # Add reset_category_tree to the session cleanup tuple
├── docs/
│   └── plans/
│       └── supervisor-intelligence-v1.md          # (reference only; do not edit)
│       └── classification-engine-phase1.md        # This published plan (stable snapshot of the reviewed design). The working copy during initial planning lived in the Grok session plan file; this is the committed reference.
├── pyproject.toml                      # (no changes; langchain-openai already present)
└── (explicitly untouched in Phase 1)
    - src/mycelium_mcp/server.py (list_specialist_routing remains stub; classification is internal)
    - src/main.py, src/graphs/core.py (no routing logic change; auto-benefits from supervisor update)
    - src/storage/, src/agents/core_identity.py, legacy routing.py/enrich/* (except test imports), etc.
```

Rationale:
- `data/categories.json` follows data/ convention and is the single source for the committed seed. Runtime writes are additive/evolving only.
- `src/agents/classification/` is a narrow, self-contained unit (matches LangGraph rules in .cursor/rules/02-langgraph.mdc + explicitness from CORE_PROMPT). Supervisor imports from it; nothing else needs to know internals.
- Minimal delta to supervisor (the "intelligence" entry point), core_data (propagation), state (bag for metadata), responses (observability). Matches "minimal changes" requirement and architecture.md ("supervisor remains narrow coordinator").
- Resets + env + fixture updates are required for test isolation (pattern from storage/core + graphs/core + conftest).
- No public API change, no hot-path LLM, no specialist creation (Phase 2).

Later (Phase 2+ per v1.md): use `classifications[*].category` / `assigned_agent` to drive real routing or trigger creation; evolve storage to SQLite or embeddings; promote classification/ out of agents/.

## Detailed Design of CategoryTree Class / Module
**Goal**: Fast in-memory lookup. Persistent JSON cache. LLM only in refresh path. Pydantic for safety/typing. Explicit and readable.

### Pydantic Models (src/agents/classification/models.py)
```python
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any

class Category(BaseModel):
    """A data category/domain that can be assigned to attributes.

    The category *name* is the dict key in CategoryTreeData.categories (no duplication
    inside the value object). This keeps the persisted JSON clean and the lookup index simple.
    """
    description: str
    assigned_agent: str  # e.g. "contact_specialist", "core_data" (Phase 1 uses core_data for unknowns too), or future specialist name
    examples: list[str] = Field(default_factory=list)

class CategoryTreeData(BaseModel):
    """The serializable shape of the entire tree (written to JSON)."""
    version: str = "1.0"
    last_updated: datetime
    model_used: str = ""  # e.g. "gpt-4o-mini" (set on last LLM refresh)
    categories: dict[str, Category]  # category_name -> Category (name is the key)
    attribute_map: dict[str, str]    # normalized_attribute (lower) -> category_name (the fast lookup index)

class ClassificationResult(BaseModel):
    """What classify() returns (easy to JSON-serialize into audit/debug/state)."""
    attribute: str
    category: str
    assigned_agent: str | None
    description: str
    confidence: float

class CategoryProposal(BaseModel):
    """Structured output shape for the LLM refresh path only (never on hot path)."""
    attribute: str
    category: str
    description: str | None = None
    assigned_agent: str | None = None
    confidence: float = 0.0
```

### CategoryTree (src/agents/classification/engine.py)
```python
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Optional
from datetime import datetime, timezone

from .models import CategoryTreeData, ClassificationResult, Category, CategoryProposal

def _default_categories_path() -> Path:
    """Follow storage/core.py + graphs/core.py env convention."""
    return Path(os.getenv("MYCELIUM_CATEGORIES_PATH", "data/categories.json"))

# Embedded fallback seed (must be kept in sync with the committed data/categories.json).
# Used only when the cache file is absent (first run after clone, or test isolation with custom path).
# Cursor will ensure the json on disk and this dict produce identical CategoryTreeData.
_SEED_CATEGORIES: dict[str, Any] = {
    "version": "1.0",
    "last_updated": "2026-06-03T00:00:00+00:00",
    "model_used": "",
    "categories": {
        "contact": {
            "description": "Direct ways to reach the person (email, phone, physical).",
            "assigned_agent": "contact_specialist",
            "examples": ["email", "phone", "mobile", "address", "website"]
        },
        "social": {
            "description": "Social and professional network profiles and handles.",
            "assigned_agent": "social_specialist",
            "examples": ["linkedin", "x_handle", "twitter", "facebook", "instagram"]
        },
        "relationships": {
            "description": "Personal and family relationships.",
            "assigned_agent": "relationships_specialist",
            "examples": ["spouse", "partner", "family", "children", "parents"]
        },
        "demographic": {
            "description": "Basic personal characteristics and background.",
            "assigned_agent": "demographic_specialist",
            "examples": ["age", "birthday", "gender", "nationality", "location"]
        },
        "professional": {
            "description": "Career, education, and investment-related details.",
            "assigned_agent": "professional_specialist",
            "examples": ["title", "bio", "education", "previous_firms", "investments"]
        }
    },
    "attribute_map": {
        "email": "contact",
        "phone": "contact",
        "mobile": "contact",
        "address": "contact",
        "website": "contact",
        "linkedin": "social",
        "x_handle": "social",
        "twitter": "social",
        "facebook": "social",
        "instagram": "social",
        "spouse": "relationships",
        "partner": "relationships",
        "family": "relationships",
        "children": "relationships",
        "parents": "relationships",
        "age": "demographic",
        "birthday": "demographic",
        "gender": "demographic",
        "nationality": "demographic",
        "location": "demographic",
        "title": "professional",
        "bio": "professional",
        "education": "professional",
        "previous_firms": "professional",
        "investments": "professional"
    }
}

class CategoryTree:
    """In-memory category tree with persistent JSON cache.

    Core contract for Phase 1:
    - classify() is a pure, fast, in-memory dict lookup. NEVER calls LLM or does I/O on the hot path.
    - LLM (via refresh_from_llm) is used only occasionally, explicitly, off the query path.
    - Persistent store starts as simple committed JSON (data/categories.json). Easy to evolve to SQLite later.
    - Unknown attributes return a safe, explicit "unknown" result (no exception, no LLM call).
    """

    def __init__(self, cache_path: Optional[Path] = None):
        self.cache_path = cache_path or _default_categories_path()
        self._data: Optional[CategoryTreeData] = None
        self._load()

    def _load(self) -> None:
        if self.cache_path.exists():
            raw = json.loads(self.cache_path.read_text(encoding="utf-8"))
            self._data = CategoryTreeData.model_validate(raw)
        else:
            self._data = self._create_seed()
            self._save()

    def _save(self) -> None:
        """Atomic write to reduce risk of partial writes / corruption."""
        if self._data is None:
            return
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        payload = self._data.model_dump_json(indent=2)
        # Write to temp then replace (cross-platform safe).
        fd, tmp_path = tempfile.mkstemp(dir=self.cache_path.parent, suffix=".json.tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(payload)
            os.replace(tmp_path, self.cache_path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
            raise

    def _create_seed(self) -> CategoryTreeData:
        """Return a fresh CategoryTreeData from the embedded seed constant.

        This is the only place the initial seed taxonomy (5 categories and 25 attribute mappings) is defined in code.
        The committed data/categories.json must match the effect of this.
        """
        # last_updated in seed is a fixed past time; real updates will set now().
        return CategoryTreeData.model_validate(_SEED_CATEGORIES)

    def reload(self) -> None:
        """Force reload from disk (for manual/admin use after external edit)."""
        self._load()

    def classify(self, attribute: str) -> ClassificationResult:
        """Fast in-memory lookup by normalized attribute name. Never blocks on I/O or LLM."""
        if self._data is None:
            self._load()
        normalized = attribute.strip().lower()
        if normalized not in self._data.attribute_map:
            return ClassificationResult(
                attribute=attribute,
                category="unknown",
                assigned_agent=None,
                description="No classification available for this attribute.",
                confidence=0.0,
            )
        cat_name = self._data.attribute_map[normalized]
        cat = self._data.categories[cat_name]
        return ClassificationResult(
            attribute=attribute,
            category=cat_name,
            assigned_agent=cat.assigned_agent,
            description=cat.description,
            confidence=0.95,  # Phase 1: known mappings are high-confidence by construction
        )

    def get_categories(self) -> dict[str, Category]:
        if self._data is None:
            self._load()
        return self._data.categories.copy()

    def refresh_from_llm(
        self,
        attributes: list[str],
        llm: Optional[Any] = None,
        model: str = "gpt-4o-mini",
    ) -> dict[str, Any]:
        """Occasional / admin / script-only path. SAFE TO CALL FROM CLI OR FUTURE JOB.

        - Builds a careful prompt including current taxonomy.
        - Calls LLM with structured output (CategoryProposal list) — temperature 0.
        - Applies *only* proposals with confidence >= 0.7, additive only (never deletes).
        - Updates last_updated + model_used, persists atomically, reloads in-memory.
        - Returns a change summary for logging/audit.
        - If no OPENAI_API_KEY (or other provider), the ChatOpenAI call will raise — caller handles.
        """
        if llm is None:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model=model, temperature=0.0)

        if self._data is None:
            self._load()

        current_cat_names = list(self._data.categories.keys())
        current_map = self._data.attribute_map
        attrs_to_consider = [a.strip() for a in attributes if a.strip() and a.strip().lower() not in current_map]

        if not attrs_to_consider:
            return {"added_categories": [], "updated_attributes": [], "skipped": [], "reason": "all already known"}

        # Prompt is explicit, versioned, and conservative.
        prompt = f"""You are maintaining a small, stable taxonomy for personal/career data attributes used by an AI data system.

Current top-level categories: {current_cat_names}

Existing attribute -> category mappings (do not re-propose these): {list(current_map.keys())[:30]} ...

For each of the following new or unknown attributes, decide:
- The best existing category, or propose a new short category name (lowercase, no spaces, e.g. "financial", "education").
- A one-sentence description for the category (only if new).
- A sensible future "assigned_agent" name (e.g. "financial_specialist" or "pending_<cat>").
- Your confidence (0.0-1.0) that this is the right long-term home for the attribute.

Return ONLY a list of proposals (even if empty). Be conservative: if unsure, confidence < 0.7 or skip.

Attributes to classify: {attrs_to_consider}
"""
        structured_llm = llm.with_structured_output(list[CategoryProposal])
        proposals: list[CategoryProposal] = structured_llm.invoke(prompt)

        changes = {"added_categories": [], "updated_attributes": [], "skipped": []}
        for p in proposals:
            attr = p.attribute.strip().lower()
            cat_name = p.category.strip().lower().replace(" ", "_")
            conf = float(p.confidence or 0.0)
            if conf < 0.7:
                changes["skipped"].append(attr)
                continue
            if cat_name not in self._data.categories:
                self._data.categories[cat_name] = Category(
                    description=(p.description or f"Data related to {cat_name}."),
                    assigned_agent=(p.assigned_agent or f"pending_{cat_name}"),
                    examples=[attr],
                )
                changes["added_categories"].append(cat_name)
            self._data.attribute_map[attr] = cat_name
            if attr not in changes["updated_attributes"]:
                changes["updated_attributes"].append(attr)

        self._data.last_updated = datetime.now(timezone.utc)
        self._data.model_used = model
        self._save()
        self._load()
        return changes
```

**Singleton / access + reset** (put at bottom of engine.py or in __init__.py):
```python
_category_tree: Optional[CategoryTree] = None

def get_category_tree() -> CategoryTree:
    """Process-wide cached CategoryTree (lazy; respects MYCELIUM_CATEGORIES_PATH)."""
    global _category_tree
    if _category_tree is None:
        _category_tree = CategoryTree()
    return _category_tree

def reset_category_tree() -> None:
    """Clear the singleton (for tests + admin reload scenarios). Safe to call liberally."""
    global _category_tree
    _category_tree = None
```

**Loading strategy**: Lazy on first `get_category_tree().classify(...)`. After load: pure dict lookups, O(1), no I/O. `reload()` for admin after hand-editing the JSON. `reset_category_tree()` clears the global for test isolation (see conftest and temp fixtures).

**Persistence & safety**: Atomic _save (tempfile + os.replace). On any write error the tmp is cleaned. Low-concurrency assumption in Phase 1 (CLI one-shot, single MCP stdio process, test fixtures with env overrides). Later can add file locks or move to SQLite if contention appears.

**Extensibility notes**: The public surface (classify returning ClassificationResult, get_categories, refresh_from_llm) is stable. Internal _data is not exposed. Easy to later add embedding similarity fallback inside classify for "fuzzy unknown", or change the backing store behind the same API. Also import `tempfile` and `os` at top for the atomic save.

## How the Supervisor Will Call This (Minimal Changes)
Current supervisor is one tiny function (~30 LOC). We add classification **only** for requested_attributes (no behavior change for pure core lookups). Classification metadata is injected for observability and future routing; the route decision stays "core_data" in Phase 1.

**Realistic small diff for `src/agents/supervisor.py`** (the only material change; _coerce already exists locally):

```diff
 from __future__ import annotations

 from typing import Any

+from .classification import get_category_tree
 from models.state import MyceliumGraphState


 def _coerce(state: MyceliumGraphState | dict[str, Any]) -> MyceliumGraphState:
     if isinstance(state, MyceliumGraphState):
         return state
     return MyceliumGraphState.model_validate(state)


 def supervisor_agent(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
     """
     Coordinator entry point: classify the query and route to specialists.

     Does not access storage or build ``PersonResponse`` payloads. Core lookups
     are delegated to ``core_data_agent`` via ``route="core_data"``.
     """
-    _ = _coerce(state)
-    return {
-        "route": "core_data",
-        "audit_log": [
-            "Supervisor: evaluating query.",
-            "Supervisor: routing to core_data specialist.",
-        ],
-    }
+    current = _coerce(state)
+    query = current.query
+    audit_log = ["Supervisor: evaluating query."]
+
+    classifications: list[dict[str, Any]] = []
+    if query.requested_attributes:
+        tree = get_category_tree()
+        for attr in query.requested_attributes:
+            cl = tree.classify(attr)
+            classifications.append(cl.model_dump())
+            if cl.category != "unknown":
+                audit_log.append(
+                    f"Supervisor: classified '{attr}' -> category={cl.category}, "
+                    f"agent={cl.assigned_agent}, confidence={cl.confidence:.2f}"
+                )
+
+    # Phase 1: classification is metadata only. Real specialist routing comes in Phase 2+.
+    route = "core_data"
+    audit_log.append(f"Supervisor: routing to {route} specialist.")
+
+    result: dict[str, Any] = {
+        "route": route,
+        "audit_log": audit_log,
+    }
+    if classifications:
+        result["classifications"] = classifications  # visible in final graph state + Studio
+
+    return result
```

**State change (minimal, one field)**: Add to `MyceliumGraphState` in `src/models/state.py` (near audit_log):
```python
    classifications: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Per-attribute classification metadata from supervisor (category, assigned_agent, confidence, ...). Phase 1 lookup only; used for debug + future routing.",
    )
```
(Import `Any` from typing if not already present for the annotation. The field is a plain list — supervisor writes it; later nodes read it. No reducer needed because it is set once per invocation.)

**Propagation to result / observability (core_data + responses)**:
- In `src/agents/core_data.py` (in `_run_core_data_lookup` or right after `current = _coerce(state)`): `classifications = getattr(current, "classifications", [])` and include in the returned payload dict so it ends up in the final graph state.
- Pass `classifications` (or a json-safe summary) into the response builder calls or enhance the debug_for_query(**extra) calls inside `response_non_core` etc. so that `response.debug` contains e.g. `classifications=[{'attribute':'email','category':'contact',...}]`.
- Because debug_for_query already does `**extra`, a one-line addition like `classifications=...` in the builder call sites (or a small helper) is sufficient.
- Net effect: `response.debug` + full state (Studio/LangSmith) + audit_log all surface the classifications for known non-core attrs. Unknowns are explicit with category="unknown", confidence=0.0 (no LLM call, no breakage).

This is the **minimal** surface: supervisor does the lookup + audit injection + state bag; core_data just forwards; responses just stringifies for debug. Zero change to graph edges, public PersonResponse shape, or query behavior for core-only requests. Future phases will read `classifications` in supervisor to choose `route` dynamically.

## Safe Mechanism for Occasional LLM-Based Tree Updates
**Never** called from `supervisor_agent`, `core_data_agent`, `run_query`, MCP `query_person`, etc.

**The mechanism** (in `CategoryTree`):
- `refresh_from_llm(attributes: list[str], model=..., llm=None) -> dict`
- Inside: builds a careful prompt (current categories + the attributes), calls LLM with `with_structured_output`, applies only high-confidence proposals, updates metadata, calls `_save()` (atomic), reloads.
- Conservative rules inside refresh:
  - Confidence threshold (e.g. >= 0.7).
  - Never delete existing mappings.
  - New categories only if LLM proposes with description + assigned_agent.
  - Log/return exactly what changed.
- Invocation (documented, not in hot path):
  - Ad-hoc: `python -c 'from src.agents.classification.engine import get_category_tree; print(get_category_tree().refresh_from_llm(["spouse", "kids", "new_field"]))'`
  - Future CLI: `uv run mycelium evolve-classifier --attrs spouse,kids` (add later, out of Phase 1 scope).
  - Triggered by logs: parse "unknown attribute" from audit logs of recent queries and feed them in.
- Safety: temperature=0, structured output (Pydantic or json schema), explicit prompt with examples from seed, version bump on change.

This satisfies "LLM only occasionally to build and evolve", "separate from normal queries".

## Initial Seed Content for categories.json
The committed `data/categories.json` (created in Step 1) contains the exact initial taxonomy (5 categories, 25 attributes across demographic / contact / relationships / social / professional). It is the runtime-persistent source of truth.

The JSON below is the **target content** (hand-authored or emitted by a tiny one-off `python -c 'from agents.classification.engine import CategoryTree; ...'` after the constant is defined). It must produce the same `CategoryTreeData` as the `_SEED_CATEGORIES` constant embedded in `engine.py` (the constant is the single source for "bootstrap when file absent").

```json
{
  "version": "1.0",
  "last_updated": "2026-06-03T00:00:00+00:00",
  "model_used": "",
  "categories": {
    "contact": {
      "description": "Direct ways to reach the person (email, phone, physical).",
      "assigned_agent": "contact_specialist",
      "examples": ["email", "phone", "mobile", "address", "website"]
    },
    "social": {
      "description": "Social and professional network profiles and handles.",
      "assigned_agent": "social_specialist",
      "examples": ["linkedin", "x_handle", "twitter", "facebook", "instagram"]
    },
    "relationships": {
      "description": "Personal and family relationships.",
      "assigned_agent": "relationships_specialist",
      "examples": ["spouse", "partner", "family", "children", "parents"]
    },
    "demographic": {
      "description": "Basic personal characteristics and background.",
      "assigned_agent": "demographic_specialist",
      "examples": ["age", "birthday", "gender", "nationality", "location"]
    },
    "professional": {
      "description": "Career, education, and investment-related details.",
      "assigned_agent": "professional_specialist",
      "examples": ["title", "bio", "education", "previous_firms", "investments"]
    }
  },
  "attribute_map": {
    "email": "contact", "phone": "contact", "mobile": "contact", "address": "contact", "website": "contact",
    "linkedin": "social", "x_handle": "social", "twitter": "social", "facebook": "social", "instagram": "social",
    "spouse": "relationships", "partner": "relationships", "family": "relationships", "children": "relationships", "parents": "relationships",
    "age": "demographic", "birthday": "demographic", "gender": "demographic", "nationality": "demographic", "location": "demographic",
    "title": "professional", "bio": "professional", "education": "professional", "previous_firms": "professional", "investments": "professional"
  }
}
```

(Exactly 25 attributes. Covers the required demographic/contact/relationships plus social/professional for realism. `assigned_agent` values are forward-looking names for Phase 2+ dynamic specialists; in Phase 1 they are only metadata.)

`CategoryTree` on missing file (or explicit reset + custom path) falls back to the embedded `_SEED_CATEGORIES` and writes the file. Cursor must keep the committed JSON and the `_SEED_CATEGORIES` literal in sync (verified in smoke + "delete json, re-run" test).

## Risk / Mitigation Section (Focus on cache consistency + unknowns)
- **Cache staleness / inconsistency across processes or after manual edit**: 
  - Mitigation: Atomic `_save` (tempfile + os.replace) in engine.py. Explicit `reload()` and `reset_category_tree()` APIs. Tests and fixtures always set `MYCELIUM_CATEGORIES_PATH` to an isolated tmp file and call resets (see temp_storage fixture + conftest). Document "after hand-editing the JSON, call .reload() or restart the process".
  - Phase 1 assumption: low write concurrency (one CLI invocation at a time, one long-lived MCP stdio, test processes with env overrides). No file locking yet.
- **Unknown attributes break queries, cause bad UX, or accidentally trigger LLM on hot path**:
  - Mitigation: `classify(attr)` **never** calls LLM or does sync I/O; for missing normalized key it returns a well-typed `ClassificationResult(category="unknown", assigned_agent=None, confidence=0.0, description=...)`. Supervisor only appends audit for non-unknown. Core data / responses treat "unknown" exactly as today (non_core narrative still emitted, query succeeds). Unknowns are logged in audit for later explicit `refresh_from_llm` (manual or log-mining job).
- **LLM hallucinations / bad proposals during refresh**:
  - Mitigation: `refresh_from_llm` is **never reachable from supervisor, core_data, run_query, or MCP**. Conservative merge: conf >= 0.7 only, additive (no deletes, no overwrites of existing attrs), temperature=0, structured Pydantic output (CategoryProposal), prompt tells model to be conservative and reuse existing cats. Detailed changes dict returned. Human can always `git checkout` or hand-edit the JSON + reload. No auto-refresh in hot path.
- **Drift between committed data/categories.json and the _SEED_CATEGORIES fallback constant**:
  - Mitigation: Step 1 creates the json; Step 2 implements engine with the constant; explicit verification step ("rm data/categories.json; uv run python -c 'from agents.classification import get...; print(get().classify(\"email\"))'") + smoke test that exercises the fallback path. Version field present for future.
- **Performance or memory on hot path**:
  - Mitigation: After first load, classify is two dict lookups + str ops. Singleton is cheap. No per-query I/O or allocations beyond the result object (which is tiny and immediately dumped to audit/state).
- **State bloat / checkpoint bloat / serialization issues**:
  - Mitigation: `classifications` is list[plain dict] (Pydantic + LangGraph serde already handle similar for Person etc.). Only present when requested_attributes was non-empty. Debug stringification keeps it human-readable but bounded. Checkpoint allowlist may need update in graphs/core.py if we see warnings (small, documented).
- **Scope creep (accidentally implementing dynamic agents or hot-path LLM in Phase 1)**:
  - Mitigation: This plan + the Cursor prompt will have **strict scope boxes** listing exact files. "Stop and escalate" rule from WORKFLOW. Explicit comments in code: "Phase 1 lookup only", "LLM only in refresh_from_llm". v1.md and architecture.md referenced as context.
- **Missing OPENAI key or provider cost during manual refresh**:
  - Mitigation: Refresh is opt-in (python -c or future script). Document that it requires a valid key for the chosen model. Hot path has literally zero LLM imports or calls (grep-enforced in verification). If key missing, the manual call fails loudly with clear ImportError / auth error — no silent degradation into hot path.

All mitigations are lightweight and Pythonic; nothing speculative. The design explicitly prepares the extension points (separate refresh, stable ClassificationResult shape, reset hooks) for Phase 2 without implementing any of it.

## Step-by-Step Implementation Tasks for Cursor (Small, Reviewable)
Follow WORKFLOW.md + test policy strictly. Scope boundaries: only the files listed in "Proposed final file/folder structure" above (plus the plan artifact itself). Smoke tests default. One small diff per step where possible. Reference this plan + supervisor-intelligence-v1.md + current architecture.md.

**Step 1: Scaffold + seed data (pure data + docs, no code logic)**
- Create `data/categories.json` with the exact initial seed JSON from the "Initial Seed Content" section (18 attrs, 5 cats). `git add` it.
- Create the package dir + files: `src/agents/classification/__init__.py` (will export later), `models.py` (can be minimal), `engine.py` (with stubs or pass).
- No code changes to any existing .py yet. No docs/ edits required beyond this plan.
- Verify: `git status`, `cat data/categories.json | head -20`, `uv run python -c "
import json, pprint
pprint.pprint(list(json.load(open('data/categories.json'))['attribute_map'].keys()))
"`.
- `uv run pytest -m smoke -q` (must be green; nothing broken).

**Step 2: Core Pydantic models + basic engine (no LLM, no wiring)**
- Implement `src/agents/classification/models.py` with Category, CategoryTreeData, ClassificationResult, CategoryProposal (exact shapes from plan).
- Implement `src/agents/classification/engine.py`: imports (incl. tempfile/os), _SEED_CATEGORIES constant (exact match to json), _default_categories_path (MYCELIUM_CATEGORIES_PATH), CategoryTree with __init__/_load/_save (atomic tempfile+replace), _create_seed (from _SEED), reload, classify (fast path + unknown), get_categories, refresh_from_llm stub or no-op, plus the two module-level get_category_tree / reset_category_tree.
- Implement `src/agents/classification/__init__.py`: `from .engine import get_category_tree, CategoryTree, reset_category_tree; __all__ = ...`
- Add a smoke-safe test (in test_supervisor_routing.py or a new tiny test_classify_smoke.py but prefer existing) that does `from agents.classification.engine import CategoryTree; t=CategoryTree(cache_path=tmp_json_with_seed); assert t.classify('email').category == 'contact'; assert t.classify('foo').category == 'unknown'`.
- Verify: `uv run pytest -m smoke -q`; manual:
  `uv run python -c '
  from agents.classification import get_category_tree, reset_category_tree
  reset_category_tree()
  t = get_category_tree()
  print(t.classify("email"))
  print(t.classify("spouse"))
  print(t.classify("weird_unknown"))
  '`
  (should show contact/relationships/unknown, no errors, no LLM).

**Step 3: Wire into Supervisor (minimal change, audit + state injection) + test isolation basics**
- Update `src/models/state.py`: add the `classifications: list[dict[str, Any]] = Field(...)` field + description. (Also ensure `Any` imported.)
- Update `src/agents/supervisor.py`: the small diff shown in the "How the Supervisor..." section (import, current= , classify loop, audit strings for known, return the list).
- Update `tests/conftest.py`: import reset_category_tree and add it to the cleanup tuple in _final_cleanup.
- Update `tests/test_supervisor_routing.py`: (a) make the existing `test_supervisor_agent_routes_to_core_data` still pass (empty classifications ok), (b) add a new @pytest.mark.smoke test that supplies requested_attributes with a known non-core + asserts "classifications" in result and correct category/assigned_agent values (smoke because no storage, just the agent node + our pure classify).
- Verify: `uv run pytest -m smoke -q`; `uv run mycelium query --person-key "Nichanan Kesonpat" --attributes email` (audit now has "classified 'email' -> category=contact...", state dump would show classifications, response still works exactly as before).

**Step 4: Propagate classification metadata into the result (debug / response) + full test fixture**
- Update `src/agents/core_data.py`: after `current = _coerce(state)`, capture `classifications = getattr(current, "classifications", [])`; include `"classifications": classifications` in the payload dict returned by `_run_core_data_lookup`.
- Update `src/agents/responses.py`: make `debug_for_query` tolerant of non-str extra values (e.g. `str(value)` or json.dumps for lists); or update the three response_* call sites inside core_data (or add a small internal helper) to pass `classifications=...` (or a compact str) so it appears in the final response.debug.
- Update `tests/test_core_graph.py`: in the `temp_storage` fixture, also `from agents.classification.engine import reset_category_tree`; call `reset_category_tree()` in setup and teardown; add `monkeypatch.setenv("MYCELIUM_CATEGORIES_PATH", str(tmp_path / "categories.json"))` (so tests use isolated copy; the first classify will seed it from constant or we can pre-copy the committed one).
- Update the non-core full test (or add assert) to check that when requested_attributes has known values, the response.debug contains category info or the final state (if inspected) has classifications.
- Verify: `uv run pytest -m smoke -q` (still); `uv run pytest -m full -q -k "non_core or query_non_core"` (the full test must pass and show classification evidence in debug or via direct state inspection if added). Manual CLI non-core query now has the metadata in .debug.

**Step 5: Add the LLM refresh path (still not on hot path; implement the real body)**
- Fill in the body of `refresh_from_llm` in engine.py (the sketch in the design section is the target): lazy `from langchain_openai import ChatOpenAI`, build the exact prompt shown (current cats + attrs), `with_structured_output(list[CategoryProposal])`, conservative merge (0.7, additive, normalize names), set metadata, atomic save + reload, return changes.
- Add a smoke test (in test_supervisor_routing.py or alongside the classify smoke) that exercises the *merge logic* safely: either (a) pass a pre-created llm mock via the param, or (b) temporarily monkeypatch the ChatOpenAI class, or (c) test only the "all known -> no-op" early return path + the change-dict shape. Do **not** make a real LLM call in the smoke run.
- In engine.py add a clear module docstring or comment block: "refresh_from_llm is the ONLY place in the entire codebase that may import or call an LLM for classification. It must never be called from supervisor, core_data, graphs, mcp, main, or any query path."
- Verify (as part of this step): `grep -r "refresh_from_llm\|ChatOpenAI" --include="*.py" src/agents/supervisor.py src/agents/core_data.py src/graphs/core.py src/mycelium_mcp/server.py src/main.py` → only hits should be inside classification/engine.py (the method itself). Manual off-path call (with key) updates a temp json and subsequent classify sees the new attr.

**Step 6: Polish, cross-test updates, lint, docs touch (minimal), final verification**
- (Optional) Update `src/agents/__init__.py` to also export classification symbols if it simplifies imports elsewhere (low priority; can stay internal via agents.classification).
- Ensure all the smoke tests that directly invoke supervisor_agent or core_data_agent with requested_attributes still pass and (where meaningful) assert on the new classifications field or debug content.
- Enhance the full non-core test in test_core_graph.py (already touched in step 4) to assert classification evidence appears for a seeded attr.
- Run the full verification matrix (see below). Fix any breakage.
- Small doc updates only if high value: add 1-2 sentences to `docs/architecture.md` under "Derivative / Non-Core Data" or the supervisor section mentioning "Phase 1 Classification Engine (see docs/plans/...) provides fast cached category metadata for requested_attributes; injected into audit + debug + state.classifications. LLM used only for offline tree evolution."
- `uv run ruff check src/agents/classification src/agents/supervisor.py src/agents/core_data.py src/models/state.py tests/test_supervisor_routing.py tests/test_core_graph.py tests/conftest.py`
- `uv run pytest -m smoke -q && uv run pytest -m full -q -k "non_core or supervisor or classify or graph"` (or the relevant subset).
- Final manual matrix (see Verification).

**Step 7 (small, recommended)**: Add a pure helper (no LLM) in engine.py:
```python
def get_unknown_attributes_from_audit(audit_log: list[str]) -> list[str]:
    """Extract attribute names mentioned in 'classified ... unknown' lines. Pure, for future log-mining refresh jobs."""
    ...
```
Wire a call or just leave as a TODO comment if time. Not required for Phase 1 success.

## Verification (End-to-End + Regression)
Cursor must run these (smoke default per WORKFLOW; full only for the graph tests). Grok will re-run independently on review.

**Automated (must be green):**
- `uv run pytest -m smoke -q` (all existing + new classify/supervisor smoke tests).
- `uv run pytest -m full -q -k "non_core or query_non_core or supervisor_agent"` (exercises real run_query + temp fixture + classification in full path).
- `uv run ruff check` on every file listed in the structure section.

**Manual hot-path (zero LLM, fast lookup, correct metadata):**
- Core only: `uv run mycelium query --person-key "Nichanan Kesonpat"` → response normal, debug has no (or empty) classifications, audit has only the two original supervisor lines.
- Known non-core: `uv run mycelium query --person-key "Nichanan Kesonpat" --attributes email` → still "we're still researching email.", but:
  - audit_log contains `Supervisor: classified 'email' -> category=contact, agent=contact_specialist, confidence=0.95`
  - final response.debug contains `classifications=` (or the key) with the full ClassificationResult for email.
  - (If you inspect the graph result before response extraction, state.classifications has the dict.)
- Another known: `--attributes spouse` → category=relationships.
- Unknown: `--attributes foo_bar_baz` → category=unknown, confidence=0.0 in the metadata, no LLM call (query still succeeds with the generic researching message).
- Ambiguous name + attr (regression): `uv run mycelium query --person-key "Kevin Zhang" --attributes x_handle` → 2 results, both have the classification metadata in debug, num_matches=2 etc. (Kevin Zhang fix must not regress).
- MCP path (same as CLI): `uv run python -c '
import json
from mycelium_mcp.server import query_person
print(query_person(json.dumps({"person_key": "Nichanan Kesonpat", "requested_attributes": ["linkedin", "spouse", "weird"]})))
'`

**Test isolation & cache behaviors:**
- In a temp dir or by env: `MYCELIUM_CATEGORIES_PATH=/tmp/test-cat-$$.json uv run python -c 'from agents.classification import get_category_tree, reset_category_tree; reset...; print(get().classify("email").category)'` → works, writes the seed json to that path.
- Delete the committed data/categories.json (or move aside), `uv run mycelium query --attributes email ...` → still succeeds (falls back to _SEED_CATEGORIES constant, may rewrite the file). Restore the committed json after.
- Full test fixture uses its own MYCELIUM_CATEGORIES_PATH in tmp; no pollution of source data/ or checkpoints.

**Off-path LLM refresh (manual, with key; mock in tests):**
- With OPENAI_API_KEY in env: `uv run python -c '
from agents.classification.engine import get_category_tree, reset_category_tree
reset_category_tree()
t = get_category_tree()
print(t.refresh_from_llm(["kids", "net_worth"]))
print(t.classify("kids"))
'`
  - Should add or map the new attrs, update last_updated + model_used in the (temp or real) json, subsequent classify sees it.
- Smoke test for refresh exercises only the non-LLM parts (early return, change dict shape, conservative filter) via mock or by calling internal merge if extracted, or just the "already known" path.
- Grep enforcement (run in step 5 and final): only classification/engine.py may contain "refresh_from_llm", "ChatOpenAI", "with_structured_output" related to classification.

**No hot-path LLM guarantee:**
- After all changes: `git grep -n "ChatOpenAI\|refresh_from_llm\|langchain.*chat\|invoke.*llm" -- src/agents/supervisor.py src/agents/core_data.py src/graphs/ src/mycelium_mcp/ src/main.py src/models/ | cat`
  - Expected: zero matches outside the classification/ tree (and inside only inside the refresh method and its tests).

**Observability / Studio / state:**
- classifications list appears in the graph state (visible in LangSmith Studio state inspector for a non-core query).
- audit_log and response.debug contain human-readable classification info for the requested non-core attrs.

**Lint + hygiene:**
- ruff clean on touched files.
- No changes outside the explicit scope list.
- Committed data/categories.json is valid JSON + roundtrips through CategoryTreeData.model_validate.

**After Cursor delivers:**
- Read `prompts/cursor/done/<the-task>/output.md` + any diffs.
- Re-run the full verification matrix above (smoke + key full + manual queries + grep + delete-json reseed).
- Write `review.md` with findings + any follow-ups.
- Only then commit (per prior pattern).

**Success criteria for Phase 1 (from this plan + v1.md):**
- Fast in-memory classify by attr name, returns category/assigned_agent/description/confidence.
- Unknown → clear "unknown" result, confidence 0, no LLM, query still succeeds.
- Persistent JSON at data/categories.json (with the seed + metadata).
- LLM refresh is completely separate, conservative, never on any query hot path.
- Supervisor injects the metadata with **minimal** code change; everything still routes through core_data; public behavior for core + non-core messages unchanged.
- Tests (smoke + full) + manual matrix all green.
- Ready for Phase 2 (supervisor can now *use* the category to pick real routes or trigger creation).

This plan is self-contained, references the authoritative `docs/plans/supervisor-intelligence-v1.md`, is scoped exactly to Phase 1 (Classification Engine only), follows all project conventions (WORKFLOW, architecture.md, smoke policy, reset singletons, env paths, Pydantic, explicit code), and gives Cursor 7 small reviewable steps with exact commands and scope. Ready for exit_plan_mode + user approval before any Cursor prompt is created or code touched.