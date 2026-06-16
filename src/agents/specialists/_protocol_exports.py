"""Attach standard protocol handlers to a specialist module."""

from __future__ import annotations

from typing import Any

from agents.specialists.agent import SpecialistAgent
from agents.specialists import handlers


def attach_protocol_handlers(
    namespace: dict[str, Any] | Any,
    *,
    category: str,
    agent_name: str,
    agent: SpecialistAgent | None = None,
) -> None:
    resolved = agent or namespace.get("AGENT") if isinstance(namespace, dict) else getattr(namespace, "AGENT", None)
    if resolved is not None:
        write_fields = resolved.write_fields
        read_fields = resolved.read_fields
        bootstrap_entity = resolved.bootstrap_entity
    else:
        def write_fields(
            entity_id: str,
            fields: dict[str, str],
            *,
            actor_kind: str,
            at: str | None = None,
        ) -> dict[str, str]:
            return handlers.write_fields(
                category,
                agent_name,
                entity_id,
                fields,
                actor_kind=actor_kind,
                at=at,
            )

        def read_fields(
            entity_id: str,
            fields: list[str],
            *,
            include_versions: bool = False,
            include_provenance: bool | None = None,
        ) -> dict[str, Any]:
            kwargs: dict[str, Any] = {}
            if include_provenance is not None:
                kwargs["include_provenance"] = include_provenance
            else:
                kwargs["include_versions"] = include_versions
            return handlers.read_fields(
                category,
                agent_name,
                entity_id,
                fields,
                **kwargs,
            )

        def bootstrap_entity(
            entity_id: str,
            fields: dict[str, str],
            *,
            actor_kind: str = "seed_bootstrap",
        ) -> dict[str, str]:
            return handlers.bootstrap_entity(
                category,
                agent_name,
                entity_id,
                fields,
                actor_kind=actor_kind,
            )

    if isinstance(namespace, dict):
        namespace["write_fields"] = write_fields
        namespace["read_fields"] = read_fields
        namespace["bootstrap_entity"] = bootstrap_entity
        if resolved is not None:
            namespace["AGENT"] = resolved
    else:
        namespace.write_fields = write_fields  # type: ignore[attr-defined]
        namespace.read_fields = read_fields  # type: ignore[attr-defined]
        namespace.bootstrap_entity = bootstrap_entity  # type: ignore[attr-defined]
        if resolved is not None:
            namespace.AGENT = resolved  # type: ignore[attr-defined]
