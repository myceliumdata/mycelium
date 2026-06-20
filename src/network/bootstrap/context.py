"""Bootstrap phase dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from network.paths import NetworkPaths

if TYPE_CHECKING:
    from network.bootstrap.progress import BootstrapProgress


@dataclass(frozen=True)
class BootstrapContext:
    """Inputs for a network bootstrap handler."""

    paths: NetworkPaths
    guide_text: str | None
    progress: BootstrapProgress | None = None


@dataclass
class BootstrapResult:
    """Outcome of ``run_network_bootstrap``."""

    entities_committed: int
    sources_processed: list[str] = field(default_factory=list)
    handler_id: str = "default_seed"
    errors: list[str] = field(default_factory=list)
    entities_by_record_type: dict[str, int] = field(default_factory=dict)
    warehouse_ingest_counts: dict[str, int] = field(default_factory=dict)
