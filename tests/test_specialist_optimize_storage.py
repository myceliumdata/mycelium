"""Tests for SpecialistAgent threshold-based optimize_storage policy."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from agents.specialists.agent import SpecialistAgent


@pytest.fixture
def agent_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    agents_dir = tmp_path / "agent_data"
    monkeypatch.setenv("MYCELIUM_AGENT_DATA_DIR", str(agents_dir))
    return agents_dir


@pytest.mark.smoke
def test_optimize_storage_below_threshold(agent_data_dir: Path) -> None:
    _ = agent_data_dir
    agent = SpecialistAgent(category="demographic")
    assert agent.optimize_storage() is False


@pytest.mark.smoke
def test_optimize_storage_at_threshold(agent_data_dir: Path) -> None:
    _ = agent_data_dir
    agent = SpecialistAgent(category="demographic")
    with patch.object(agent, "record_count", return_value=50):
        assert agent.optimize_storage() is True


@pytest.mark.smoke
def test_optimize_storage_skips_count_when_already_migrated(agent_data_dir: Path) -> None:
    _ = agent_data_dir
    agent = SpecialistAgent(category="demographic")
    with patch.object(agent.storage, "current_strategy", return_value="minisql_v1"):
        with patch.object(agent, "record_count") as count_mock:
            assert agent.optimize_storage() is False
            count_mock.assert_not_called()


@pytest.mark.smoke
def test_optimize_storage_threshold_env_override(
    agent_data_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = agent_data_dir
    monkeypatch.setenv("MYCELIUM_OPTIMIZE_STORAGE_THRESHOLD", "3")
    agent = SpecialistAgent(category="contact")
    with patch.object(agent, "record_count", return_value=2):
        assert agent.optimize_storage() is False
    with patch.object(agent, "record_count", return_value=3):
        assert agent.optimize_storage() is True


@pytest.mark.smoke
def test_write_at_threshold_attempts_migrate_and_succeeds(agent_data_dir: Path) -> None:
    agent = SpecialistAgent(category="professional")
    agent.storage.save({"records": {"existing-entity": {}}})
    with patch.object(agent, "optimize_storage_threshold", return_value=1):
        with patch.object(
            agent,
            "migrate_to",
            side_effect=NotImplementedError,
        ) as migrate_mock:
            result = agent.write_fields(
                "new-entity",
                {"employer": "Acme Corp"},
                actor_kind="bind",
            )
    migrate_mock.assert_called_once_with("minisql_v1")
    assert result == {"employer": "Acme Corp"}


@pytest.mark.smoke
def test_optimize_storage_threshold_subclass_override(agent_data_dir: Path) -> None:
    _ = agent_data_dir

    class ThresholdSpecialist(SpecialistAgent):
        def optimize_storage_threshold(self) -> int:
            return 10

    agent = ThresholdSpecialist(category="social")
    with patch.object(agent, "record_count", return_value=9):
        assert agent.optimize_storage() is False
    with patch.object(agent, "record_count", return_value=10):
        assert agent.optimize_storage() is True
