"""End-to-end check that getcsound installs Csound and libcsound uses it.

The test installs Csound 7 through ``getcsound``, then imports ``libcsound``
with automatic installation explicitly disabled (``LIBCSOUND_INSTALL=0``) and
verifies that:

* libcsound loads the same library that getcsound installed;
* a short score can be compiled and rendered, so the library and its opcodes
  really work.

It is skipped unless ``GETCSOUND_RUN_LIBCSOUND_INTEGRATION=1`` because it
downloads and installs Csound and needs administrator rights on macOS and
Windows. The GitHub Actions workflow ``.github/workflows/ci.yml`` sets it on
Linux x86-64, macOS arm64 and Windows x86-64.
"""

from __future__ import annotations

import os
import platform
import sys
import wave
from pathlib import Path

import pytest

RUN_INTEGRATION = os.environ.get("GETCSOUND_RUN_LIBCSOUND_INTEGRATION") == "1"

pytestmark = pytest.mark.skipif(
    not RUN_INTEGRATION,
    reason="set GETCSOUND_RUN_LIBCSOUND_INTEGRATION=1 to install Csound and "
           "test the libcsound hand-off",
)

ORC = r"""
sr = 44100
ksmps = 64
nchnls = 1
0dbfs = 1

instr 1
    a1 oscili 0.5, 440
    out a1
endin
"""


def _clear_csound_env() -> None:
    for name in ("LIBCSOUNDPATH", "OPCODE7DIR64",
                 "GETCSOUND_INSTALL", "LIBCSOUND_INSTALL"):
        os.environ.pop(name, None)


def test_expected_architecture():
    expected = os.environ.get("GETCSOUND_EXPECTED_ARCH")
    if not expected:
        pytest.skip("GETCSOUND_EXPECTED_ARCH is not set")
    actual = platform.machine().lower()
    aliases = {
        "x86_64": {"x86_64", "amd64"},
        "amd64": {"x86_64", "amd64"},
        "arm64": {"arm64", "aarch64"},
        "aarch64": {"arm64", "aarch64"},
    }
    allowed = aliases.get(expected.lower(), {expected.lower()})
    assert actual in allowed, (
        f"This job is meant to run on {expected}, but the runner reports "
        f"{platform.machine()}")


def test_getcsound_install_then_libcsound(tmp_path, monkeypatch):
    import getcsound

    _clear_csound_env()

    # Force the installer so that this test does not silently pass on a runner
    # that happens to have Csound preinstalled.
    installed = getcsound.install_csound(quiet=True)
    print(f"getcsound installed: {installed}")
    assert installed.libpath.is_file()
    assert installed.plugindir is not None
    assert installed.plugindir.is_dir()
    assert os.environ["LIBCSOUNDPATH"] == str(installed.libpath)
    assert os.environ["OPCODE7DIR64"] == str(installed.plugindir)

    # ensure_csound() must find the installation that was just made and must
    # not run the installer again.
    ensured = getcsound.ensure_csound()
    assert ensured == installed

    # From here on libcsound must not install anything by itself. If it cannot
    # find the library that getcsound installed, the import below fails.
    os.environ["LIBCSOUND_INSTALL"] = "0"
    assert "libcsound" not in sys.modules

    import libcsound

    print(f"libcsound imported: version={libcsound.VERSION} "
          f"path={libcsound.libcsoundPath}")
    assert libcsound.VERSION >= 7000
    assert Path(libcsound.libcsoundPath).resolve() == installed.libpath.resolve()

    # Render a short WAV offline. The output header is finalized on destroy().
    monkeypatch.chdir(tmp_path)
    libcsound.csoundInitialize(signalHandler=False)
    cs = libcsound.Csound()
    try:
        cs.setOption("-oout.wav")
        cs.setOption("--wave")
        ret = cs.compileOrc(ORC)
        assert ret == 0, f"compileOrc() returned {ret}"
        cs.start()
        cs.event("i", [1, 0, 0.1])
        cs.event("e", [0, 0.2])
        while not cs.performKsmps():
            pass
    finally:
        cs.destroy()

    outfile = tmp_path / "out.wav"
    assert outfile.is_file(), "Csound did not write out.wav"
    with wave.open(str(outfile), "rb") as wf:
        nframes = wf.getnframes()
        print(f"Rendered {outfile}: channels={wf.getnchannels()} "
              f"samplerate={wf.getframerate()} frames={nframes}")
        assert nframes > 0
