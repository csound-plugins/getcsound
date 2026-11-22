import ast
import os
import subprocess
import sys
from pathlib import Path

import getcsound

PACKAGE_DIR = Path(getcsound.__file__).parent


def test_public_api_is_exported():
    for name in getcsound.__all__:
        assert hasattr(getcsound, name), name


def test_package_does_not_import_ctypes_or_libcsound():
    """getcsound must remain usable without ctypes or libcsound."""
    forbidden = {"ctypes", "libcsound"}
    for path in PACKAGE_DIR.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
            else:
                continue
            for module in modules:
                assert module.split(".")[0] not in forbidden, (
                    f"{path} imports {module}")


def test_import_loads_no_ctypes():
    """A fresh interpreter must not have ctypes in sys.modules after import."""
    code = ("import sys, getcsound; "
            "sys.exit(1 if 'ctypes' in sys.modules else 0)")
    env = os.environ.copy()
    root = str(PACKAGE_DIR.parent)
    env["PYTHONPATH"] = os.pathsep.join(
        [root] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
    result = subprocess.run([sys.executable, "-c", code], env=env,
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr


def test_import_has_no_side_effects():
    """Importing getcsound must not touch Csound environment variables."""
    code = ("import os, getcsound; "
            "print(os.environ.get('LIBCSOUNDPATH', '')); "
            "print(os.environ.get('OPCODE7DIR64', ''))")
    env = os.environ.copy()
    for name in ("LIBCSOUNDPATH", "OPCODE7DIR64"):
        env.pop(name, None)
    root = str(PACKAGE_DIR.parent)
    env["PYTHONPATH"] = os.pathsep.join(
        [root] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
    result = subprocess.run([sys.executable, "-c", code], env=env,
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.splitlines() == ["", ""]
