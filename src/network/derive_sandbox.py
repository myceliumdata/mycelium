"""Sandbox execution for LLM-generated warehouse derive functions."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from network.warehouse import query_warehouse


class DeriveSourceError(ValueError):
    """Raised when derive source is invalid or execution fails."""


_FORBIDDEN_CALLS = frozenset(
    {
        "open",
        "eval",
        "exec",
        "compile",
        "__import__",
        "getattr",
        "globals",
        "locals",
        "vars",
        "dir",
        "input",
        "help",
        "breakpoint",
        "exit",
        "quit",
    },
)


def validate_derive_source(source: str) -> None:
    """Reject derive code with imports or unsafe constructs."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise DeriveSourceError(str(exc)) from exc

    has_compute = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise DeriveSourceError("imports are not allowed in derive functions")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in _FORBIDDEN_CALLS:
                raise DeriveSourceError(f"forbidden call: {node.func.id}")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise DeriveSourceError("dunder attribute access is forbidden")
        if isinstance(node, ast.FunctionDef) and node.name == "compute":
            has_compute = True

    if not has_compute:
        raise DeriveSourceError(
            "derive source must define compute(player_id, warehouse)",
        )


def run_derive_function(
    source: str,
    *,
    player_id: str,
    warehouse: Path,
) -> str:
    """Execute validated derive source and return the string result."""
    validate_derive_source(source)
    namespace: dict[str, Any] = {
        "__builtins__": {
            "str": str,
            "int": int,
            "float": float,
            "round": round,
            "sum": sum,
            "len": len,
            "abs": abs,
            "ValueError": ValueError,
            "ZeroDivisionError": ZeroDivisionError,
            "TypeError": TypeError,
        },
        "Path": Path,
        "query_warehouse": query_warehouse,
    }
    exec(compile(source, "<derive>", "exec"), namespace)
    compute = namespace.get("compute")
    if not callable(compute):
        raise DeriveSourceError("compute function missing after exec")
    result = compute(player_id, warehouse)
    if result is None:
        raise DeriveSourceError("compute returned None")
    text = str(result).strip()
    if not text:
        raise DeriveSourceError("compute returned empty value")
    return text
