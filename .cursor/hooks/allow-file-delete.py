#!/usr/bin/env python3
"""preToolUse (Delete): auto-allow single-file deletes via the Delete tool."""

from __future__ import annotations

import json
import sys

# Delete tool removes files only, not directories.


def _emit(permission: str, *, user_message: str = "", agent_message: str = "") -> None:
    out: dict[str, str] = {"permission": permission}
    if user_message:
        out["user_message"] = user_message
    if agent_message:
        out["agent_message"] = agent_message
    json.dump(out, sys.stdout)
    sys.stdout.write("\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.stderr.write("allow-file-delete: invalid JSON on stdin\n")
        return 1

    tool_name = str(payload.get("tool_name", ""))
    if tool_name != "Delete":
        return 0

    tool_input = payload.get("tool_input") or {}
    if isinstance(tool_input, str):
        try:
            tool_input = json.loads(tool_input)
        except json.JSONDecodeError:
            tool_input = {}

    path = (
        tool_input.get("path")
        or tool_input.get("file_path")
        or tool_input.get("target")
        or ""
    )

    _emit(
        "allow",
        agent_message=f"Hook auto-approved Delete for: {path or '(unknown path)'}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
