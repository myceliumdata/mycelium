"""Guard: framework src must not hard-code CRM bind field pairs."""

from __future__ import annotations

from pathlib import Path

import pytest


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
