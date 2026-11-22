import pytest

from getcsound import CsoundInstallError, _util, run_installer


def test_run_installer_noninteractive(monkeypatch, capsys):
    monkeypatch.setattr(_util, "stdin_is_tty", lambda: False)

    run_installer(["bash", "-c", "echo hello"])

    assert "hello" in capsys.readouterr().out


def test_run_installer_noninteractive_failure(monkeypatch, capsys):
    monkeypatch.setattr(_util, "stdin_is_tty", lambda: False)

    with pytest.raises(CsoundInstallError) as excinfo:
        run_installer(["bash", "-c", "echo out; echo err >&2; exit 3"],
                      failure_hint="install this manually")

    message = str(excinfo.value)
    assert "status 3" in message
    assert "Command: bash -c" in message
    assert "out" in message
    assert "err" in message
    assert "install this manually" in message
    assert "out" in capsys.readouterr().out


def test_run_installer_interactive_failure(monkeypatch):
    monkeypatch.setattr(_util, "stdin_is_tty", lambda: True)

    with pytest.raises(CsoundInstallError, match="status 7"):
        run_installer(["bash", "-c", "exit 7"])


def test_run_installer_missing_command(monkeypatch):
    monkeypatch.setattr(_util, "stdin_is_tty", lambda: False)

    with pytest.raises(CsoundInstallError, match="Could not run installer"):
        run_installer(["/nonexistent/getcsound-test-command"])


def test_stdin_is_tty_without_stdin(monkeypatch):
    monkeypatch.setattr(_util.sys, "stdin", None)
    assert _util.stdin_is_tty() is False
