"""Fetch remote example seed data declared in ``seed.source.json``."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GitSeedSource:
    """Git-hosted seed tree copied into a live network root."""

    repo: str
    ref: str
    source_path: str
    dest: str


def load_git_seed_source(manifest_path: Path) -> GitSeedSource | None:
    """Parse ``seed.source.json`` when present; return ``None`` when missing."""
    if not manifest_path.is_file():
        return None
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid seed.source.json at {manifest_path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"{manifest_path}: seed.source.json must be a JSON object")
    seed_type = raw.get("type")
    if seed_type != "git":
        raise ValueError(
            f"{manifest_path}: unsupported seed source type {seed_type!r} (only 'git')",
        )
    repo = str(raw.get("repo", "")).strip()
    ref = str(raw.get("ref", "")).strip()
    source_path = str(raw.get("source_path", "")).strip()
    dest = str(raw.get("dest", "")).strip()
    if not repo or not ref or not source_path or not dest:
        raise ValueError(
            f"{manifest_path}: git seed requires repo, ref, source_path, and dest",
        )
    return GitSeedSource(repo=repo, ref=ref, source_path=source_path, dest=dest)


def git_seed_summary(source: GitSeedSource) -> str:
    """Short label for refresh logging."""
    repo_name = source.repo.rstrip("/").split("/")[-1].removesuffix(".git")
    return f"{repo_name}@{source.ref}"


def fetch_git_seed(
    network_root: Path,
    source: GitSeedSource,
    *,
    subprocess_run: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> str:
    """Shallow-clone ``source`` and copy ``source_path`` into ``network_root/dest``.

    Returns a short summary string for operator logs.
    """
    network_root = network_root.expanduser().resolve()
    dest_dir = network_root / source.dest
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    dest_dir.parent.mkdir(parents=True, exist_ok=True)

    runner = subprocess_run if subprocess_run is not None else subprocess.run
    with tempfile.TemporaryDirectory(prefix="mycelium-seed-") as tmp:
        clone_root = Path(tmp) / "clone"
        completed = runner(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                source.ref,
                source.repo,
                str(clone_root),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            stderr = (completed.stderr or "").strip()
            raise RuntimeError(
                f"git clone failed for {git_seed_summary(source)}: {stderr or completed.stdout}",
            )
        src = clone_root / source.source_path
        if not src.is_dir():
            raise RuntimeError(
                f"Seed path missing in {git_seed_summary(source)}: {source.source_path}",
            )
        shutil.copytree(src, dest_dir)
    return git_seed_summary(source)


def fetch_example_seed(network_root: Path) -> str | None:
    """Fetch remote seed when ``seed.source.json`` exists under ``network_root``."""
    manifest_path = network_root / "seed.source.json"
    source = load_git_seed_source(manifest_path)
    if source is None:
        return None
    return fetch_git_seed(network_root, source)