"""Smoke and full tests for ``mycelium network create`` (Phase 5c)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from agents.classification.models import Category, CategoryTreeData
from agents.registry import RegisteredAgent
from graphs.core import reset_core_graph, run_query
from models.state import PersonQuery
from network.create import create_network
from network.ontology import SkeletonOntologyResult
from network.paths import NetworkPaths, apply_network_paths
from network.registry import load_network_registry

_CRM_SIX = frozenset(
    {
        "contact",
        "social",
        "relationships",
        "demographic",
        "professional",
        "financial",
    },
)


def _write_seed(path: Path, people: list[dict[str, str]]) -> Path:
    path.write_text(json.dumps({"people": people}, indent=2) + "\n", encoding="utf-8")
    return path


def _mock_ontology_three(
    *,
    marker: str = "mock-three",
) -> SkeletonOntologyResult:
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    categories = {
        "alpha": Category(
            description=f"Alpha domain {marker}",
            assigned_agent="alpha_specialist",
            examples=["alpha_attr", "alpha_score"],
        ),
        "beta": Category(
            description=f"Beta domain {marker}",
            assigned_agent="beta_specialist",
            examples=["beta_flag"],
        ),
        "gamma": Category(
            description=f"Gamma domain {marker}",
            assigned_agent="gamma_specialist",
            examples=["gamma_level"],
        ),
    }
    attribute_map = {
        "alpha_attr": "alpha",
        "alpha_score": "alpha",
        "beta_flag": "beta",
        "gamma_level": "gamma",
    }
    agents = [
        RegisteredAgent(
            name=f"{key}_specialist",
            category=key,
            description=cat.description,
            module_path=f"agents.specialists.{key}_specialist",
            entrypoint=f"{key}_specialist",
            storage_path=f"agents/{key}/storage.json",
            strategy_path=f"agents/{key}/storage_strategy.json",
            is_generated=True,
            created_at=now_iso,
        )
        for key, cat in categories.items()
    ]
    return SkeletonOntologyResult(
        categories=CategoryTreeData(
            version="1.0",
            last_updated=now,
            model_used="mock",
            categories=categories,
            attribute_map=attribute_map,
        ),
        agents=agents,
        model_used="mock",
    )


def _mock_ontology_two() -> SkeletonOntologyResult:
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    categories = {
        "telemetry": Category(
            description="Sensor readings",
            assigned_agent="telemetry_specialist",
            examples=["signal_strength"],
        ),
        "maintenance": Category(
            description="Service history",
            assigned_agent="maintenance_specialist",
            examples=["last_service"],
        ),
    }
    agents = [
        RegisteredAgent(
            name="telemetry_specialist",
            category="telemetry",
            description="Sensor readings",
            module_path="agents.specialists.telemetry_specialist",
            entrypoint="telemetry_specialist",
            storage_path="agents/telemetry/storage.json",
            strategy_path="agents/telemetry/storage_strategy.json",
            is_generated=True,
            created_at=now_iso,
        ),
        RegisteredAgent(
            name="maintenance_specialist",
            category="maintenance",
            description="Service history",
            module_path="agents.specialists.maintenance_specialist",
            entrypoint="maintenance_specialist",
            storage_path="agents/maintenance/storage.json",
            strategy_path="agents/maintenance/storage_strategy.json",
            is_generated=True,
            created_at=now_iso,
        ),
    ]
    return SkeletonOntologyResult(
        categories=CategoryTreeData(
            version="1.0",
            last_updated=now,
            model_used="mock",
            categories=categories,
            attribute_map={
                "signal_strength": "telemetry",
                "last_service": "maintenance",
            },
        ),
        agents=agents,
        model_used="mock",
    )


def _isolated_registry(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    config = tmp_path / "networks.json"
    monkeypatch.setenv("MYCELIUM_NETWORKS_CONFIG", str(config))
    return config


@pytest.mark.smoke
def test_create_network_dry_run_writes_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _isolated_registry(monkeypatch, tmp_path)
    root = tmp_path / "dry_net"
    seed = _write_seed(tmp_path / "seed.json", [{"name": "Dry Person", "employer": "D"}])
    ontology_calls = 0

    def _ontology(_prompt: str) -> SkeletonOntologyResult:
        nonlocal ontology_calls
        ontology_calls += 1
        return _mock_ontology_three()

    result = create_network(
        "dry_net",
        root,
        seed,
        "Track widget telemetry",
        dry_run=True,
        ontology_fn=_ontology,
    )

    assert result.dry_run is True
    assert result.categories_count == 3
    assert ontology_calls == 1
    assert result.ontology_json is not None
    assert not root.exists()


@pytest.mark.smoke
def test_create_network_happy_path_writes_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _isolated_registry(monkeypatch, tmp_path)
    root = tmp_path / "happy_net"
    seed = _write_seed(
        tmp_path / "seed.json",
        [{"name": "Happy Person", "employer": "H"}],
    )

    result = create_network(
        "happy_net",
        root,
        seed,
        "Custom widget network",
        display_name="Happy Net",
        default=True,
        ontology_fn=lambda _p: _mock_ontology_three(),
    )

    assert result.registered is True
    assert result.specialists_count == 3
    assert (root / "seed.json").is_file()
    assert (root / "categories.json").is_file()
    assert (root / "agent_registry.json").is_file()
    assert (root / "network.json").is_file()
    assert (root / "specialists" / "alpha_specialist.py").is_file()
    assert (root / "agents" / "alpha" / "storage.json").is_file()

    manifest = json.loads((root / "network.json").read_text(encoding="utf-8"))
    assert manifest["display_name"] == "Happy Net"
    assert manifest["creation_prompt"] == "Custom widget network"

    entries = load_network_registry()
    assert any(e.name == "happy_net" and e.default for e in entries)
    assert config.is_file()


@pytest.mark.smoke
def test_create_network_rejects_existing_without_force(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _isolated_registry(monkeypatch, tmp_path)
    root = tmp_path / "existing"
    root.mkdir()
    (root / "network.json").write_text("{}", encoding="utf-8")
    seed = _write_seed(tmp_path / "seed.json", [{"name": "X"}])

    with pytest.raises(ValueError, match="network.json present"):
        create_network(
            "existing",
            root,
            seed,
            "prompt",
            ontology_fn=lambda _p: _mock_ontology_three(),
        )


@pytest.mark.smoke
def test_create_network_invalid_seed_before_ontology(tmp_path: Path) -> None:
    root = tmp_path / "bad_seed"
    seed = tmp_path / "bad.json"
    seed.write_text(json.dumps({"items": []}), encoding="utf-8")

    def _should_not_run(_prompt: str) -> SkeletonOntologyResult:
        msg = "ontology should not be called for invalid seed"
        raise AssertionError(msg)

    with pytest.raises(ValueError, match="people"):
        create_network(
            "bad_seed",
            root,
            seed,
            "prompt",
            ontology_fn=_should_not_run,
        )


@pytest.mark.smoke
def test_create_network_force_overwrites_ontology(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _isolated_registry(monkeypatch, tmp_path)
    root = tmp_path / "force_net"
    seed = _write_seed(tmp_path / "seed.json", [{"name": "Force Person"}])

    create_network(
        "force_net",
        root,
        seed,
        "first",
        ontology_fn=lambda _p: _mock_ontology_three(marker="first"),
    )
    orphan = root / "specialists" / "orphan_specialist.py"
    orphan.parent.mkdir(parents=True, exist_ok=True)
    orphan.write_text("# stale orphan\n", encoding="utf-8")

    create_network(
        "force_net",
        root,
        seed,
        "second",
        force=True,
        ontology_fn=lambda _p: _mock_ontology_three(marker="second-pass"),
    )

    categories = json.loads((root / "categories.json").read_text(encoding="utf-8"))
    assert categories["categories"]["alpha"]["description"].endswith("second-pass")
    assert not orphan.is_file()


@pytest.mark.smoke
def test_create_network_mcp_snippet_contains_network_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _isolated_registry(monkeypatch, tmp_path)
    root = tmp_path / "mcp_net"
    seed = _write_seed(tmp_path / "seed.json", [{"name": "MCP Person"}])

    result = create_network(
        "mcp_net",
        root,
        seed,
        "MCP snippet test",
        ontology_fn=lambda _p: _mock_ontology_three(),
    )

    assert result.mcp_snippet is not None
    assert "MYCELIUM_NETWORK_ROOT" in result.mcp_snippet
    assert str(root.resolve()) in result.mcp_snippet


@pytest.fixture(autouse=True)
def _sync_checkpointer_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")


@pytest.mark.full
def test_create_network_query_uses_custom_ontology_not_crm_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _isolated_registry(monkeypatch, tmp_path)
    root = tmp_path / "query_net"
    seed = _write_seed(
        tmp_path / "seed.json",
        [{"name": "Query Person", "employer": "Q Co"}],
    )
    mock = _mock_ontology_two()

    create_network(
        "query_net",
        root,
        seed,
        "Industrial equipment monitoring",
        default=True,
        ontology_fn=lambda _p: mock,
    )

    apply_network_paths(NetworkPaths.from_root(root))
    reset_core_graph()
    from agents.classification import reset_category_tree
    from agents.factory.agent_factory import reset_agent_factory
    from agents.registry import reset_agent_registry
    from agents.seed import reset_seed_data
    from storage.core import reset_storage

    for reset_fn in (
        reset_storage,
        reset_seed_data,
        reset_category_tree,
        reset_agent_registry,
        reset_agent_factory,
    ):
        reset_fn()

    categories_on_disk = json.loads((root / "categories.json").read_text(encoding="utf-8"))
    assert set(categories_on_disk["categories"].keys()) == {"telemetry", "maintenance"}
    assert set(categories_on_disk["categories"].keys()).isdisjoint(_CRM_SIX)

    response = run_query(
        PersonQuery(
            person_key="Query Person",
            requested_attributes=["signal_strength"],
        ),
        thread_id="network-create-integration",
    )
    assert len(response.results) == 1
    assert response.results[0]["id"]
    assert "Query Person" in response.message
    assert "signal_strength" in response.message or "signal_strength" in response.debug
    assert "telemetry" in response.debug
    assert config.is_file()
