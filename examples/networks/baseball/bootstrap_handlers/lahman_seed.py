"""Lahman warehouse bootstrap handler for the baseball example network."""

from __future__ import annotations

from agents.attribute_write import ensure_entity_bind_fields
from agents.entity_registry import get_entity_registry
from bootstrap_handlers.lahman_common import (
    distinct_player_team_rows,
    distinct_team_labels,
    ingest_warehouse,
    resolve_lahman_csv_dir,
    resolve_network_seed,
)
from network.bootstrap.context import BootstrapContext, BootstrapResult


class LahmanSeedHandler:
    """Ingest Lahman CSV seed, warehouse, and commit team + player entity grains."""

    def run(self, ctx: BootstrapContext) -> BootstrapResult:
        seed_ref = resolve_network_seed(ctx.paths.root)
        if seed_ref is None:
            return BootstrapResult(
                entities_committed=0,
                sources_processed=[],
                handler_id="lahman_seed",
            )

        csv_dir = resolve_lahman_csv_dir(seed_ref)
        if csv_dir is None:
            return BootstrapResult(
                entities_committed=0,
                sources_processed=[],
                handler_id="lahman_seed",
                errors=[f"No Lahman CSV data at {seed_ref}"],
            )

        warehouse_path = ctx.paths.root / "warehouse" / "lahman.sqlite"
        ingest_counts = ingest_warehouse(csv_dir, warehouse_path)

        team_registry = get_entity_registry(grain="team")
        player_registry = get_entity_registry(grain="player")
        teams_committed = 0
        players_committed = 0
        player_ids: dict[str, str] = {}

        for team_name in distinct_team_labels(warehouse_path):
            _, duplicate = ensure_entity_bind_fields(
                {"name": team_name},
                source="seed_bootstrap",
                validation_state="validated",
                registry=team_registry,
            )
            if duplicate:
                continue
            teams_committed += 1

        for player_id, display_name, team_label in distinct_player_team_rows(
            warehouse_path,
        ):
            bind_values = {"name": display_name, "team": team_label}
            mapped_id = player_ids.get(player_id)
            if mapped_id is not None:
                existing = player_registry.lookup_by_bind_values(bind_values)
                if existing is not None and existing.id == mapped_id:
                    continue
                if existing is not None and existing.id != mapped_id:
                    msg = (
                        f"bind key {bind_values!r} already maps to a different entity "
                        f"for playerID {player_id!r}"
                    )
                    return BootstrapResult(
                        entities_committed=teams_committed + players_committed,
                        sources_processed=[],
                        handler_id="lahman_seed",
                        errors=[msg],
                    )
                player_registry.add_bind_alias(mapped_id, bind_values)
                continue

            entity, duplicate = ensure_entity_bind_fields(
                bind_values,
                source="seed_bootstrap",
                validation_state="validated",
                registry=player_registry,
            )
            player_ids[player_id] = entity.id
            if duplicate:
                continue
            players_committed += 1

        try:
            source_label = str(seed_ref.relative_to(ctx.paths.root))
        except ValueError:
            source_label = seed_ref.name
        sources = [source_label]
        if ingest_counts:
            sources.append("warehouse/lahman.sqlite")

        return BootstrapResult(
            entities_committed=teams_committed + players_committed,
            sources_processed=sources,
            handler_id="lahman_seed",
            entities_by_grain={
                "team": teams_committed,
                "player": players_committed,
            },
        )
