"""Helpers shared by the platform-specific installers.

This module only uses the Python standard library. In particular it does not
import :mod:`ctypes`: ``getcsound`` is intended to be safe to depend on from
pure-Python packages.
"""

from __future__ import annotations

import logging
import subprocess
import sys
from collections import deque
from collections.abc import Sequence

from ._errors import CsoundInstallError

logger = logging.getLogger("getcsound")


def stdin_is_tty() -> bool:
    """Return True if stdin is an interactive terminal."""
    try:
        return bool(sys.stdin is not None and not sys.stdin.closed and sys.stdin.isatty())
    except (AttributeError, OSError, ValueError):
        return False


def run_installer(cmd: Sequence[str], failure_hint: str = "") -> None:
    """Run an installer command, streaming its output live while capturing it.

    When stdin is a terminal (interactive use) the child inherits stdio
    directly so prompts are visible. Capturing via a pipe would hide prompts
    printed without a trailing newline (e.g. ``read -p "…: "``, as used by the
    Linux bundled ``install.sh``, or ``sudo``'s password prompt): line-wise
    iteration only forwards complete lines, so the question would never be
    shown while the installer blocks waiting for the answer. Piping also makes
    the child's stdout fully buffered instead of line-buffered, delaying
    progress output.

    In non-interactive mode (no tty) stdout and stderr are merged, printed as
    they arrive and the last 50 lines are retained for diagnostics.

    Args:
        cmd: the command to run.
        failure_hint: extra text appended to the error message when the command
            fails.

    Raises:
        CsoundInstallError: if the command exits with a non-zero status. The
            error includes the exit status, the full command, the tail of the
            captured output (non-interactive mode only) and ``failure_hint``.
    """
    logger.info("Running bundled installer: %s", " ".join(str(c) for c in cmd))
    if stdin_is_tty():
        # Interactive: inherit stdio so `read -p`/sudo prompts are visible.
        try:
            returncode = subprocess.run(list(cmd), check=False).returncode
        except OSError as e:
            raise CsoundInstallError(
                f"Could not run installer command "
                f"{' '.join(str(c) for c in cmd)!r}: {e}") from e
        if returncode != 0:
            message = (f"Installer exited with status {returncode}\n"
                       f"Command: {' '.join(str(c) for c in cmd)}")
            if failure_hint:
                message += f"\n{failure_hint}"
            raise CsoundInstallError(message)
        return

    try:
        proc = subprocess.Popen(list(cmd),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                text=True, bufsize=1)
    except OSError as e:
        raise CsoundInstallError(
            f"Could not run installer command "
            f"{' '.join(str(c) for c in cmd)!r}: {e}") from e

    tail: deque[str] = deque(maxlen=50)
    assert proc.stdout is not None
    for line in proc.stdout:
        tail.append(line)
        print(line, end="")
    returncode = proc.wait()
    if returncode != 0:
        output = "".join(tail).rstrip() or "<no output captured>"
        message = (f"Installer exited with status {returncode}\n"
                   f"Command: {' '.join(str(c) for c in cmd)}\n"
                   f"--- installer output (last {len(tail)} lines) ---\n"
                   f"{output}")
        if failure_hint:
            message += f"\n{failure_hint}"
        raise CsoundInstallError(message)
