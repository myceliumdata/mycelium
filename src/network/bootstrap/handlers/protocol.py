"""Bootstrap handler protocol."""

from __future__ import annotations

from typing import Protocol

from network.bootstrap.context import BootstrapContext, BootstrapResult


class BootstrapHandler(Protocol):
    """Network-specific bootstrap implementation."""

    def run(self, ctx: BootstrapContext) -> BootstrapResult: ...
