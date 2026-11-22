# Agent notes

## The bundled installers are mirrors

`getcsound/data/getcsound.sh` and `getcsound/data/getcsound.ps1` are copies of
the canonical installers in `~/dev/csound/installer/`, published at
https://csound-plugins.github.io/.

Never edit the files in `getcsound/data/` directly. Edit the canonical source,
then run:

    scripts/sync-installers.sh

Set `GETCSOUND_INSTALLER_SRC` if the canonical directory is somewhere else.

## No libcsound or ctypes dependency

`getcsound` must remain pure Python with no runtime dependencies. Do not import
`libcsound` or `ctypes` from this package. The test suite checks this.
