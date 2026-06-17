"""Lahman warehouse bootstrap handler for the baseball example network."""

from __future__ import annotations

from agents.attribute_write import ensure_entity_bind_fields
from agents.entity_registry import get_entity_registry
from bootstrap_handlers.lahman_common import (
    distinct_player_team_rows,
    distinct_team_label_rows,
    ingest_warehouse,
    resolve_lahman_csv_dir,
    resolve_network_seed,
)
from network.bootstrap.context import BootstrapContext, BootstrapResult

LAHMAN_PLAYER_ID = "lahman.playerID"
LAHMAN_TEAM_ID = "lahman.teamID"
LAHMAN_FRANCH_ID = "lahman.franchID"


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
        progress = ctx.progress
        if progress is not None:
            progress.retrieving("building warehouse")
        ingest_counts = ingest_warehouse(csv_dir, warehouse_path)
        player_rows = distinct_player_team_rows(warehouse_path)

        team_registry = get_entity_registry(grain="team")
        player_registry = get_entity_registry(grain="player")
        teams_committed = 0
        players_committed = 0
        bind_collisions: list[str] = []

        for team_name, team_id, franch_id in distinct_team_label_rows(warehouse_path):
            entity, duplicate = ensure_entity_bind_fields(
                {"name": team_name},
                source="seed_bootstrap",
                validation_state="validated",
                registry=team_registry,
            )
            source_keys = {LAHMAN_TEAM_ID: team_id}
            if franch_id:
                source_keys[LAHMAN_FRANCH_ID] = franch_id
            if duplicate:
                existing = team_registry.lookup_by_bind_values({"name": team_name})
                if existing is not None:
                    team_registry.set_source_keys(existing.id, source_keys)
                continue
            team_registry.set_source_keys(entity.id, source_keys)
            teams_committed += 1

        total_players = len(player_rows)
        for index, (player_id, display_name, team_label) in enumerate(player_rows, start=1):
            if progress is not None:
                progress.processing(index, total_players, detail="player binds")
            bind_values = {"name": display_name, "team": team_label}
            existing_by_source = player_registry.lookup_by_source_key(
                LAHMAN_PLAYER_ID,
                player_id,
            )
            if existing_by_source is not None:
                mapped_id = existing_by_source.id
                existing = player_registry.lookup_by_bind_values(bind_values)
                if existing is not None and existing.id == mapped_id:
                    continue
                if existing is not None and existing.id != mapped_id:
                    bind_collisions.append(
                        "skipped alias "
                        f"{bind_values!r} for playerID {player_id!r}: "
                        f"already bound to a different player",
                    )
                    continue
                player_registry.add_bind_alias(mapped_id, bind_values)
                continue

            entity, duplicate = ensure_entity_bind_fields(
                bind_values,
                source="seed_bootstrap",
                validation_state="validated",
                registry=player_registry,
            )
            player_registry.set_source_keys(entity.id, {LAHMAN_PLAYER_ID: player_id})
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
            errors=bind_collisions,
        )
