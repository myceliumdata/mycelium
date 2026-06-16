"""Ensure ``categories.json`` maps MVR bind fields for Program 2 unified writes.

``CRM_MVR_FIELD_CATEGORY`` is a **bootstrap/merge reference only** for example
networks and ``network create`` when LLM ontologies omit MVR mappings. Runtime
bind-field ownership is always resolved from ``categories.json`` ``attribute_map``
via ``resolve_attribute_owner`` — never from this hardcoded map.
"""

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
    "team": "professional",
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


def _required_bind_fields(paths: NetworkPaths) -> set[str]:
    from network.mvr import load_mvr_config

    config = load_mvr_config(paths=paths)
    fields: set[str] = set()
    for grain in config.grains.values():
        for field in grain.bind_fields:
            key = field.strip().lower()
            if key:
                fields.add(key)
    return fields


def categories_map_mvr_fields(
    categories_path: Any,
    required_fields: set[str] | None = None,
) -> bool:
    if not categories_path.is_file():
        return False
    try:
        data = json.loads(categories_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    attr_map = data.get("attribute_map") if isinstance(data, dict) else None
    if not isinstance(attr_map, dict):
        return False
    needed = required_fields if required_fields is not None else set(CRM_MVR_FIELD_CATEGORY)
    return bool(needed) and all(attr_map.get(field) for field in needed)


def ensure_categories_for_mvr_bind(paths: NetworkPaths) -> None:
    """Ensure MVR bind fields are mapped; copy sample or merge into existing tree."""
    from agents.classification import get_category_tree, reset_category_tree

    required_fields = _required_bind_fields(paths)
    paths.categories_path.parent.mkdir(parents=True, exist_ok=True)
    if not categories_map_mvr_fields(paths.categories_path, required_fields):
        if paths.categories_path.is_file():
            try:
                raw = json.loads(paths.categories_path.read_text(encoding="utf-8"))
                tree = CategoryTreeData.model_validate(raw)
                updated = ensure_mvr_fields_in_category_tree(tree, required_fields)
                paths.categories_path.write_text(
                    updated.model_dump_json(indent=2) + "\n",
                    encoding="utf-8",
                )
            except (OSError, json.JSONDecodeError, ValueError):
                _copy_sample_categories(paths.categories_path)
                _merge_required_bind_fields(paths, required_fields)
        else:
            _copy_sample_categories(paths.categories_path)
            _merge_required_bind_fields(paths, required_fields)
    reset_category_tree()
    get_category_tree()


def _copy_sample_categories(categories_path: Path) -> None:
    sample = sample_categories_path()
    if not sample.is_file():
        msg = "categories.json missing MVR attribute_map and no sample template"
        raise ValueError(msg)
    shutil.copy(sample, categories_path)


def _merge_required_bind_fields(paths: NetworkPaths, required_fields: set[str]) -> None:
    raw = json.loads(paths.categories_path.read_text(encoding="utf-8"))
    tree = CategoryTreeData.model_validate(raw)
    updated = ensure_mvr_fields_in_category_tree(tree, required_fields)
    paths.categories_path.write_text(
        updated.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )


def ensure_mvr_fields_in_category_tree(
    tree: CategoryTreeData,
    bind_fields: set[str] | None = None,
) -> CategoryTreeData:
    """Merge manifest MVR bind fields into ontology ``attribute_map`` when absent."""
    updated = tree.model_copy(deep=True)
    fields_to_map = bind_fields if bind_fields is not None else set(CRM_MVR_FIELD_CATEGORY)
    for field in sorted(fields_to_map):
        key = field.strip().lower()
        if not key or key in updated.attribute_map:
            continue
        category_name = CRM_MVR_FIELD_CATEGORY.get(key, "professional")
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
