import os
from pathlib import Path

import pytest

import getcsound

DATA_DIR = Path(getcsound.__file__).parent / "data"
CANONICAL_DIR = Path(os.environ.get(
    "GETCSOUND_INSTALLER_SRC",
    Path.home() / "dev" / "csound" / "installer"))

INSTALLERS = ["getcsound.sh", "getcsound.ps1"]


@pytest.mark.parametrize("name", INSTALLERS)
def test_bundled_installer_exists(name):
    path = DATA_DIR / name
    assert path.is_file()
    assert path.stat().st_size > 0


def test_bundled_installers_are_not_empty_shell_scripts():
    assert (DATA_DIR / "getcsound.sh").read_text(
        encoding="utf-8").startswith("#!/usr/bin/env bash")
    assert "Csound" in (DATA_DIR / "getcsound.ps1").read_text(
        encoding="utf-8")


@pytest.mark.skipif(not CANONICAL_DIR.is_dir(),
                    reason=f"canonical installer source not found: {CANONICAL_DIR}")
@pytest.mark.parametrize("name", INSTALLERS)
def test_bundled_installers_match_canonical_source(name):
    canonical = CANONICAL_DIR / name
    assert canonical.is_file()
    assert (DATA_DIR / name).read_bytes() == canonical.read_bytes(), (
        f"{DATA_DIR / name} is out of sync with {canonical}; run "
        "scripts/sync-installers.sh")
