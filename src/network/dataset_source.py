"""Pack dataset source pins from ``seed.source.json``."""

from __future__ import annotations

import json
from typing import Any

from network.paths import NetworkPaths


def _dataset_id_from_repo(repo: str, explicit: str | None) -> str:
    if explicit and explicit.strip():
        return explicit.strip()
    basename = repo.rstrip("/").split("/")[-1]
    if basename.endswith(".git"):
        basename = basename[:-4]
    return basename or "dataset"


def load_pack_dataset_source(paths: NetworkPaths) -> list[dict[str, Any]] | None:
    """Return dataset source dicts when ``seed.source.json`` declares a git pin."""
    source_path = paths.root / "seed.source.json"
    if not source_path.is_file():
        return None
    try:
        data = json.loads(source_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or data.get("type") != "git":
        return None
    repo = data.get("repo")
    ref = data.get("ref")
    if not isinstance(repo, str) or not repo.strip():
        return None
    if not isinstance(ref, str) or not ref.strip():
        return None
    dataset_id = _dataset_id_from_repo(repo, data.get("dataset_id"))
    return [
        {
            "kind": "dataset",
            "id": dataset_id,
            "version": ref.strip(),
            "retrieved_from": repo.strip(),
            "ref": ref.strip(),
        },
    ]
