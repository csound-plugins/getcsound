"""Install Csound 7 from Python.

``getcsound`` lets a Python package declare Csound as a dependency and make it
available on the user's machine without asking them to install it manually::

    from getcsound import ensure_csound

    installation = ensure_csound()
    # LIBCSOUNDPATH and OPCODE7DIR64 now point at a usable Csound 7.
    import libcsound  # or any other Csound binding

    # installation.libpath, installation.plugindir and installation.bindir
    # describe the installation without loading it.

The package is pure Python and has no runtime dependencies. It deliberately
does **not** import :mod:`ctypes` or depend on ``libcsound``, so it can be used
even by projects that must remain free of binary dependencies.

Importing ``getcsound`` does not install anything. Installation happens only
when :func:`ensure_csound` (or one of the ``install_csound_*`` functions) is
called.

The official installers are bundled with the package and are run with bash or
PowerShell:

* Linux: installs the portable Csound 7 build to ``~/.local/csound`` when no
  terminal is available, or interactively otherwise.
* macOS: installs the official Csound 7 ``.pkg`` (needs sudo, either an
  interactive terminal or password-less sudo).
* Windows: installs the machine-wide x86_64 package (needs Administrator
  rights; an interactive or already-elevated session is required).

Environment variables
---------------------

``LIBCSOUNDPATH``
    If set, absolute path to the Csound shared library to use. When set to a
    file that does not exist, :func:`ensure_csound` refuses to install another
    Csound and raises instead.

``OPCODE7DIR64``
    Plugin directory. Set or updated by the installation functions when it is
    known.

``GETCSOUND_INSTALL``
    Set to ``0``, ``false``, ``no`` or ``off`` to disable automatic
    installation. ``LIBCSOUND_INSTALL`` is accepted as a compatibility alias.

If automatic installation is disabled or unsupported, the official one-line
installers can still be used manually::

    # Linux / macOS
    curl -fsSL https://csound-plugins.github.io/getcsound.sh | bash

    # Windows (PowerShell)
    irm https://csound-plugins.github.io/getcsound.ps1 | iex
"""

from __future__ import annotations

from ._errors import CsoundInstallError, CsoundNotFoundError, GetCsoundError
from ._install import (
    ensure_csound,
    install_csound,
    install_csound_linux,
    install_csound_macos,
    install_csound_windows,
    install_disabled,
)
from ._locate import CsoundInstallation, find_csound
from ._util import run_installer, stdin_is_tty

__all__ = [
    "CsoundInstallError",
    "CsoundInstallation",
    "CsoundNotFoundError",
    "GetCsoundError",
    "ensure_csound",
    "find_csound",
    "install_csound",
    "install_csound_linux",
    "install_csound_macos",
    "install_csound_windows",
    "install_disabled",
    "run_installer",
    "stdin_is_tty",
]
