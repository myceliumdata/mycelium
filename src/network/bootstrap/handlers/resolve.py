"""Resolve network bootstrap handler from ``network.json``."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

from network.bootstrap.config import BootstrapConfig, load_bootstrap_config
from network.bootstrap.handlers.protocol import BootstrapHandler
from network.paths import NetworkPaths


def _instantiate_handler(
    mod: object,
    *,
    module_name: str,
    class_name: str,
    load_context: str,
) -> BootstrapHandler:
    cls = getattr(mod, class_name, None)
    if cls is None:
        raise ValueError(
            f"Bootstrap {load_context} has no class {class_name!r}",
        )
    try:
        handler = cls()
    except Exception as exc:
        raise ValueError(
            f"Cannot instantiate bootstrap handler {class_name!r} "
            f"from {module_name!r}: {exc}",
        ) from exc
    run_fn = getattr(handler, "run", None)
    if not callable(run_fn):
        raise ValueError(
            f"Bootstrap handler {class_name!r} must implement run(ctx)",
        )
    return handler


def _load_framework_handler(config: BootstrapConfig) -> BootstrapHandler:
    try:
        mod = importlib.import_module(config.module)
    except Exception as exc:
        raise ValueError(
            f"Cannot import bootstrap framework module {config.module!r}: {exc}",
        ) from exc
    return _instantiate_handler(
        mod,
        module_name=config.module,
        class_name=config.class_name,
        load_context=f"framework module {config.module!r}",
    )


def _load_pack_handler(
    paths: NetworkPaths,
    config: BootstrapConfig,
) -> BootstrapHandler:
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

    return _instantiate_handler(
        mod,
        module_name=config.module,
        class_name=config.class_name,
        load_context=f"pack module {config.module!r}",
    )


def resolve_handler(paths: NetworkPaths) -> BootstrapHandler:
    """Instantiate the bootstrap handler declared in ``network.json``."""
    config = load_bootstrap_config(paths)
    if config.module.startswith("network."):
        return _load_framework_handler(config)
    return _load_pack_handler(paths, config)
