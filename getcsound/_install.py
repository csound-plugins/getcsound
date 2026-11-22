"""Install Csound 7 by running the official bundled installers.

The development version of these installers lives at
https://github.com/csound-plugins/csound-plugins.github.io and is published at
https://csound-plugins.github.io/. Copies are bundled under
``getcsound/data/`` so that installing Csound does not depend on any external
Python package.
"""

from __future__ import annotations

import importlib.resources
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from ._errors import CsoundInstallError, CsoundNotFoundError
from ._locate import (
    CsoundInstallation,
    _linux_candidates,
    _macos_candidates,
    _windows_candidates,
    find_csound,
)
from ._util import logger, run_installer, stdin_is_tty

_CSOUND_SH_URL = "https://csound-plugins.github.io/getcsound.sh"
_CSOUND_PS1_URL = "https://csound-plugins.github.io/getcsound.ps1"

_DISABLED_VALUES = {"0", "false", "no", "off"}

_ADMIN_CHECK = (
    "$p = New-Object Security.Principal.WindowsPrincipal("
    "[Security.Principal.WindowsIdentity]::GetCurrent()); "
    "if ($p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) "
    "{ exit 0 } else { exit 1 }"
)


def _bundled_installer(name: str):
    installer = importlib.resources.files(__package__).joinpath("data", name)
    if not installer.is_file():
        raise CsoundInstallError(f"The bundled installer was not found: {installer}")
    return installer


def _manual_install_hint() -> str:
    if sys.platform.startswith("win"):
        return ("Csound 7 can be installed from a PowerShell session with:\n"
                f"    irm {_CSOUND_PS1_URL} | iex")
    if sys.platform in ("linux", "darwin"):
        return ("Csound 7 can be installed with:\n"
                f"    curl -fsSL {_CSOUND_SH_URL} | bash")
    return "See https://github.com/csound/csound/releases for Csound 7 packages."


def install_disabled() -> bool:
    """Return True if automatic installation has been disabled by the user.

    ``GETCSOUND_INSTALL`` is checked first; ``LIBCSOUND_INSTALL`` is accepted as
    a compatibility alias. A value of ``0``, ``false``, ``no`` or ``off``
    disables installation.
    """
    for name in ("GETCSOUND_INSTALL", "LIBCSOUND_INSTALL"):
        value = os.environ.get(name)
        if value is not None:
            return value.strip().lower() in _DISABLED_VALUES
    return False


def install_csound_linux(quiet: bool = True) -> CsoundInstallation:
    """Install Csound 7 on Linux by running the bundled installer.

    This runs the bundled copy of the official installer at
    https://csound-plugins.github.io/getcsound.sh with bash. The installer
    downloads the portable Csound 7 release from the
    ``csound-plugins/csound-plugins`` GitHub repository, verifies its SHA-256
    checksum and installs it. ``--no-risset`` is always passed so that risset is
    never installed.

    When running inside a terminal the installer is run interactively;
    otherwise it is run with ``--user -y`` so that Csound is installed to
    ``~/.local/csound`` without prompting.

    After a successful installation, the environment variables
    ``LIBCSOUNDPATH`` and ``OPCODE7DIR64`` point to the installed library and
    plugin directory, so that the current process can find Csound without
    opening a new terminal.

    Args:
        quiet: only print essential installer output.

    Returns:
        the newly installed Csound installation.

    Raises:
        CsoundInstallError: if the bundled installer could not be found or
            failed, or if Csound could not be located after installation.
    """
    installer = _bundled_installer("getcsound.sh")
    hint = ("Csound can also be installed manually:\n"
            f"    curl -fsSL {_CSOUND_SH_URL} | bash")

    # as_file() yields a real filesystem path, extracting to a temporary file
    # first when the package is loaded from an archive (e.g. a zip).
    with importlib.resources.as_file(installer) as script:
        options = ["bash", str(script), "--no-risset"]
        if not stdin_is_tty():
            # No terminal (e.g. on CI): install for the current user and answer
            # yes to any prompt, so that no password is needed and the
            # installer does not block waiting for input.
            options.extend(["--user", "-y"])
        if quiet:
            options.append("--quiet")
        run_installer(options, failure_hint=hint)

    # Make the freshly installed Csound available to the current process.
    for candidate in _linux_candidates():
        if not candidate.libpath.exists():
            continue
        if candidate.plugindir is None or not candidate.plugindir.is_dir():
            raise CsoundInstallError(
                f"Csound 7 installation failed: plugin directory "
                f"'{candidate.plugindir}' was not found")
        installation = CsoundInstallation(candidate.libpath.resolve(),
                                          candidate.plugindir.resolve())
        installation.update_environ()
        logger.info("Csound installed successfully to %s", candidate.libpath.parent)
        return installation

    raise CsoundInstallError(
        "Csound 7 installation failed: libcsound64.so was not found in any of "
        "the standard locations")


def install_csound_macos(quiet: bool = True) -> CsoundInstallation:
    """Install the latest Csound 7 .pkg for macOS by running the installer.

    The official Csound 7 macOS package is produced by the ``csound_builds``
    workflow of the csound/csound repository on the ``develop`` branch and is
    installed with the system ``installer`` under sudo. An interactive terminal
    session is used when available (so sudo can prompt for the password). When
    there is no terminal (e.g. on CI) the install still succeeds if sudo is
    configured to run password-less.

    This runs the bundled copy of the one-line installer used at
    https://csound-plugins.github.io/getcsound.sh, which resolves the latest
    successful workflow run, downloads its ``csound-7.*-macos*`` artifact
    through the anonymous nightly.link mirror and installs the extracted .pkg.
    ``--no-risset`` is always passed so that risset is never installed.

    After installation the environment variables ``LIBCSOUNDPATH`` and
    ``OPCODE7DIR64`` point to the installed library and plugin directory, so
    that the current process can find Csound immediately without opening a new
    session.

    Args:
        quiet: only print essential installer output.

    Returns:
        the newly installed Csound installation.

    Raises:
        CsoundInstallError: if the bundled installer could not be found or
            failed, or if no Csound installation could be located afterwards.
    """
    installer = _bundled_installer("getcsound.sh")
    hint = ("The Csound macOS .pkg is installed with sudo and needs an "
            "interactive terminal (or passwordless sudo).\n"
            "Alternatively, Csound can be installed manually:\n"
            f"    curl -fsSL {_CSOUND_SH_URL} | bash")
    with importlib.resources.as_file(installer) as script:
        args = ["bash", str(script), "--no-risset"]
        if quiet:
            args.append("--quiet")
        run_installer(args, failure_hint=hint)

    for candidate in _macos_candidates():
        if not candidate.libpath.exists():
            continue
        installation = CsoundInstallation(
            candidate.libpath.resolve(),
            candidate.plugindir.resolve()
            if candidate.plugindir is not None and candidate.plugindir.is_dir()
            else None)
        installation.update_environ()
        logger.info("Csound installed successfully to %s",
                    candidate.libpath.parents[1])
        return installation

    raise CsoundInstallError(
        "Csound 7 installation failed: CsoundLib64 was not found in "
        "/Applications/Csound")


def _find_powershell() -> str:
    # Prefer PowerShell 7. Windows PowerShell 5.1's Expand-Archive -Force can
    # fail with "Cannot find an overload for ExtractToDirectory ... argument
    # count: 3" on .NET Framework, so use pwsh when it is available and fall
    # back to the built-in powershell otherwise.
    powershell = shutil.which("pwsh") or shutil.which("powershell")
    if not powershell:
        raise CsoundInstallError(
            "PowerShell was not found. It is needed to install Csound on "
            "Windows.\nAlternatively, Csound can be installed manually:\n"
            f"    irm {_CSOUND_PS1_URL} | iex")
    return powershell


def _windows_is_admin(powershell: str | None = None) -> bool:
    """Return True if the current Windows session is elevated.

    This asks PowerShell directly, so it works without :mod:`ctypes` (which
    ``getcsound`` deliberately does not use). Returns False when the check
    cannot confirm elevation, so callers fail with a helpful message rather
    than assuming admin rights.
    """
    if powershell is None:
        powershell = shutil.which("pwsh") or shutil.which("powershell")
    if not powershell:
        logger.debug("Could not determine Windows elevation status: "
                     "PowerShell was not found")
        return False
    try:
        result = subprocess.run(
            [powershell, "-NoProfile", "-NonInteractive", "-Command", _ADMIN_CHECK],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as e:
        logger.debug("Could not determine Windows elevation status: %s", e)
        return False
    return result.returncode == 0


def install_csound_windows(quiet: bool = True) -> CsoundInstallation:
    """Install the latest Csound 7 for Windows by running the installer.

    This runs the bundled copy of the official installer at
    https://csound-plugins.github.io/getcsound.ps1 with Windows PowerShell. The
    installer resolves the latest successful ``csound_builds`` workflow run of
    the ``csound/csound`` repository on the ``develop`` branch, downloads the
    Windows x86_64 Inno Setup package and installs it silently to
    ``%ProgramFiles%\\Csound7``. Windows on ARM64 is not supported yet.

    The package is installed machine-wide and needs admin rights: when the
    current session is not elevated the installer triggers a UAC prompt, so an
    interactive (or pre-elevated) session is required. On CI runners the
    session is usually already elevated. ``--no-risset`` is always passed so
    that risset is never installed.

    After a successful installation the environment variables
    ``LIBCSOUNDPATH`` and ``OPCODE7DIR64`` point to the installed library and
    plugin folder, and the Csound ``bin`` directory is prepended to ``PATH``,
    so that the current process can find Csound immediately without opening a
    new terminal.

    Args:
        quiet: pass ``--quiet`` to the installer to only print essential
            output.

    Returns:
        the newly installed Csound installation.

    Raises:
        CsoundInstallError: if the architecture is unsupported, PowerShell or
            the bundled installer could not be found, the session is not
            elevated, the installer failed, or no Csound installation could be
            located afterwards.
    """
    machine = platform.machine().lower()
    if machine in ("arm64", "aarch64"):
        raise CsoundInstallError(
            f"Windows on ARM64 (detected: '{platform.machine()}') is not "
            "supported by the automatic Csound installer, which provides an "
            "x86_64 package only.\n"
            "Install Csound manually (e.g. from "
            "https://github.com/csound/csound/releases) and point "
            "LIBCSOUNDPATH at the installed csound64.dll.")

    powershell = _find_powershell()

    if not _windows_is_admin(powershell):
        if stdin_is_tty():
            logger.warning("The Csound Windows installer installs machine-wide "
                           "and needs admin rights; the installer will request "
                           "elevation (UAC prompt).")
        else:
            raise CsoundInstallError(
                "The Csound Windows installer installs machine-wide and needs "
                "admin rights, but the current session is not elevated and "
                "there is no interactive terminal to show the UAC prompt.\n"
                "Run from an interactive (or already elevated) PowerShell "
                "session, or install Csound manually:\n"
                f"    irm {_CSOUND_PS1_URL} | iex")

    installer = _bundled_installer("getcsound.ps1")
    hint = ("The Csound Windows installer installs machine-wide and needs "
            "admin rights: run it from an interactive (or elevated) "
            "PowerShell session.\n"
            "Alternatively, Csound can be installed manually:\n"
            f"    irm {_CSOUND_PS1_URL} | iex")
    with importlib.resources.as_file(installer) as script:
        args = [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(script), "--no-risset"]
        if quiet:
            args.append("--quiet")
        run_installer(args, failure_hint=hint)

    for candidate in _windows_candidates():
        if not candidate.libpath.is_file():
            continue
        installation = CsoundInstallation(
            candidate.libpath.resolve(),
            candidate.plugindir.resolve()
            if candidate.plugindir is not None and candidate.plugindir.is_dir()
            else None,
            candidate.bindir.resolve()
            if candidate.bindir is not None and candidate.bindir.is_dir()
            else None)
        installation.update_environ()
        logger.info("Csound installed successfully to %s",
                    candidate.libpath.parent.parent)
        return installation

    first = _windows_candidates()[0]
    raise CsoundInstallError(
        f"Csound 7 installation failed: csound64.dll was not found in "
        f"'{first.bindir}'")


def install_csound(quiet: bool = True) -> CsoundInstallation:
    """Install Csound 7 for the current platform.

    Dispatches to :func:`install_csound_linux`, :func:`install_csound_macos`
    or :func:`install_csound_windows`. The newly installed installation is
    returned and the environment of the current process is updated so that
    ``LIBCSOUNDPATH`` and ``OPCODE7DIR64`` point at it.
    """
    if sys.platform == "linux":
        return install_csound_linux(quiet=quiet)
    if sys.platform == "darwin":
        return install_csound_macos(quiet=quiet)
    if sys.platform.startswith("win"):
        return install_csound_windows(quiet=quiet)
    raise CsoundInstallError(
        f"Automatic Csound installation is not supported on {sys.platform!r}.\n"
        + _manual_install_hint())


def ensure_csound(quiet: bool = True,
                  install: bool | None = None) -> CsoundInstallation:
    """Return a usable Csound 7 installation, installing it if necessary.

    This is the main entry point for packages that want Csound to be available
    without asking the user to install it manually. If Csound is already
    installed, its environment variables are applied to the current process.
    Otherwise the official installer is run and the result is returned.

    Args:
        quiet: only print essential installer output.
        install: whether to install Csound when it cannot be found. If None,
            automatic installation is enabled unless ``GETCSOUND_INSTALL`` (or
            the compatibility alias ``LIBCSOUND_INSTALL``) is set to ``0``,
            ``false``, ``no`` or ``off``.

    Returns:
        the Csound installation. ``LIBCSOUNDPATH`` and, when known,
        ``OPCODE7DIR64`` are set in :data:`os.environ`.

    Raises:
        CsoundNotFoundError: if Csound was not found, ``LIBCSOUNDPATH`` points
            to a missing file, or installation is disabled.
        CsoundInstallError: if automatic installation was attempted and
            failed.
    """
    libcsoundpath = os.environ.get("LIBCSOUNDPATH")
    if libcsoundpath and not Path(libcsoundpath).expanduser().is_file():
        raise CsoundNotFoundError(
            f"The environment variable LIBCSOUNDPATH '{libcsoundpath}' does "
            "not point to an existing file")

    found = find_csound()
    if found is not None:
        found.update_environ()
        return found

    if install is None:
        install = not install_disabled()
    if not install:
        raise CsoundNotFoundError(
            "Csound 7 was not found and automatic installation is disabled.\n"
            + _manual_install_hint())

    return install_csound(quiet=quiet)
