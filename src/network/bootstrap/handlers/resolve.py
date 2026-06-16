"""Resolve network bootstrap handler from ``network.json``."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Type

from network.bootstrap.config import BootstrapConfig, load_bootstrap_config
from network.bootstrap.handlers.default_seed import DefaultSeedHandler
from network.bootstrap.handlers.protocol import BootstrapHandler
from network.paths import NetworkPaths

BUILTIN_HANDLERS: dict[str, Type[BootstrapHandler]] = {
    "default_seed": DefaultSeedHandler,
}


def _load_pack_handler(
    paths: NetworkPaths,
    config: BootstrapConfig,
) -> BootstrapHandler:
    if not config.module or not config.class_name:
        raise ValueError("pack bootstrap config requires module and handler class name")

    module_path = paths.root / Path(*config.module.split(".")).with_suffix(".py")
    root = str(paths.root.resolve())
    inserted = False
    if root not in sys.path:
        sys.path.insert(0, root)
        inserted = True
    try:
        mod = importlib.import_module(config.module)
    except Exception as exc:
        hint = f" (expected file {module_path})" if not module_path.is_file() else ""
        raise ValueError(
            f"Cannot import bootstrap pack module {config.module!r} from {paths.root}{hint}: {exc}",
        ) from exc
    finally:
        if inserted:
            sys.path.remove(root)

    cls = getattr(mod, config.class_name, None)
    if cls is None:
        raise ValueError(
            f"Bootstrap pack module {config.module!r} has no class {config.class_name!r}",
        )
    try:
        handler = cls()
    except Exception as exc:
        raise ValueError(
            f"Cannot instantiate bootstrap handler {config.class_name!r} "
            f"from {config.module!r}: {exc}",
        ) from exc
    run_fn = getattr(handler, "run", None)
    if not callable(run_fn):
        raise ValueError(
            f"Bootstrap handler {config.class_name!r} must implement run(ctx)",
        )
    return handler


def resolve_handler(paths: NetworkPaths) -> BootstrapHandler:
    """Instantiate the bootstrap handler declared in ``network.json``."""
    config = load_bootstrap_config(paths)
    if config.builtin_key:
        return BUILTIN_HANDLERS[config.builtin_key]()
    return _load_pack_handler(paths, config)
