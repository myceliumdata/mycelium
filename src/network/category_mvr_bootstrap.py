"""Ensure ``categories.json`` maps MVR bind fields for Program 2 unified writes."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from agents.classification.models import Category, CategoryTreeData
from network.paths import NetworkPaths, framework_root

CRM_MVR_FIELD_CATEGORY: dict[str, str] = {
    "name": "demographic",
    "employer": "professional",
}

_MINIMAL_MVR_CATEGORIES: dict[str, tuple[str, str]] = {
    "demographic": (
        "Demographic attributes including display name",
        "demographic_specialist",
    ),
    "professional": (
        "Professional attributes including current employer",
        "professional_specialist",
    ),
}


def sample_categories_path() -> Path:
    primary = framework_root() / "docs" / "examples" / "sample-categories.json"
    if primary.is_file():
        return primary
    return Path(__file__).resolve().parents[2] / "docs" / "examples" / "sample-categories.json"


def categories_map_mvr_fields(categories_path: Any) -> bool:
    if not categories_path.is_file():
        return False
    try:
        data = json.loads(categories_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    attr_map = data.get("attribute_map") if isinstance(data, dict) else None
    if not isinstance(attr_map, dict):
        return False
    return bool(attr_map.get("name") and attr_map.get("employer"))


def ensure_categories_for_mvr_bind(paths: NetworkPaths) -> None:
    """Ensure MVR bind fields are mapped; copy sample or merge into existing tree."""
    from agents.classification import get_category_tree, reset_category_tree

    paths.categories_path.parent.mkdir(parents=True, exist_ok=True)
    if not categories_map_mvr_fields(paths.categories_path):
        if paths.categories_path.is_file():
            try:
                raw = json.loads(paths.categories_path.read_text(encoding="utf-8"))
                tree = CategoryTreeData.model_validate(raw)
                updated = ensure_mvr_fields_in_category_tree(tree)
                paths.categories_path.write_text(
                    updated.model_dump_json(indent=2) + "\n",
                    encoding="utf-8",
                )
            except (OSError, json.JSONDecodeError, ValueError):
                _copy_sample_categories(paths.categories_path)
        else:
            _copy_sample_categories(paths.categories_path)
    reset_category_tree()
    get_category_tree()


def _copy_sample_categories(categories_path: Path) -> None:
    sample = sample_categories_path()
    if not sample.is_file():
        msg = "categories.json missing MVR attribute_map and no sample template"
        raise ValueError(msg)
    shutil.copy(sample, categories_path)


def ensure_mvr_fields_in_category_tree(tree: CategoryTreeData) -> CategoryTreeData:
    """Merge CRM MVR bind fields into ontology ``attribute_map`` when absent."""
    updated = tree.model_copy(deep=True)
    for field, category_name in CRM_MVR_FIELD_CATEGORY.items():
        key = field.strip().lower()
        if key in updated.attribute_map:
            continue
        if category_name not in updated.categories:
            desc, agent = _MINIMAL_MVR_CATEGORIES[category_name]
            updated.categories[category_name] = Category(
                description=desc,
                assigned_agent=agent,
                examples=[key],
            )
        updated.attribute_map[key] = category_name
        cat = updated.categories[category_name]
        if key not in cat.examples:
            cat.examples = [key, *cat.examples]
    return updated
