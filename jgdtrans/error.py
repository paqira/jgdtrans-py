"""Provides :class:`Error` etc."""

from __future__ import annotations


class Error(Exception):
    """The root error of this package."""

    pass


class ParameterNotFoundError(Error, LookupError):
    """Parameter not found."""

    def __str__(self):
        return "{} ({})".format(*self.args)


class ParseError(Error, ValueError):
    """Failed to parse."""


class NotConvergeError(Error, ValueError):
    """Error is greater than criteria."""


if __name__ == "__main__":
    pass
