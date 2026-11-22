import os

import pytest

from getcsound import (
    CsoundInstallation,
    CsoundNotFoundError,
    _install,
    ensure_csound,
    install_disabled,
)


def _fake_installation(tmp_path):
    lib = tmp_path / "libcsound64.so"
    lib.touch()
    return CsoundInstallation(lib)


def test_ensure_returns_existing_installation(tmp_path, monkeypatch,
                                              isolated_env):
    installation = _fake_installation(tmp_path)
    monkeypatch.setattr(_install, "find_csound", lambda: installation)

    result = ensure_csound()

    assert result is installation
    assert os.environ["LIBCSOUNDPATH"] == str(installation.libpath)


def test_ensure_rejects_missing_libcsoundpath(tmp_path, monkeypatch,
                                              isolated_env):
    missing = tmp_path / "missing.so"
    monkeypatch.setenv("LIBCSOUNDPATH", str(missing))

    def fail():
        raise AssertionError("find_csound must not run with an invalid LIBCSOUNDPATH")

    monkeypatch.setattr(_install, "find_csound", fail)

    with pytest.raises(CsoundNotFoundError, match="LIBCSOUNDPATH"):
        ensure_csound()


def test_ensure_disabled_raises(monkeypatch, isolated_env):
    monkeypatch.setattr(_install, "find_csound", lambda: None)
    monkeypatch.setenv("GETCSOUND_INSTALL", "0")

    with pytest.raises(CsoundNotFoundError, match="disabled"):
        ensure_csound()


def test_ensure_install_false_overrides_environment(monkeypatch, isolated_env):
    monkeypatch.setattr(_install, "find_csound", lambda: None)

    with pytest.raises(CsoundNotFoundError):
        ensure_csound(install=False)


def test_ensure_installs_when_not_found(tmp_path, monkeypatch, isolated_env):
    installation = _fake_installation(tmp_path)
    calls = []
    monkeypatch.setattr(_install, "find_csound", lambda: None)
    monkeypatch.setattr(_install, "install_csound",
                        lambda quiet=True: calls.append(quiet) or installation)

    result = ensure_csound(quiet=False)

    assert result is installation
    assert calls == [False]


def test_ensure_install_true_overrides_disabled_environment(
        tmp_path, monkeypatch, isolated_env):
    installation = _fake_installation(tmp_path)
    monkeypatch.setattr(_install, "find_csound", lambda: None)
    monkeypatch.setattr(_install, "install_csound",
                        lambda quiet=True: installation)
    monkeypatch.setenv("GETCSOUND_INSTALL", "0")

    assert ensure_csound(install=True) is installation


@pytest.mark.parametrize("value", ["0", "false", "FALSE", "no", "off", " 0 "])
def test_install_disabled_values(value, monkeypatch, isolated_env):
    monkeypatch.setenv("GETCSOUND_INSTALL", value)
    assert install_disabled() is True


@pytest.mark.parametrize("value", ["1", "true", "yes", "on", ""])
def test_install_enabled_values(value, monkeypatch, isolated_env):
    monkeypatch.setenv("GETCSOUND_INSTALL", value)
    assert install_disabled() is False


def test_liBCSOUND_install_alias(monkeypatch, isolated_env):
    monkeypatch.setenv("LIBCSOUND_INSTALL", "0")
    assert install_disabled() is True


def test_getcsound_install_takes_precedence(monkeypatch, isolated_env):
    monkeypatch.setenv("GETCSOUND_INSTALL", "1")
    monkeypatch.setenv("LIBCSOUND_INSTALL", "0")
    assert install_disabled() is False
