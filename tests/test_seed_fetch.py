"""Tests for remote example seed fetch."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from network.seed_fetch import (
    GitSeedSource,
    fetch_example_seed,
    fetch_git_seed,
    git_seed_summary,
    load_git_seed_source,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
BASEBALL_EXAMPLE = REPO_ROOT / "examples" / "networks" / "baseball"


def _write_minimal_lahman_fixture(seed_dir: Path) -> None:
    seed_dir.mkdir(parents=True, exist_ok=True)
    (seed_dir / "Teams.csv").write_text(
        "yearID,lgID,teamID,franchID,name\n"
        "1957,NL,BRO,LAD,Brooklyn Dodgers\n",
        encoding="utf-8",
    )
    (seed_dir / "People.csv").write_text(
        "ID,playerID,nameFirst,nameLast\n"
        "1,aaronha01,Hank,Aaron\n",
        encoding="utf-8",
    )
    (seed_dir / "Appearances.csv").write_text(
        "yearID,teamID,playerID\n"
        "1957,BRO,aaronha01\n",
        encoding="utf-8",
    )


@pytest.mark.smoke
def test_load_git_seed_source_from_baseball_example() -> None:
    source = load_git_seed_source(BASEBALL_EXAMPLE / "seed.source.json")
    assert source is not None
    assert source.repo.endswith("myceliumdata/lahman-seed.git")
    assert source.ref == "v2025.1"
    assert source.source_path == "lahman_1871-2025_csv"
    assert source.dest == "seed/lahman_1871-2025_csv"
    assert git_seed_summary(source) == "lahman-seed@v2025.1"


@pytest.mark.smoke
def test_fetch_git_seed_copies_fixture(tmp_path: Path) -> None:
    fixture_root = tmp_path / "fixture-repo"
    fixture_csv = fixture_root / "lahman_1871-2025_csv"
    _write_minimal_lahman_fixture(fixture_csv)
    network_root = tmp_path / "live"
    network_root.mkdir()
    source = GitSeedSource(
        repo="https://example.com/lahman-seed.git",
        ref="v2025.1",
        source_path="lahman_1871-2025_csv",
        dest="seed/lahman_1871-2025_csv",
    )

    def fake_clone(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        clone_dest = Path(cmd[-1])
        shutil.copytree(fixture_root, clone_dest, dirs_exist_ok=True)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    summary = fetch_git_seed(network_root, source, subprocess_run=fake_clone)
    assert summary == "lahman-seed@v2025.1"
    copied = network_root / "seed" / "lahman_1871-2025_csv"
    assert (copied / "People.csv").is_file()
    assert (copied / "Teams.csv").is_file()


@pytest.mark.smoke
def test_fetch_example_seed_reads_manifest(tmp_path: Path) -> None:
    fixture_root = tmp_path / "fixture-repo"
    fixture_csv = fixture_root / "lahman_1871-2025_csv"
    _write_minimal_lahman_fixture(fixture_csv)
    network_root = tmp_path / "live"
    network_root.mkdir()
    shutil.copy(BASEBALL_EXAMPLE / "seed.source.json", network_root / "seed.source.json")

    def fake_clone(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        clone_dest = Path(cmd[-1])
        shutil.copytree(fixture_root, clone_dest, dirs_exist_ok=True)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    import network.seed_fetch as seed_fetch_mod

    original = seed_fetch_mod.fetch_git_seed

    def patched_fetch(
        root: Path,
        source: GitSeedSource,
        *,
        subprocess_run: object | None = None,
        progress: object | None = None,
    ) -> str:
        return original(root, source, subprocess_run=fake_clone, progress=progress)

    seed_fetch_mod.fetch_git_seed = patched_fetch  # type: ignore[assignment]
    try:
        summary = fetch_example_seed(network_root)
    finally:
        seed_fetch_mod.fetch_git_seed = original

    assert summary == "lahman-seed@v2025.1"
    assert (network_root / "seed" / "lahman_1871-2025_csv" / "People.csv").is_file()