#!/usr/bin/env bash
# Copy the canonical Csound installers into this package.
#
# The source of truth is ~/dev/csound/installer/. Override its location with
# GETCSOUND_INSTALLER_SRC if needed. Do not edit getcsound/data/ directly.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
src="${GETCSOUND_INSTALLER_SRC:-$HOME/dev/csound/installer}"
dst="$here/getcsound/data"

if [[ ! -d "$src" ]]; then
    echo "error: installer source not found: $src" >&2
    echo "Set GETCSOUND_INSTALLER_SRC to the canonical installer directory." >&2
    exit 1
fi

mkdir -p "$dst"
for name in getcsound.sh getcsound.ps1; do
    if [[ ! -f "$src/$name" ]]; then
        echo "error: missing $src/$name" >&2
        exit 1
    fi
    cp "$src/$name" "$dst/$name"
done

echo "Copied installers from $src to $dst"
sha256sum "$dst/getcsound.sh" "$dst/getcsound.ps1"
