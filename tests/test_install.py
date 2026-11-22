import os
from pathlib import Path

import pytest

from getcsound import CsoundInstallError, _install, install_csound


def _make_file(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
    return path


def _make_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_install_csound_linux_noninteractive(tmp_path, monkeypatch,
                                             isolated_env):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(_install, "stdin_is_tty", lambda: False)
    lib = _make_file(tmp_path / ".local/csound/libcsound64.so")
    plugins = _make_dir(tmp_path / ".local/lib/csound/7.0/plugins64")
    calls = []

    def fake_run(cmd, failure_hint=""):
        calls.append(list(cmd))

    monkeypatch.setattr(_install, "run_installer", fake_run)

    installation = _install.install_csound_linux(quiet=True)

    assert installation.libpath == lib.resolve()
    assert installation.plugindir == plugins.resolve()
    assert os.environ["LIBCSOUNDPATH"] == str(lib.resolve())
    assert os.environ["OPCODE7DIR64"] == str(plugins.resolve())

    (cmd,) = calls
    assert cmd[0] == "bash"
    assert cmd[1].endswith("getcsound.sh")
    assert "--no-risset" in cmd
    assert "--user" in cmd
    assert "-y" in cmd
    assert "--quiet" in cmd


def test_install_csound_linux_interactive(tmp_path, monkeypatch, isolated_env):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(_install, "stdin_is_tty", lambda: True)
    _make_file(tmp_path / ".local/csound/libcsound64.so")
    _make_dir(tmp_path / ".local/lib/csound/7.0/plugins64")
    calls = []
    monkeypatch.setattr(_install, "run_installer",
                        lambda cmd, failure_hint="": calls.append(list(cmd)))

    _install.install_csound_linux(quiet=False)

    (cmd,) = calls
    assert "--user" not in cmd
    assert "-y" not in cmd
    assert "--quiet" not in cmd


def test_install_csound_linux_requires_plugin_dir(tmp_path, monkeypatch,
                                                  isolated_env):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(_install, "stdin_is_tty", lambda: False)
    _make_file(tmp_path / ".local/csound/libcsound64.so")
    monkeypatch.setattr(_install, "run_installer",
                        lambda cmd, failure_hint="": None)

    with pytest.raises(CsoundInstallError, match="plugin directory"):
        _install.install_csound_linux()


def test_install_csound_linux_missing_library(tmp_path, monkeypatch,
                                             isolated_env):
    missing = tmp_path / "missing.so"
    monkeypatch.setattr(_install, "stdin_is_tty", lambda: False)
    monkeypatch.setattr(_install, "run_installer",
                        lambda cmd, failure_hint="": None)
    monkeypatch.setattr(_install, "_linux_candidates",
                        lambda: [_install.CsoundInstallation(missing)])

    with pytest.raises(CsoundInstallError, match="libcsound64.so was not found"):
        _install.install_csound_linux()


def test_install_csound_macos(tmp_path, monkeypatch, isolated_env):
    app = tmp_path / "Csound"
    lib = _make_file(app / "CsoundLib64.framework/CsoundLib64")
    plugins = _make_dir(app / "CsoundLib64.framework/Resources/Opcodes64")
    monkeypatch.setattr(
        _install, "_macos_candidates",
        lambda: [_install.CsoundInstallation(lib, plugins)])
    calls = []
    monkeypatch.setattr(_install, "run_installer",
                        lambda cmd, failure_hint="": calls.append(list(cmd)))

    installation = _install.install_csound_macos(quiet=True)

    assert installation.libpath == lib.resolve()
    assert installation.plugindir == plugins.resolve()
    assert os.environ["LIBCSOUNDPATH"] == str(lib.resolve())
    assert os.environ["OPCODE7DIR64"] == str(plugins.resolve())

    (cmd,) = calls
    assert cmd[0] == "bash"
    assert cmd[1].endswith("getcsound.sh")
    assert "--no-risset" in cmd
    assert "--quiet" in cmd


def test_install_csound_macos_missing_library(tmp_path, monkeypatch,
                                              isolated_env):
    missing = tmp_path / "missing"
    monkeypatch.setattr(
        _install, "_macos_candidates",
        lambda: [_install.CsoundInstallation(missing)])
    monkeypatch.setattr(_install, "run_installer",
                        lambda cmd, failure_hint="": None)

    with pytest.raises(CsoundInstallError, match="CsoundLib64"):
        _install.install_csound_macos()


def test_install_csound_windows(tmp_path, monkeypatch, isolated_env):
    program_files = tmp_path / "Program Files"
    monkeypatch.setattr(_install.platform, "machine", lambda: "AMD64")
    monkeypatch.setattr(_install, "_find_powershell", lambda: "/bin/true")
    monkeypatch.setattr(_install, "_windows_is_admin",
                        lambda powershell=None: True)
    monkeypatch.setenv("ProgramW6432", str(program_files))
    monkeypatch.delenv("ProgramFiles", raising=False)
    dll = _make_file(program_files / "Csound7/bin/csound64.dll")
    plugins = _make_dir(program_files / "Csound7/plugins64")
    calls = []
    monkeypatch.setattr(_install, "run_installer",
                        lambda cmd, failure_hint="": calls.append(list(cmd)))

    installation = _install.install_csound_windows()

    assert installation.libpath == dll.resolve()
    assert installation.plugindir == plugins.resolve()
    assert installation.bindir == (program_files / "Csound7/bin").resolve()
    assert os.environ["LIBCSOUNDPATH"] == str(dll.resolve())
    assert os.environ["OPCODE7DIR64"] == str(plugins.resolve())
    assert os.environ["PATH"].split(os.pathsep)[0] == str(
        (program_files / "Csound7/bin").resolve())

    (cmd,) = calls
    assert cmd[0] == "/bin/true"
    assert "-NoProfile" in cmd
    assert "-ExecutionPolicy" in cmd
    assert cmd[-3].endswith("getcsound.ps1")
    assert cmd[-2] == "--no-risset"
    assert cmd[-1] == "--quiet"


def test_find_powershell_prefers_pwsh(monkeypatch):
    monkeypatch.setattr(
        _install.shutil, "which",
        lambda name: {"pwsh": "/pwsh", "powershell": "/powershell"}.get(name))
    assert _install._find_powershell() == "/pwsh"


def test_find_powershell_falls_back_to_windows_powershell(monkeypatch):
    monkeypatch.setattr(
        _install.shutil, "which",
        lambda name: "/powershell" if name == "powershell" else None)
    assert _install._find_powershell() == "/powershell"


def test_windows_is_admin_true():
    assert _install._windows_is_admin("/bin/true") is True


def test_windows_is_admin_false():
    assert _install._windows_is_admin("/bin/false") is False


def test_windows_is_admin_missing_powershell():
    assert _install._windows_is_admin("/nonexistent/powershell") is False


def test_install_csound_windows_rejects_arm64(monkeypatch):
    monkeypatch.setattr(_install.platform, "machine", lambda: "ARM64")
    with pytest.raises(CsoundInstallError, match="ARM64"):
        _install.install_csound_windows()


def test_install_csound_windows_requires_powershell(monkeypatch):
    monkeypatch.setattr(_install.platform, "machine", lambda: "AMD64")
    monkeypatch.setattr(_install.shutil, "which", lambda name: None)
    with pytest.raises(CsoundInstallError, match="PowerShell"):
        _install.install_csound_windows()


def test_install_csound_windows_requires_admin_without_tty(monkeypatch):
    monkeypatch.setattr(_install.platform, "machine", lambda: "AMD64")
    monkeypatch.setattr(_install, "_find_powershell", lambda: "/bin/true")
    monkeypatch.setattr(_install, "_windows_is_admin",
                        lambda powershell=None: False)
    monkeypatch.setattr(_install, "stdin_is_tty", lambda: False)
    with pytest.raises(CsoundInstallError, match="admin rights"):
        _install.install_csound_windows()


@pytest.mark.parametrize("platform_name,function_name", [
    ("linux", "install_csound_linux"),
    ("darwin", "install_csound_macos"),
    ("win32", "install_csound_windows"),
])
def test_install_csound_dispatches(platform_name, function_name, monkeypatch):
    sentinel = object()
    monkeypatch.setattr(_install.sys, "platform", platform_name)
    monkeypatch.setattr(_install, function_name, lambda quiet=True: sentinel)

    assert install_csound(quiet=False) is sentinel


def test_install_csound_unsupported_platform(monkeypatch):
    monkeypatch.setattr(_install.sys, "platform", "freebsd14")
    with pytest.raises(CsoundInstallError, match="not supported"):
        install_csound()
