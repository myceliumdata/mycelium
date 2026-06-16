"""Tests for bootstrap stderr progress reporting."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from network.bootstrap import run_network_bootstrap
from network.bootstrap.progress import BootstrapProgress
from network.paths import NetworkPaths

REPO_ROOT = Path(__file__).resolve().parent.parent
CRM_SEED = REPO_ROOT / "examples" / "networks" / "crm" / "seed.json"
CRM_MANIFEST = REPO_ROOT / "examples" / "networks" / "crm" / "network.json"
BASEBALL_EXAMPLE = REPO_ROOT / "examples" / "networks" / "baseball"
BASEBALL_MANIFEST = BASEBALL_EXAMPLE / "network.json"


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


def _prepare_crm_root(tmp_path: Path) -> NetworkPaths:
    root = tmp_path / "crm"
    root.mkdir(parents=True)
    shutil.copy(CRM_SEED, root / "seed.json")
    shutil.copy(CRM_MANIFEST, root / "network.json")
    return NetworkPaths.from_root(root)


def _prepare_baseball_root(tmp_path: Path) -> NetworkPaths:
    root = tmp_path / "baseball"
    root.mkdir()
    shutil.copy(BASEBALL_MANIFEST, root / "network.json")
    shutil.copytree(BASEBALL_EXAMPLE / "bootstrap_handlers", root / "bootstrap_handlers")
    _write_minimal_lahman_fixture(root / "seed")
    return NetworkPaths.from_root(root)


@pytest.mark.smoke
def test_bootstrap_progress_disabled_on_stderr(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("MYCELIUM_BOOTSTRAP_PROGRESS", "0")
    paths = _prepare_baseball_root(tmp_path)
    run_network_bootstrap(paths, progress=None)
    err = capsys.readouterr().err
    assert "Processing records" not in err
    assert "Cleaning up" not in err


@pytest.mark.smoke
def test_bootstrap_progress_forced_shows_all_phases(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("MYCELIUM_BOOTSTRAP_PROGRESS", "1")
    paths = _prepare_baseball_root(tmp_path)
    result = run_network_bootstrap(paths)
    err = capsys.readouterr().err
    assert result.entities_committed >= 1
    assert "Retrieving data" in err
    assert "Processing records" in err
    assert "(1/1)" in err
    assert "Cleaning up" in err


@pytest.mark.smoke
def test_crm_bootstrap_unchanged_with_progress_off(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MYCELIUM_BOOTSTRAP_PROGRESS", "0")
    paths = _prepare_crm_root(tmp_path)
    result = run_network_bootstrap(paths)
    assert result.handler_id == "default_seed"
    assert result.entities_committed == 15
    payload = json.loads(paths.entities_path.read_text(encoding="utf-8"))
    assert len(payload["entities"]) == 15


@pytest.mark.smoke
def test_bootstrap_progress_reporter_api() -> None:
    lines: list[str] = []

    class _Stream:
        def write(self, text: str) -> None:
            lines.append(text)

        def flush(self) -> None:
            return None

        def isatty(self) -> bool:
            return False

    stream = _Stream()
    progress = BootstrapProgress(enabled=True, stream=stream)
    progress.retrieving("git clone")
    progress.processing(1, 2, detail="player binds")
    progress.processing(2, 2, detail="player binds")
    progress.cleaning_up()
    progress.done()
    joined = "".join(lines)
    assert "Retrieving data" in joined
    assert "Processing records (2/2)" in joined
    assert "Cleaning up" in joined
