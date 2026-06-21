"""Guard: framework src must not hard-code CRM bind field pairs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CRM_METERING = json.loads(
    (REPO_ROOT / "examples" / "networks" / "crm-seeded" / "network.json").read_text(
        encoding="utf-8",
    ),
)["metering"]


def _write_player_record_type_manifest(root: Path) -> None:
    manifest = {
        "name": "player-net",
        "mvr": {
            "default_record_type": "player",
            "record_types": {
                "player": {
                    "bind_fields": ["name", "team"],
                    "description": "player record type",
                    "new_records": "query_allowed",
                },
            },
        },
        "metering": dict(CRM_METERING),
    }
    (root / "network.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )


@pytest.mark.smoke
def test_no_hardcoded_crm_bind_frozenset_in_src() -> None:
    root = Path(__file__).resolve().parent.parent / "src"
    forbidden = 'frozenset({"name", "employer"})'
    hits: list[str] = []
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if forbidden in text:
            hits.append(str(path.relative_to(root.parent)))
    assert hits == []

@pytest.mark.smoke
def test_bind_from_record_uses_mvr_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from agents.context import bind_from_record
    from network_helpers import copy_crm_network_manifest

    copy_crm_network_manifest(tmp_path)
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))

    record = {
        "id": "player-1",
        "name": "Babe Ruth",
        "team": "New York Yankees",
    }
    bind = bind_from_record(
        record,
        bind_fields=["name", "team"],
    )
    assert bind == {"name": "Babe Ruth", "team": "New York Yankees"}
    assert "employer" not in bind


@pytest.mark.smoke
def test_identity_records_from_match_preserves_mvr_bind_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from agents.responses import _identity_records_from_match, shape_results
    from network.paths import NetworkPaths, apply_network_paths

    _write_player_record_type_manifest(tmp_path)
    paths = NetworkPaths.from_root(tmp_path)
    apply_network_paths(paths)
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))

    matched = [
        {
            "id": "player-1",
            "name": "Babe Ruth",
            "team": "New York Yankees",
            "_registry": True,
            "_validation_state": "validated",
        },
    ]
    identity_rows = _identity_records_from_match(matched)
    shaped = shape_results(identity_rows, None)

    assert shaped == [
        {
            "id": "player-1",
            "name": "Babe Ruth",
            "team": "New York Yankees",
        },
    ]
    assert "employer" not in shaped[0]


@pytest.mark.smoke
def test_identity_message_label_uses_secondary_bind_field(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from agents.responses import _identity_message_label
    from network.paths import NetworkPaths, apply_network_paths

    _write_player_record_type_manifest(tmp_path)
    paths = NetworkPaths.from_root(tmp_path)
    apply_network_paths(paths)
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))

    label = _identity_message_label(
        {"id": "player-1", "name": "Babe Ruth", "team": "New York Yankees"},
    )
    assert label == "Babe Ruth at New York Yankees"
