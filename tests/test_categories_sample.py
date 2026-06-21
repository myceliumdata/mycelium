"""Smoke tests for the documentation categories sample."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"


@pytest.mark.smoke
def test_sample_categories_json_parses() -> None:
    assert SAMPLE_CATEGORIES.is_file()
    data = json.loads(SAMPLE_CATEGORIES.read_text(encoding="utf-8"))
    assert data["version"] == "1.0"
    assert data["last_updated"] == "2026-06-03T00:00:00+00:00"
    assert set(data) >= {"categories", "attribute_map", "version", "last_updated"}
    assert len(data["categories"]) == 6
    assert "email" in data["attribute_map"]
    assert data["attribute_map"]["email"] == "contact"


@pytest.mark.smoke
def test_refresh_example_network_skips_categories_json(tmp_path: Path) -> None:
    """Even if a stray categories.json exists in the example dir, refresh must skip it."""
    import subprocess
    import sys

    stray = REPO_ROOT / "examples" / "networks" / "crm-seeded" / "categories.json"
    created_stray = False
    if not stray.exists():
        stray.write_text('{"version":"0"}', encoding="utf-8")
        created_stray = True
    try:
        target = tmp_path / "out"
        script = REPO_ROOT / "bin" / "refresh-example-network"
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                "crm-seeded",
                "--root",
                str(target),
                "--no-register",
                "--yes",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr or result.stdout
        assert (target / "categories.json").is_file()
        data = json.loads((target / "categories.json").read_text(encoding="utf-8"))
        assert data.get("version") == "1.0"
        assert "name" in data.get("attribute_map", {})
    finally:
        if created_stray and stray.exists():
            stray.unlink()
