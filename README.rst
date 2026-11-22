=========
getcsound
=========

Install Csound 7 from Python, with no runtime dependencies.

``getcsound`` is a small, pure-Python package that makes Csound available to
other Python packages. A package using Csound can list ``getcsound`` as a
dependency and call :func:`getcsound.ensure_csound`; if Csound is not already
installed, the official Csound 7 installer is downloaded and run automatically.

``getcsound`` does **not** depend on ``libcsound`` and does **not** import
``ctypes``, so it is safe to use in pure-Python environments.


Installation
------------

.. code::

    pip install getcsound


Usage
-----

.. code-block:: python

    from getcsound import ensure_csound

    installation = ensure_csound()
    print(installation.libpath)
    print(installation.plugindir)

    # LIBCSOUNDPATH and OPCODE7DIR64 now point at the installation, so any
    # Csound binding imported afterwards can find it.
    import libcsound

Importing ``getcsound`` is side-effect free; installation only happens when
``ensure_csound()`` (or one of the ``install_csound_*`` functions) is called.

To locate an existing installation without installing anything and without
changing the environment, use ``find_csound()``. It returns a
``CsoundInstallation`` or ``None``. Only the locations used by the official
Csound 7 installers are searched; set ``LIBCSOUNDPATH`` to use an installation
somewhere else.

The ``CsoundInstallation`` object exposes the paths and can produce the
environment variables for the installation:

.. code-block:: python

    from getcsound import find_csound

    installation = find_csound()
    if installation is not None:
        print(installation.as_env())
        # {'LIBCSOUNDPATH': '/home/user/.local/csound/libcsound64.so',
        #  'OPCODE7DIR64': '/home/user/.local/lib/csound/7.0/plugins64'}


Platform notes
--------------

* **Linux**: installs the portable Csound 7 build to ``~/.local/csound`` when
  there is no interactive terminal, or runs the interactive installer when
  there is one.
* **macOS**: installs the official Csound 7 ``.pkg`` with sudo. This needs an
  interactive terminal (to enter the password) or password-less sudo.
* **Windows**: installs the machine-wide x86_64 package, which needs
  Administrator rights. Windows on ARM64 is not supported by the automatic
  installer. An interactive or already-elevated session is required.

On unsupported platforms, or when installation is disabled, the official
one-line installers can still be used manually:

.. code-block:: sh

    # Linux / macOS
    curl -fsSL https://csound-plugins.github.io/getcsound.sh | bash

.. code-block:: powershell

    # Windows
    irm https://csound-plugins.github.io/getcsound.ps1 | iex


Environment variables
---------------------

``LIBCSOUNDPATH``
    Absolute path to the Csound shared library to use. Checked first by
    ``find_csound()``. If it is set to a missing file, ``ensure_csound()``
    raises instead of installing another Csound.

``OPCODE7DIR64``
    Csound plugin directory. Used when ``LIBCSOUNDPATH`` comes from the
    environment and set automatically after an installation.

``GETCSOUND_INSTALL``
    Set to ``0``, ``false``, ``no`` or ``off`` to disable automatic
    installation. ``LIBCSOUND_INSTALL`` is accepted as a compatibility alias.


Bundled installers
------------------

``getcsound/data/getcsound.sh`` and ``getcsound/data/getcsound.ps1`` are
mirrors of the canonical installers in ``~/dev/csound/installer/`` (published
at https://csound-plugins.github.io/). Do not edit the copies in this
repository; update the canonical source and run ``scripts/sync-installers.sh``.


Testing
-------

Run the unit tests with::

    pip install ".[test]"
    python -m pytest

The integration test in ``tests/test_integration_libcsound.py`` installs Csound
with ``getcsound``, then imports ``libcsound`` with ``LIBCSOUND_INSTALL=0`` and
checks that it loads the same installation and renders a short score. It is
skipped by default because it downloads and installs Csound; enable it with::

    GETCSOUND_RUN_LIBCSOUND_INTEGRATION=1 python -m pytest \
        tests/test_integration_libcsound.py

The GitHub Actions workflow runs this test on Linux x86-64, macOS arm64 and
Windows x86-64.


License
-------

LGPL-2.1-or-later. See ``LICENSE``.

The installation logic is derived from ``libcsound``'s ``_install.py``; it has
been adapted to be standalone and free of ``ctypes``.
