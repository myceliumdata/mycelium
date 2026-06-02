#!/usr/bin/env python3
"""beforeShellExecution: require approval for commands that delete directories."""

from __future__ import annotations

import json
import re
import sys

# Recursive rm, rmdir, and find -delete patterns (best-effort).
_DIR_DELETE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\brmdir\b", re.IGNORECASE),
    re.compile(r"\brm\b\s+(?:[^\s|;&]+\s+)*-[rR]", re.IGNORECASE),
    re.compile(r"\brm\b\s+.*-(?:rf|fr)\b", re.IGNORECASE),
    re.compile(r"\bfind\b.*\s-delete\b", re.IGNORECASE),
    re.compile(r"\bfind\b.*-exec\s+rm\b", re.IGNORECASE),
)


def _emit(permission: str, *, user_message: str, agent_message: str = "") -> None:
    out: dict[str, str] = {
        "permission": permission,
        "user_message": user_message,
    }
    if agent_message:
        out["agent_message"] = agent_message
    json.dump(out, sys.stdout)
    sys.stdout.write("\n")


def _looks_like_directory_deletion(command: str) -> bool:
    normalized = " ".join(command.split())
    return any(pattern.search(normalized) for pattern in _DIR_DELETE_PATTERNS)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.stderr.write("gate-directory-deletion: invalid JSON on stdin\n")
        return 1

    command = str(payload.get("command", "")).strip()
    if not command:
        return 0

    if _looks_like_directory_deletion(command):
        _emit(
            "ask",
            user_message=(
                "This command may delete a directory. "
                "Review it before approving."
            ),
            agent_message=(
                "Directory deletion blocked pending user approval "
                f"(command: {command[:200]})"
            ),
        )
        return 0

    _emit("allow", user_message="", agent_message="Shell command passed directory-deletion gate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
