#!/usr/bin/env python3
"""Transform ``seed_crm.json`` → ``seed.json`` (name + employer only).

Reads the CRM seed (which may include legacy ``id`` fields) and writes the
committed origin file without ``id`` keys. Run from repo root::

    python data/prepare_seed.py

See slice 1720 (seed-data-context redesign).
"""

from __future__ import annotations

import json
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent
_DEFAULT_CRM = _DATA_DIR / "seed_crm.json"
_DEFAULT_OUT = _DATA_DIR / "seed.json"


def prepare_seed(
    crm_path: Path = _DEFAULT_CRM,
    out_path: Path = _DEFAULT_OUT,
) -> int:
    payload = json.loads(crm_path.read_text(encoding="utf-8"))
    people: list[dict[str, str | None]] = []
    for row in payload.get("people", []):
        if not isinstance(row, dict):
            continue
        people.append(
            {
                "name": row.get("name", ""),
                "employer": row.get("employer"),
            },
        )
    out_path.write_text(
        json.dumps({"people": people}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return len(people)


def main() -> None:
    count = prepare_seed()
    print(f"Wrote {count} people to {_DEFAULT_OUT} (no id fields)")


if __name__ == "__main__":
    main()
