"""Enable sibling imports for dynamically loaded pack specialist modules."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_LOADER_KEY = "_baseball_pack_specialist_loader"


def bootstrap(caller_file: str) -> None:
    pack_dir = Path(caller_file).resolve().parent
    pack_dir_s = str(pack_dir)
    if pack_dir_s not in sys.path:
        sys.path.insert(0, pack_dir_s)
    if _LOADER_KEY in sys.modules:
        return
    loader_path = pack_dir / "specialist_loader.py"
    spec = importlib.util.spec_from_file_location(_LOADER_KEY, loader_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load specialist_loader from {loader_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[_LOADER_KEY] = mod
    spec.loader.exec_module(mod)