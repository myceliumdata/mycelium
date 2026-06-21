"""Assertion vocabulary for live gate scenario checks."""

from __future__ import annotations

import math
import os
import re
from pathlib import Path
from typing import Any


class AssertionErrorDetail(Exception):
    """Raised when a scenario assertion fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def _resolve_path(obj: Any, path: str) -> Any:
    """Resolve dotted / bracket paths like results[0].name or quote.quote_id."""
    if not path:
        return obj
    parts = re.split(r"\.|\[|\]", path)
    parts = [part for part in parts if part != ""]
    current = obj
    for part in parts:
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return current


def _coerce_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def missing_env_vars(names: list[str]) -> list[str]:
    missing: list[str] = []
    for name in names:
        if not str(os.getenv(name, "")).strip():
            missing.append(name)
    return missing


def check_assertions(
    response: Any,
    *,
    public: dict[str, Any],
    assertions: dict[str, Any],
    context: dict[str, Any],
    network_root: Path | None = None,
) -> list[str]:
    """Return list of failure messages (empty when all pass)."""
    failures: list[str] = []

    if "outcome" in assertions:
        expected = assertions["outcome"]
        actual = getattr(response, "outcome", public.get("outcome"))
        if actual != expected:
            failures.append(f"outcome: expected {expected!r}, got {actual!r}")

    if "total_matches" in assertions:
        expected_raw = assertions["total_matches"]
        expected = int(expected_raw) if not isinstance(expected_raw, int) else expected_raw
        actual = getattr(response, "total_matches", public.get("total_matches"))
        if actual != expected:
            failures.append(
                f"total_matches: expected {expected!r}, got {actual!r}",
            )

    if assertions.get("total_matches_gte") is not None:
        actual = getattr(response, "total_matches", public.get("total_matches"))
        minimum = assertions["total_matches_gte"]
        if actual is None or actual < minimum:
            failures.append(
                f"total_matches: expected >= {minimum}, got {actual!r}",
            )

    if assertions.get("results_empty"):
        results = public.get("results") or getattr(response, "results", None) or []
        if results:
            failures.append(f"results: expected empty, got {len(results)} row(s)")

    if assertions.get("results_count") is not None:
        results = public.get("results") or getattr(response, "results", None) or []
        expected_raw = assertions["results_count"]
        expected = int(expected_raw) if not isinstance(expected_raw, int) else expected_raw
        if len(results) != expected:
            failures.append(
                f"results_count: expected {expected}, got {len(results)}",
            )

    if assertions.get("delivery_present"):
        delivery = getattr(response, "delivery", None) or public.get("delivery")
        if not delivery:
            failures.append("delivery: expected present, got none")

    if assertions.get("create_on_deliver") is True:
        delivery = getattr(response, "delivery", None) or public.get("delivery") or {}
        if isinstance(delivery, dict):
            flag = delivery.get("create_on_deliver")
        else:
            flag = getattr(delivery, "create_on_deliver", None)
        if not flag:
            failures.append("delivery.create_on_deliver: expected true")

    if assertions.get("create_on_deliver") is False:
        delivery = getattr(response, "delivery", None) or public.get("delivery") or {}
        if isinstance(delivery, dict):
            flag = delivery.get("create_on_deliver")
        else:
            flag = getattr(delivery, "create_on_deliver", None)
        if flag:
            failures.append("delivery.create_on_deliver: expected false/absent")

    if "quote_present" in assertions:
        quote = getattr(response, "quote", None) or public.get("quote")
        if assertions["quote_present"] and not quote:
            failures.append("quote: expected present, got none")
        if assertions["quote_present"] is False and quote:
            failures.append("quote: expected absent")

    for key, expected in (assertions.get("path") or {}).items():
        actual = _resolve_path(public, key)
        if isinstance(expected, dict):
            if "approx" in expected:
                actual_num = _coerce_number(actual)
                target = float(expected["approx"])
                tolerance = float(expected.get("tolerance", 0.01))
                if actual_num is None or not math.isclose(
                    actual_num,
                    target,
                    rel_tol=0,
                    abs_tol=tolerance,
                ):
                    failures.append(
                        f"path {key}: expected ≈ {target} (±{tolerance}), got {actual!r}",
                    )
            elif "equals" in expected:
                if str(actual) != str(expected["equals"]):
                    failures.append(
                        f"path {key}: expected {expected['equals']!r}, got {actual!r}",
                    )
            elif "contains" in expected:
                if expected["contains"] not in str(actual):
                    failures.append(
                        f"path {key}: expected to contain {expected['contains']!r}, got {actual!r}",
                    )
            elif "one_of" in expected:
                options = expected["one_of"]
                if not isinstance(options, list) or not options:
                    failures.append(f"path {key}: one_of must be a non-empty list")
                elif str(actual) not in {str(option) for option in options}:
                    failures.append(
                        f"path {key}: expected one of {options!r}, got {actual!r}",
                    )
            elif "truthy" in expected and expected["truthy"]:
                if not actual:
                    failures.append(f"path {key}: expected truthy, got {actual!r}")
        else:
            if str(actual) != str(expected):
                failures.append(f"path {key}: expected {expected!r}, got {actual!r}")

    if assertions.get("suggestion_lookup"):
        suggestions = getattr(response, "suggestions", None) or public.get(
            "suggestions",
        )
        expected_lookup = assertions["suggestion_lookup"]
        if not suggestions:
            failures.append("suggestions: expected at least one")
        else:
            first = suggestions[0]
            if isinstance(first, dict):
                actual_lookup = first.get("suggested_lookup")
            else:
                actual_lookup = getattr(first, "suggested_lookup", None)
            if actual_lookup != expected_lookup:
                failures.append(
                    f"suggestion_lookup: expected {expected_lookup!r}, got {actual_lookup!r}",
                )

    if assertions.get("registry_entity_count") is not None:
        from agents.entity_registry import get_entity_registry

        expected_raw = assertions["registry_entity_count"]
        if isinstance(expected_raw, str) and expected_raw.isdigit():
            expected = int(expected_raw)
        else:
            expected = int(expected_raw)
        actual = get_entity_registry().entity_count()
        if actual != expected:
            failures.append(
                f"registry_entity_count: expected {expected}, got {actual}",
            )

    if assertions.get("file_exists"):
        if network_root is None:
            failures.append("file_exists: network_root not configured")
        else:
            rel = assertions["file_exists"]
            path = network_root / rel
            if not path.is_file():
                failures.append(f"file_exists: missing {rel}")

    if assertions.get("registry_entity_count_gte") is not None:
        from agents.entity_registry import get_entity_registry

        minimum = int(assertions["registry_entity_count_gte"])
        actual = get_entity_registry().entity_count()
        if actual < minimum:
            failures.append(
                f"registry_entity_count: expected >= {minimum}, got {actual}",
            )

    if assertions.get("same_timestamp_as"):
        ref_id = assertions["same_timestamp_as"]
        ref = context.get(ref_id)
        if not ref:
            failures.append(f"same_timestamp_as: missing context for {ref_id!r}")
        else:
            ref_ts = ref.get("provenance_timestamp")
            prov = public.get("provenance") or {}
            try:
                attrs = prov["entities"][0]["attributes"]
                current_ts = next(iter(attrs.values()))["versions"][0]["timestamp"]
            except (KeyError, IndexError, StopIteration, TypeError):
                current_ts = None
            if ref_ts and current_ts and ref_ts != current_ts:
                failures.append(
                    f"provenance timestamp: expected {ref_ts!r}, got {current_ts!r}",
                )

    if assertions.get("intent_slug"):
        expected_slug = assertions["intent_slug"]
        prov = public.get("provenance") or {}
        try:
            attrs = prov["entities"][0]["attributes"]
            actual_slug = None
            for attr_data in attrs.values():
                versions = attr_data.get("versions") or []
                if versions:
                    actual_slug = versions[0].get("parameters", {}).get("intent_slug")
                    if actual_slug:
                        break
        except (KeyError, IndexError, TypeError):
            actual_slug = None
        if actual_slug != expected_slug:
            failures.append(
                f"intent_slug: expected {expected_slug!r}, got {actual_slug!r}",
            )

    return failures


def extract_provenance_timestamp(public: dict[str, Any], attribute: str) -> str | None:
    prov = public.get("provenance") or {}
    try:
        return prov["entities"][0]["attributes"][attribute]["versions"][0]["timestamp"]
    except (KeyError, IndexError, TypeError):
        return None
