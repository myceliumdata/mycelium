"""Resolve network bootstrap handler (default or override)."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Callable

from network.bootstrap.context import BootstrapContext, BootstrapResult
from network.bootstrap.handlers.default_seed import DefaultSeedHandler
from network.bootstrap.handlers.protocol import BootstrapHandler
from network.paths import NetworkPaths


class _OverrideHandler:
    """Wrap a network ``bootstrap_specialist.py`` module."""

    def __init__(self, fn: Callable[[BootstrapContext], BootstrapResult], path: Path) -> None:
        self._fn = fn
        self._path = path

    def run(self, ctx: BootstrapContext) -> BootstrapResult:
        try:
            return self._fn(ctx)
        except Exception as exc:
            raise ValueError(
                f"Bootstrap override failed ({self._path}): {exc}",
            ) from exc


def _load_override_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(
        "network_bootstrap_override",
        str(path),
    )
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load bootstrap override from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def resolve_handler(paths: NetworkPaths) -> BootstrapHandler:
    """Return default seed handler or network override when present."""
    override_path = paths.specialists_dir / "bootstrap_specialist.py"
    if not override_path.is_file():
        return DefaultSeedHandler()
    try:
        mod = _load_override_module(override_path)
    except Exception as exc:
        raise ValueError(
            f"Cannot import bootstrap override at {override_path}: {exc}",
        ) from exc
    fn = getattr(mod, "run_bootstrap", None)
    if not callable(fn):
        raise ValueError(
            f"{override_path}: must define callable run_bootstrap(ctx: BootstrapContext)",
        )
    return _OverrideHandler(fn, override_path)
