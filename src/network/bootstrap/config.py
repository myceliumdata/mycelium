"""Parse ``network.json`` bootstrap handler configuration."""

from __future__ import annotations

import json
from dataclasses import dataclass

from network.mvr import default_record_type, load_mvr_config
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
    seed_record_type: str | None = None


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

    if bootstrap.get("seed_grain") is not None:
        raise ValueError(
            f"{manifest_path}: legacy bootstrap.seed_grain is not supported; "
            "use bootstrap.seed_record_type",
        )

    seed_record_type: str | None = None
    seed_record_type_raw = bootstrap.get("seed_record_type")
    if seed_record_type_raw is not None:
        if not isinstance(seed_record_type_raw, str) or not seed_record_type_raw.strip():
            raise ValueError(
                "network.json bootstrap.seed_record_type must be a non-empty string",
            )
        seed_record_type = seed_record_type_raw.strip()
        record_types = load_mvr_config(paths=paths).record_types
        if seed_record_type not in record_types:
            known = ", ".join(sorted(record_types.keys()))
            raise ValueError(
                f"network.json bootstrap.seed_record_type {seed_record_type!r} is not declared "
                f"in mvr.record_types ({known})",
            )

    return BootstrapConfig(
        module=module,
        class_name=class_name,
        seed_record_type=seed_record_type,
    )


def resolve_bootstrap_record_type(paths: NetworkPaths) -> str:
    """Return the entity record type that receives ``DefaultSeedHandler`` rows."""
    bootstrap = load_bootstrap_config(paths)
    if bootstrap.seed_record_type:
        return bootstrap.seed_record_type
    return default_record_type(paths=paths)
