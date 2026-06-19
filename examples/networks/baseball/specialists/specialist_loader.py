"""Dynamic import helper for baseball pack specialist modules."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def load_sibling(module_name: str) -> ModuleType:
    """Load a sibling ``.py`` module from the network specialists directory."""
    key = f"_baseball_pack_{module_name}"
    if key in sys.modules:
        return sys.modules[key]
    path = Path(__file__).resolve().parent / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(key, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load pack module {module_name} from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


def load_warehouse_resolve() -> ModuleType:
    """Load the pack warehouse resolver module."""
    return load_sibling("warehouse_resolve")


def load_derive_resolve() -> ModuleType:
    """Load the pack derive orchestration module."""
    return load_sibling("derive_resolve")
