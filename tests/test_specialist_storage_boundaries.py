"""Guard: framework code must not import specialist storage internals."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
_SPECIALISTS_ROOT = _SRC / "agents" / "specialists"
_FORBIDDEN_FIELD_MODULES = frozenset(
    {
        "agents.specialists.fields",
        "agents.specialist_fields",
    },
)


def _python_files_outside_specialists() -> list[Path]:
    files: list[Path] = []
    for path in _SRC.rglob("*.py"):
        if path.is_relative_to(_SPECIALISTS_ROOT):
            continue
        files.append(path)
    return files


def _forbidden_specialist_imports(tree: ast.AST) -> list[str]:
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module in _FORBIDDEN_FIELD_MODULES:
                hits.append(module)
            if module == "agents.specialists.base":
                for alias in node.names:
                    if alias.name == "SpecialistStorage":
                        hits.append("agents.specialists.base.SpecialistStorage")
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in _FORBIDDEN_FIELD_MODULES:
                    hits.append(alias.name)
    return hits


@pytest.mark.parametrize("path", _python_files_outside_specialists(), ids=lambda p: str(p.relative_to(_SRC.parent)))
def test_no_specialist_storage_import_outside_specialists(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    hits = _forbidden_specialist_imports(tree)
    assert not hits, f"{path} imports specialist internals: {hits}"
