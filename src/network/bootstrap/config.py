"""Parse ``network.json`` bootstrap handler configuration."""

from __future__ import annotations

import json
from dataclasses import dataclass

from network.paths import NetworkPaths

_EXAMPLE_BOOTSTRAP = (
    '{"bootstrap": {"module": "network.bootstrap.handlers.default_seed", '
    '"handler": "DefaultSeedHandler"}}'
)


@dataclass(frozen=True)
class BootstrapConfig:
    """Resolved bootstrap handler declaration from ``network.json``."""

    module: str
    class_name: str


def load_bootstrap_config(paths: NetworkPaths) -> BootstrapConfig:
    """Load and validate the ``bootstrap`` block from ``network.json``."""
    manifest_path = paths.root / "network.json"
    if not manifest_path.is_file():
        raise ValueError(
            f"{manifest_path}: network manifest required for bootstrap "
            "(add network.json with a bootstrap block)",
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid network.json: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ValueError("network.json must be a JSON object")

    bootstrap = manifest.get("bootstrap")
    if not isinstance(bootstrap, dict):
        raise ValueError(
            f"{manifest_path}: missing required 'bootstrap' object "
            f"(e.g. {_EXAMPLE_BOOTSTRAP})",
        )

    module_raw = bootstrap.get("module")
    handler_raw = bootstrap.get("handler")
    module = str(module_raw).strip() if isinstance(module_raw, str) else ""
    class_name = str(handler_raw).strip() if isinstance(handler_raw, str) else ""

    if not module:
        raise ValueError(
            "network.json bootstrap.module is required "
            '(e.g. "network.bootstrap.handlers.default_seed" or a pack module '
            "under network_root)",
        )
    if not class_name:
        raise ValueError(
            "network.json bootstrap.handler is required "
            "(handler class name, e.g. DefaultSeedHandler)",
        )
    return BootstrapConfig(module=module, class_name=class_name)
