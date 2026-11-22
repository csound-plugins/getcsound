import os
from pathlib import Path

from getcsound import CsoundInstallation, _locate, find_csound


def _make_file(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
    return path


def _make_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_find_linux_user_installation(tmp_path, monkeypatch, isolated_env):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(_locate.sys, "platform", "linux")
    lib = _make_file(tmp_path / ".local/csound/libcsound64.so")
    plugins = _make_dir(tmp_path / ".local/lib/csound/7.0/plugins64")

    installation = find_csound()

    assert installation is not None
    assert installation.libpath == lib.resolve()
    assert installation.plugindir == plugins.resolve()
    assert installation.bindir is None


def test_find_linux_system_installation(tmp_path, monkeypatch, isolated_env):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(_locate.sys, "platform", "linux")
    monkeypatch.setattr(_locate, "_LINUX_USER_LIB", tmp_path / "missing.so")
    lib = _make_file(tmp_path / "system/lib/libcsound64.so")
    plugins = _make_dir(tmp_path / "system/lib/csound/plugins64-7.0")
    monkeypatch.setattr(_locate, "_LINUX_SYSTEM_LIB", lib)
    monkeypatch.setattr(_locate, "_LINUX_SYSTEM_PLUGINS", plugins)

    installation = find_csound()

    assert installation is not None
    assert installation.libpath == lib.resolve()
    assert installation.plugindir == plugins.resolve()


def test_find_linux_plugin_dir_is_optional(tmp_path, monkeypatch, isolated_env):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(_locate.sys, "platform", "linux")
    lib = _make_file(tmp_path / ".local/csound/libcsound64.so")

    installation = find_csound()

    assert installation is not None
    assert installation.libpath == lib.resolve()
    assert installation.plugindir is None


def test_environment_takes_precedence(tmp_path, monkeypatch, isolated_env):
    monkeypatch.setattr(_locate.sys, "platform", "linux")
    lib = _make_file(tmp_path / "custom/libcsound64.so")
    plugins = _make_dir(tmp_path / "custom/plugins")
    monkeypatch.setenv("LIBCSOUNDPATH", str(lib))
    monkeypatch.setenv("OPCODE7DIR64", str(plugins))

    installation = find_csound()

    assert installation is not None
    assert installation.libpath == lib.resolve()
    assert installation.plugindir == plugins.resolve()


def test_bad_environment_path_is_ignored_by_find(tmp_path, monkeypatch,
                                                 isolated_env):
    monkeypatch.setattr(_locate.sys, "platform", "linux")
    monkeypatch.setenv("LIBCSOUNDPATH", str(tmp_path / "missing.so"))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(_locate, "_LINUX_USER_LIB", tmp_path / "missing-user.so")
    monkeypatch.setattr(_locate, "_LINUX_SYSTEM_LIB",
                        tmp_path / "missing-system.so")

    assert find_csound() is None


def test_unsupported_platform_returns_none(monkeypatch, isolated_env):
    monkeypatch.setattr(_locate.sys, "platform", "freebsd14")
    assert find_csound() is None


def test_find_windows_installation(tmp_path, monkeypatch, isolated_env):
    monkeypatch.setattr(_locate.sys, "platform", "win32")
    monkeypatch.setenv("ProgramW6432", str(tmp_path))
    monkeypatch.delenv("ProgramFiles", raising=False)
    dll = _make_file(tmp_path / "Csound7/bin/csound64.dll")
    plugins = _make_dir(tmp_path / "Csound7/plugins64")

    installation = find_csound()

    assert installation is not None
    assert installation.libpath == dll.resolve()
    assert installation.plugindir == plugins.resolve()
    assert installation.bindir == (tmp_path / "Csound7/bin").resolve()


def test_find_macos_installation(tmp_path, monkeypatch, isolated_env):
    monkeypatch.setattr(_locate.sys, "platform", "darwin")
    app = tmp_path / "Csound"
    lib = _make_file(app / "CsoundLib64.framework/CsoundLib64")
    plugins = _make_dir(app / "CsoundLib64.framework/Resources/Opcodes64")
    monkeypatch.setattr(_locate, "_MACOS_LIB", lib)
    monkeypatch.setattr(_locate, "_MACOS_PLUGINS", plugins)

    installation = find_csound()

    assert installation is not None
    assert installation.libpath == lib.resolve()
    assert installation.plugindir == plugins.resolve()


def test_as_env():
    installation = CsoundInstallation(Path("/lib/libcsound64.so"),
                                      Path("/lib/plugins"))
    assert installation.as_env() == {
        "LIBCSOUNDPATH": "/lib/libcsound64.so",
        "OPCODE7DIR64": "/lib/plugins",
    }


def test_as_env_without_plugins():
    installation = CsoundInstallation(Path("/lib/libcsound64.so"))
    assert installation.as_env() == {"LIBCSOUNDPATH": "/lib/libcsound64.so"}


def test_update_environ_prepends_bindir_once(tmp_path):
    bindir = _make_dir(tmp_path / "bin")
    installation = CsoundInstallation(tmp_path / "csound64.dll",
                                      bindir=bindir)
    environ = {"PATH": os.pathsep.join(["/usr/bin", "/bin"])}

    installation.update_environ(environ)
    installation.update_environ(environ)

    assert environ["LIBCSOUNDPATH"] == str(tmp_path / "csound64.dll")
    entries = environ["PATH"].split(os.pathsep)
    assert entries.count(str(bindir)) == 1
    assert entries[0] == str(bindir)


def test_update_environ_handles_empty_path(tmp_path):
    bindir = _make_dir(tmp_path / "bin")
    installation = CsoundInstallation(tmp_path / "csound64.dll",
                                      bindir=bindir)
    environ: dict[str, str] = {}

    installation.update_environ(environ)

    assert environ["PATH"] == str(bindir)
