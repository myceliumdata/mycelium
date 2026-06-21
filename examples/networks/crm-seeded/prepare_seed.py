#!/usr/bin/env python3
"""Transform a CRM seed file → example ``seed.json`` (MVR bind fields only).

Maintainer utility for evolving ``examples/networks/crm-seeded/seed.json``. The full
prototype pipeline (``raw_data.json`` → ``seed_crm.json``) lives in git tag
``prototype``; pass paths explicitly when regenerating this subset.

Usage::

    python examples/networks/crm-seeded/prepare_seed.py \\
        --crm /path/to/seed_crm.json \\
        --out examples/networks/crm-seeded/seed.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def prepare_seed(crm_path: Path, out_path: Path) -> int:
    payload = json.loads(crm_path.read_text(encoding="utf-8"))
    rows: list[dict[str, str | None]] = []
    for row in payload.get("people", []):
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "name": row.get("name", ""),
                "employer": row.get("employer"),
            },
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps({"rows": rows}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return len(rows)


def main() -> None:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--crm",
        type=Path,
        default=here / "seed_crm.json",
        help="Source CRM JSON with people array",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=here / "seed.json",
        help="Output seed.json path",
    )
    args = parser.parse_args()
    count = prepare_seed(args.crm.expanduser().resolve(), args.out.expanduser().resolve())
    print(f"Wrote {count} rows to {args.out} (no id fields)")


if __name__ == "__main__":
    main()
