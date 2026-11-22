"""Locate an existing Csound 7 installation without importing libcsound.

The locations listed here are the ones used by the official Csound 7
installers on Linux, macOS and Windows. Set ``LIBCSOUNDPATH`` (and optionally
``OPCODE7DIR64``) to point at an installation in a non-standard location.
"""

from __future__ import annotations

import os
import sys
from collections.abc import MutableMapping
from dataclasses import dataclass
from pathlib import Path

_LINUX_USER_LIB = Path(".local/csound/libcsound64.so")
_LINUX_USER_PLUGINS = Path(".local/lib/csound/7.0/plugins64")
_LINUX_SYSTEM_LIB = Path("/usr/local/lib/libcsound64.so")
_LINUX_SYSTEM_PLUGINS = Path("/usr/local/lib/csound/plugins64-7.0")

_MACOS_CSOUND_DIR = Path("/Applications/Csound")
_MACOS_LIB = (_MACOS_CSOUND_DIR / "CsoundLib64.framework" / "CsoundLib64")
_MACOS_PLUGINS = (_MACOS_CSOUND_DIR / "CsoundLib64.framework" / "Resources"
                  / "Opcodes64")

_WINDOWS_CSOUND_DIR = "Csound7"
# Csound 7 uses csound7_64.dll (double precision); csound64.dll is the
# Csound 6 name and is kept as a fallback for older Csound 7 builds.
_WINDOWS_LIB_NAMES = ("csound7_64.dll", "csound64.dll")
_WINDOWS_PLUGINS = Path("plugins64")


@dataclass(frozen=True)
class CsoundInstallation:
    """A Csound 7 installation found on this system.

    Attributes:
        libpath: absolute path to the Csound shared library.
        plugindir: directory containing the Csound plugins, if known.
        bindir: directory containing the Csound DLLs on Windows, if known. It
            is added to ``PATH`` so that dependencies such as libsndfile can be
            resolved when the library is loaded.
    """

    libpath: Path
    plugindir: Path | None = None
    bindir: Path | None = None

    def as_env(self) -> dict[str, str]:
        """Return the environment variables needed to use this installation.

        The keys are the ones understood by ``libcsound`` (and by other
        packages using Csound):

        * ``LIBCSOUNDPATH``: absolute path to the Csound shared library.
        * ``OPCODE7DIR64``: plugin directory, if known.
        """
        env = {"LIBCSOUNDPATH": str(self.libpath)}
        if self.plugindir is not None:
            env["OPCODE7DIR64"] = str(self.plugindir)
        return env

    def update_environ(self,
                       environ: MutableMapping[str, str] | None = None) -> None:
        """Make this installation available to the current process.

        Sets ``LIBCSOUNDPATH`` and, when known, ``OPCODE7DIR64``. On Windows
        the ``bin`` directory is also prepended to ``PATH`` (without creating
        duplicates), because dependent DLLs are resolved through it.

        Args:
            environ: mapping to update. Defaults to :data:`os.environ`.
        """
        environ = os.environ if environ is None else environ
        environ.update(self.as_env())
        if self.bindir is None:
            return

        bindir = str(self.bindir)
        current = environ.get("PATH", "")
        entries = current.split(os.pathsep) if current else []
        if bindir not in entries:
            entries.insert(0, bindir)
        environ["PATH"] = os.pathsep.join(entries)


def _normalize(installation: CsoundInstallation) -> CsoundInstallation | None:
    """Return an installation with only existing paths, or None."""
    libpath = installation.libpath
    if not libpath.is_file():
        return None
    plugindir = installation.plugindir
    if plugindir is not None and not plugindir.is_dir():
        plugindir = None
    bindir = installation.bindir
    if bindir is not None and not bindir.is_dir():
        bindir = None
    return CsoundInstallation(libpath.resolve(),
                              plugindir.resolve() if plugindir is not None else None,
                              bindir.resolve() if bindir is not None else None)


def _linux_candidates() -> list[CsoundInstallation]:
    home = Path.home()
    return [
        CsoundInstallation(home / _LINUX_USER_LIB, home / _LINUX_USER_PLUGINS),
        CsoundInstallation(_LINUX_SYSTEM_LIB, _LINUX_SYSTEM_PLUGINS),
    ]


def _macos_candidates() -> list[CsoundInstallation]:
    return [CsoundInstallation(_MACOS_LIB, _MACOS_PLUGINS)]


def _windows_candidates() -> list[CsoundInstallation]:
    candidates: list[CsoundInstallation] = []
    seen: set[str] = set()
    for var in ("ProgramW6432", "ProgramFiles"):
        value = os.environ.get(var)
        if value and value not in seen:
            seen.add(value)
            candidates.extend(_windows_candidates_for(Path(value)))
    # This mirrors the fallback used by the installers when the environment
    # variable is not set.
    if r"C:\Program Files" not in seen:
        candidates.extend(_windows_candidates_for(Path(r"C:\Program Files")))
    return candidates


def _windows_candidates_for(program_files: Path) -> list[CsoundInstallation]:
    csound_dir = program_files / _WINDOWS_CSOUND_DIR
    return [
        CsoundInstallation(csound_dir / "bin" / libname,
                           csound_dir / _WINDOWS_PLUGINS,
                           csound_dir / "bin")
        for libname in _WINDOWS_LIB_NAMES
    ]


def _from_environment() -> CsoundInstallation | None:
    value = os.environ.get("LIBCSOUNDPATH")
    if not value:
        return None
    libpath = Path(value).expanduser()
    if not libpath.is_file():
        return None

    plugindir: Path | None = None
    plugins = os.environ.get("OPCODE7DIR64")
    if plugins:
        candidate = Path(plugins).expanduser()
        if candidate.is_dir():
            plugindir = candidate

    bindir: Path | None = None
    if sys.platform.startswith("win"):
        candidate = libpath.parent
        if candidate.is_dir():
            bindir = candidate
    return _normalize(CsoundInstallation(libpath, plugindir, bindir))


def find_csound() -> CsoundInstallation | None:
    """Find an existing Csound 7 installation.

    ``LIBCSOUNDPATH`` is checked first. If it is unset or does not point to an
    existing file, the standard installation locations for the current
    platform are searched. No installation is attempted and the environment is
    not modified.

    Returns:
        the installation, or None if no Csound library was found.
    """
    from_env = _from_environment()
    if from_env is not None:
        return from_env

    if sys.platform == "linux":
        candidates = _linux_candidates()
    elif sys.platform == "darwin":
        candidates = _macos_candidates()
    elif sys.platform.startswith("win"):
        candidates = _windows_candidates()
    else:
        return None

    for candidate in candidates:
        installation = _normalize(candidate)
        if installation is not None:
            return installation
    return None
