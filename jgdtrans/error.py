"""Provides :class:`Error` etc."""

from __future__ import annotations

__all__ = [
    "Error",
    "ParameterNotFoundError",
    "CorrectionNotFoundError",
    "PointOutOfBoundsError",
    "ParseParFileError",
]


class Error(Exception):
    """The root error of this package."""

    pass


class ParameterNotFoundError(Error, LookupError):
    """Parameter not found."""

    def __str__(self):
        return "{} ({})".format(*self.args)


class PointOutOfBoundsError(Error, ValueError):
    """Error is greater than criteria."""


class CorrectionNotFoundError(Error, ValueError):
    """Error is greater than criteria."""


class ParseParFileError(Error, ValueError):
    """Failed to parse par file."""


if __name__ == "__main__":
    pass
