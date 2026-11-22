"""Exceptions raised by :mod:`getcsound`."""

from __future__ import annotations


class GetCsoundError(RuntimeError):
    """Base class for errors raised by :mod:`getcsound`."""


class CsoundNotFoundError(GetCsoundError):
    """Csound could not be found and automatic installation is disabled."""


class CsoundInstallError(GetCsoundError):
    """Csound could not be installed."""
