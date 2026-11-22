import os

import pytest


@pytest.fixture
def isolated_env(monkeypatch):
    """Replace os.environ with a private dict for the duration of a test."""
    monkeypatch.setattr(os, "environ", dict(os.environ))
    for name in ("LIBCSOUNDPATH", "OPCODE7DIR64",
                 "GETCSOUND_INSTALL", "LIBCSOUND_INSTALL"):
        os.environ.pop(name, None)
    return os.environ
