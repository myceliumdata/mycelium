"""Parse ``network.json`` bootstrap handler configuration."""

from __future__ import annotations

import json
from dataclasses import dataclass

from network.paths import NetworkPaths


@dataclass(frozen=True)
class BootstrapConfig:
    """Resolved bootstrap handler declaration from ``network.json``."""

    builtin_key: str | None = None
    module: str | None = None
    class_name: str | None = None


BUILTIN_HANDLER_KEYS = frozenset({"default_seed"})


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
            '(e.g. {"bootstrap": {"handler": "default_seed"}})',
        )

    handler_raw = bootstrap.get("handler")
    module_raw = bootstrap.get("module")
    handler = str(handler_raw).strip() if isinstance(handler_raw, str) else None
    module = str(module_raw).strip() if isinstance(module_raw, str) else None

    if module:
        if handler in BUILTIN_HANDLER_KEYS:
            raise ValueError(
                "network.json bootstrap: cannot combine built-in handler key "
                f"{handler!r} with module {module!r}",
            )
        if not handler:
            raise ValueError(
                "network.json bootstrap.module requires bootstrap.handler "
                "(handler class name for the pack module)",
            )
        return BootstrapConfig(module=module, class_name=handler)

    if not handler:
        raise ValueError(
            "network.json bootstrap.handler is required "
            '(built-in key, e.g. "default_seed", or use module+handler for pack)',
        )
    if handler not in BUILTIN_HANDLER_KEYS:
        known = ", ".join(sorted(BUILTIN_HANDLER_KEYS))
        raise ValueError(
            f"Unknown bootstrap handler {handler!r}; built-in keys: {known}",
        )
    return BootstrapConfig(builtin_key=handler)
