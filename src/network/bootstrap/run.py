"""Network bootstrap orchestration."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import agents.entity_registry as entity_registry_module
from agents.entity_registry import reset_entity_registry
from network.bootstrap.context import BootstrapContext, BootstrapResult
from network.bootstrap.handlers.resolve import resolve_handler
from network.bootstrap.progress import BootstrapProgress, make_bootstrap_progress
from network.category_mvr_bootstrap import ensure_categories_for_mvr_bind
from network.paths import NetworkPaths, apply_network_paths


def _read_guide(paths: NetworkPaths) -> str | None:
    guide_path = paths.root / "guide.md"
    if not guide_path.is_file():
        return None
    try:
        return guide_path.read_text(encoding="utf-8")
    except OSError:
        return None


@contextmanager
def _bootstrap_deferred_with_progress(
    progress: BootstrapProgress | None,
) -> Iterator[None]:
    entity_registry_module._bootstrap_deferred_depth += 1
    try:
        yield
    finally:
        entity_registry_module._bootstrap_deferred_depth -= 1
        if entity_registry_module._bootstrap_deferred_depth == 0:
            if progress is not None:
                progress.cleaning_up()
            for registry in entity_registry_module._registry.values():
                registry.commit_deferred_save()


def run_network_bootstrap(
    paths: NetworkPaths,
    *,
    progress: BootstrapProgress | None = None,
) -> BootstrapResult:
    """Formal network bootstrap phase: paths, categories, registry reset, handler."""
    apply_network_paths(paths)
    ensure_categories_for_mvr_bind(paths)
    reset_entity_registry()
    reporter = progress if progress is not None else make_bootstrap_progress()
    ctx = BootstrapContext(
        paths=paths,
        guide_text=_read_guide(paths),
        progress=reporter,
    )
    handler = resolve_handler(paths)
    with _bootstrap_deferred_with_progress(reporter):
        result = handler.run(ctx)
    if reporter is not None:
        reporter.done()
    return result
