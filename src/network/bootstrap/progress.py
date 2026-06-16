"""stderr progress reporting for long network bootstrap / refresh."""

from __future__ import annotations

import os
import sys

_LABEL_RETRIEVING = "Retrieving data…"
_LABEL_PROCESSING = "Processing records"
_LABEL_CLEANING = "Cleaning up…"


def bootstrap_progress_enabled() -> bool:
    """Return True when bootstrap progress should emit to stderr."""
    raw = os.getenv("MYCELIUM_BOOTSTRAP_PROGRESS", "").strip()
    if raw == "0":
        return False
    if raw == "1":
        return True
    return sys.stderr.isatty()


def make_bootstrap_progress() -> BootstrapProgress | None:
    """Create a progress reporter when enabled; otherwise ``None``."""
    if not bootstrap_progress_enabled():
        return None
    return BootstrapProgress(enabled=True)


class BootstrapProgress:
    """TTY-aware stderr progress for bootstrap phases."""

    def __init__(self, *, enabled: bool, stream: object | None = None) -> None:
        self.enabled = enabled
        self._stream = stream if stream is not None else sys.stderr
        self._tty = enabled and self._stream.isatty()
        self._phase: str | None = None
        self._last_non_tty_emit = 0
        self._last_non_tty_pct = -1

    def retrieving(self, detail: str = "") -> None:
        if not self.enabled:
            return
        self._finish_processing_line()
        message = _LABEL_RETRIEVING
        if detail:
            message = f"{message} ({detail})"
        self._write_line(message)
        self._phase = "retrieving"

    def complete_retrieving(self) -> None:
        """End retrieving phase with a newline when no processing follows immediately."""
        if not self.enabled or self._phase != "retrieving":
            return
        self._write_newline()
        self._phase = None

    def processing(self, current: int, total: int, *, detail: str = "") -> None:
        if not self.enabled or total <= 0:
            return
        if self._phase == "retrieving":
            self._write_newline()
            self._phase = None
        self._phase = "processing"
        message = f"{_LABEL_PROCESSING} ({current}/{total})…"
        if detail:
            message = f"{message} {detail}"
        if self._tty:
            self._stream.write(f"\r{message}")
            self._stream.flush()
            return
        pct = int((current * 100) / total)
        step = max(1, total // 100)
        if (
            current == total
            or current - self._last_non_tty_emit >= 500
            or current - self._last_non_tty_emit >= step
            or pct > self._last_non_tty_pct
        ):
            self._write_line(message)
            self._last_non_tty_emit = current
            self._last_non_tty_pct = pct

    def cleaning_up(self, detail: str = "") -> None:
        if not self.enabled:
            return
        self._finish_processing_line()
        message = _LABEL_CLEANING
        if detail:
            message = f"{message} ({detail})"
        self._write_line(message)
        self._phase = "cleaning"

    def done(self) -> None:
        """Clear in-progress TTY line after bootstrap completes."""
        if not self.enabled:
            return
        self._finish_processing_line()
        self._phase = None

    def _finish_processing_line(self) -> None:
        if self._phase == "processing":
            self._write_newline()

    def _write_line(self, message: str) -> None:
        self._stream.write(message + "\n")
        self._stream.flush()

    def _write_newline(self) -> None:
        self._stream.write("\n")
        self._stream.flush()
