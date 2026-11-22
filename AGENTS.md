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

## Releases are tag-driven (setuptools-scm)

The package version is derived from git tags at build time
(`dynamic = ["version"]` + `[tool.setuptools_scm]` in `pyproject.toml`).
Never edit a version string to cut a release; tag instead:

    git tag 0.1.0 && git push --tags

CI checkouts must fetch tags (`fetch-depth: 0` in the workflow). Building from a
tree without git metadata (e.g. a GitHub "Download ZIP" archive) falls back to
`fallback_version`; sdists embed the frozen version in `PKG-INFO`.
