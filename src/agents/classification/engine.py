"""Category tree cache and classify() — Phase 1 (see docs/plans/classification-engine-phase1.md).

Known attributes: fast in-memory lookup (no LLM).
First-time unknown attributes: optional on-demand LLM proposal (lazy ChatOpenAI), then cache.
Garbage/nonsense attrs are rejected by prompt + logic and cached as unknown to avoid repeat LLM calls.
refresh_from_llm remains the batch/admin off-path for evolving the tree.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import Category, CategoryProposal, CategoryProposals, CategoryTreeData, ClassificationResult

# LLM imports/calls live only in this module (_llm_propose_for_attributes, refresh_from_llm).
# classify() invokes the LLM only for first-time unknowns (not for known-map hits).

_CONFIDENCE_THRESHOLD = 0.7
_UNKNOWN_MAP_SENTINEL = "unknown"


def _default_categories_path() -> Path:
    """Follow storage/core.py + graphs/core.py env convention."""
    return Path(os.getenv("MYCELIUM_CATEGORIES_PATH", "data/categories.json"))


# Embedded canonical taxonomy (written to data/categories.json on first use; file is gitignored).
_SEED_CATEGORIES: dict[str, Any] = {
    "version": "1.0",
    "last_updated": "2026-06-03T00:00:00+00:00",
    "model_used": "",
    "categories": {
        "contact": {
            "description": "Direct ways to reach the person (email, phone, physical).",
            "assigned_agent": "contact_specialist",
            "examples": ["email", "phone", "mobile", "address", "website"],
        },
        "social": {
            "description": "Social and professional profiles and handles.",
            "assigned_agent": "social_specialist",
            "examples": ["linkedin", "x_handle", "twitter", "facebook", "instagram"],
        },
        "relationships": {
            "description": "Personal and family relationships.",
            "assigned_agent": "relationships_specialist",
            "examples": ["spouse", "partner", "family", "children", "parents"],
        },
        "demographic": {
            "description": "Basic personal characteristics and background.",
            "assigned_agent": "demographic_specialist",
            "examples": ["age", "birthday", "gender", "nationality", "location"],
        },
        "professional": {
            "description": "Career, education, and investment-related details.",
            "assigned_agent": "professional_specialist",
            "examples": ["title", "bio", "education", "previous_firms", "investments"],
        },
        "financial": {
            "description": "Net worth, compensation, investments, and other financial attributes.",
            "assigned_agent": "financial_specialist",
            "examples": ["net_worth", "salary", "compensation", "portfolio"],
        },
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
        "investments": "professional",
        "net_worth": "financial",
        "salary": "financial",
        "compensation": "financial",
        "portfolio": "financial",
    },
}


def _build_llm_classification_prompt(
    attrs_to_consider: list[str],
    current_cat_names: list[str],
    current_map_keys: list[str],
) -> str:
    """Shared prompt for refresh_from_llm and on-demand classify() unknowns."""
    sample_keys = current_map_keys[:30]
    return f"""You are maintaining a small, stable taxonomy for personal/career data attributes used by an AI data system.

Current top-level categories: {current_cat_names}

Existing attribute -> category mappings (do not re-propose these): {sample_keys} ...

For each of the following new or unknown attributes, decide:
- The best existing category, or propose a new short category name (lowercase, no spaces, e.g. "financial", "education").
- A one-sentence description for the category (only if new).
- A sensible future "assigned_agent" name (e.g. "financial_specialist" or "pending_<cat>").
- Your confidence (0.0-1.0) that this is the right long-term home for the attribute.

IMPORTANT — garbage / nonsense: For random strings, obvious typos, placeholder names, or invalid attribute names
(e.g. "foo_bar_baz", "asdf123", "weird", "xxx", strings with no real-world meaning as a person data field),
return category="unknown" with high confidence (>= 0.8) that it is NOT classifiable. Do NOT invent categories for garbage.

Return ONLY a list of proposals (one per attribute, even if empty). Be conservative: if unsure, use category="unknown" or confidence < 0.7.

Attributes to classify: {attrs_to_consider}
"""


def _unknown_result(attribute: str) -> ClassificationResult:
    return ClassificationResult(
        attribute=attribute,
        category="unknown",
        assigned_agent=None,
        description="No classification available for this attribute.",
        confidence=0.0,
    )


class CategoryTree:
    """In-memory category tree with persistent JSON cache.

    classify(): known attrs are pure dict lookup. First-time unknowns may call the LLM once,
    then cache (including garbage mapped to the unknown sentinel).
    """

    def __init__(self, cache_path: Path | None = None) -> None:
        self.cache_path = cache_path or _default_categories_path()
        self._data: CategoryTreeData | None = None
        self._load()

    def _load(self) -> None:
        if self.cache_path.exists():
            raw = json.loads(self.cache_path.read_text(encoding="utf-8"))
            self._data = CategoryTreeData.model_validate(raw)
        else:
            self._data = self._create_seed()
            self._save()

    def _save(self) -> None:
        """Atomic write via temp file + replace (reduces partial-write risk)."""
        if self._data is None:
            return
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        payload = self._data.model_dump_json(indent=2)
        fd, tmp_path = tempfile.mkstemp(
            dir=self.cache_path.parent,
            suffix=".json.tmp",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
            os.replace(tmp_path, self.cache_path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def _create_seed(self) -> CategoryTreeData:
        return CategoryTreeData.model_validate(_SEED_CATEGORIES)

    def reload(self) -> None:
        self._load()

    def _result_for_mapped(
        self,
        attribute: str,
        cat_name: str,
        *,
        confidence: float = 0.95,
    ) -> ClassificationResult:
        if cat_name == _UNKNOWN_MAP_SENTINEL:
            return _unknown_result(attribute)
        cat = self._data.categories[cat_name]
        return ClassificationResult(
            attribute=attribute,
            category=cat_name,
            assigned_agent=cat.assigned_agent,
            description=cat.description,
            confidence=confidence,
        )

    def _cache_as_unknown(self, normalized: str) -> None:
        self._data.attribute_map[normalized] = _UNKNOWN_MAP_SENTINEL
        self._data.last_updated = datetime.now(timezone.utc)
        self._save()
        self._load()

    def _apply_proposal(self, proposal: CategoryProposal) -> bool:
        """Merge one proposal if it passes conservative rules. Returns True if applied."""
        if self._data is None:
            self._load()
        attr = proposal.attribute.strip().lower()
        cat_name = proposal.category.strip().lower().replace(" ", "_")
        conf = float(proposal.confidence or 0.0)
        if cat_name == _UNKNOWN_MAP_SENTINEL or conf < _CONFIDENCE_THRESHOLD:
            return False
        if cat_name not in self._data.categories:
            self._data.categories[cat_name] = Category(
                description=(proposal.description or f"Data related to {cat_name}."),
                assigned_agent=(proposal.assigned_agent or f"pending_{cat_name}"),
                examples=[attr],
            )
        self._data.attribute_map[attr] = cat_name
        return True

    def _llm_propose_for_attributes(
        self,
        attributes: list[str],
        llm: Any | None = None,
        model: str = "gpt-4o-mini",
    ) -> list[CategoryProposal]:
        """Lazy LLM call with structured CategoryProposals output (internal + tests via llm=).
        Returns the .proposals list.
        """
        if self._data is None:
            self._load()
        attrs_to_consider = [a.strip() for a in attributes if a.strip()]
        if not attrs_to_consider:
            return []

        if llm is None:
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(model=model, temperature=0.0)

        prompt = _build_llm_classification_prompt(
            attrs_to_consider,
            list(self._data.categories.keys()),
            list(self._data.attribute_map.keys()),
        )
        structured_llm = llm.with_structured_output(CategoryProposals)
        result = structured_llm.invoke(prompt)
        if isinstance(result, CategoryProposals):
            return result.proposals
        return result  # for compatibility with mocks that return list directly

    def _pick_proposal(
        self,
        proposals: list[CategoryProposal],
        normalized: str,
    ) -> CategoryProposal | None:
        for proposal in proposals:
            if proposal.attribute.strip().lower() == normalized:
                return proposal
        return proposals[0] if proposals else None

    def classify(self, attribute: str) -> ClassificationResult:
        """Lookup by normalized name; first-time unknowns may call LLM once, then cache."""
        if self._data is None:
            self._load()
        normalized = attribute.strip().lower()
        if normalized in self._data.attribute_map:
            cat_name = self._data.attribute_map[normalized]
            return self._result_for_mapped(attribute, cat_name)

        try:
            proposals = self._llm_propose_for_attributes([attribute])
        except Exception as e:
            import traceback
            print(f"[LLM classify error for {attribute}]: {type(e).__name__}: {e}", file=sys.stderr)
            traceback.print_exc()
            return _unknown_result(attribute)

        proposal = self._pick_proposal(proposals, normalized)
        if proposal is None:
            self._cache_as_unknown(normalized)
            return _unknown_result(attribute)

        if self._apply_proposal(proposal):
            self._data.last_updated = datetime.now(timezone.utc)
            self._save()
            self._load()
            cat_name = self._data.attribute_map[normalized]
            conf = min(float(proposal.confidence or 0.0), 0.95)
            return self._result_for_mapped(attribute, cat_name, confidence=conf)

        self._cache_as_unknown(normalized)
        return _unknown_result(attribute)

    def get_categories(self) -> dict[str, Category]:
        if self._data is None:
            self._load()
        return self._data.categories.copy()

    def refresh_from_llm(
        self,
        attributes: list[str],
        llm: Any | None = None,
        model: str = "gpt-4o-mini",
    ) -> dict[str, Any]:
        """Occasional / admin-only path. Never call from supervisor, core_data, or query entrypoints."""
        if self._data is None:
            self._load()

        current_map = self._data.attribute_map
        attrs_to_consider = [
            a.strip()
            for a in attributes
            if a.strip() and a.strip().lower() not in current_map
        ]

        if not attrs_to_consider:
            return {
                "added_categories": [],
                "updated_attributes": [],
                "skipped": [],
                "reason": "all already known",
            }

        proposals = self._llm_propose_for_attributes(
            attrs_to_consider,
            llm=llm,
            model=model,
        )

        changes: dict[str, Any] = {
            "added_categories": [],
            "updated_attributes": [],
            "skipped": [],
        }
        for proposal in proposals:
            attr = proposal.attribute.strip().lower()
            cat_name = proposal.category.strip().lower().replace(" ", "_")
            conf = float(proposal.confidence or 0.0)
            if cat_name == _UNKNOWN_MAP_SENTINEL or conf < _CONFIDENCE_THRESHOLD:
                changes["skipped"].append(attr)
                continue
            was_new_cat = cat_name not in self._data.categories
            if self._apply_proposal(proposal):
                if was_new_cat:
                    changes["added_categories"].append(cat_name)
                if attr not in changes["updated_attributes"]:
                    changes["updated_attributes"].append(attr)
            else:
                changes["skipped"].append(attr)

        self._data.last_updated = datetime.now(timezone.utc)
        self._data.model_used = model
        self._save()
        self._load()
        return changes


_category_tree: CategoryTree | None = None


def get_category_tree() -> CategoryTree:
    """Process-wide cached CategoryTree (lazy; respects MYCELIUM_CATEGORIES_PATH)."""
    global _category_tree
    if _category_tree is None:
        _category_tree = CategoryTree()
    return _category_tree


def reset_category_tree() -> None:
    """Clear the singleton (for tests + admin reload scenarios)."""
    global _category_tree
    _category_tree = None
