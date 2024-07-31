"""Provides utilities."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Literal

from typing_extensions import Self  # typing @ >= 3.11

__all__ = [
    "to_dms",
    "from_dms",
    "DMS",
]


def to_dms(t: float) -> str:
    """Returns a DMS notation :obj:`str` from a DD notation :obj:`float`.

    Args:
        t: the DD notation latitude or longitude which satisfies -180.0 <= and 180.0

    Returns:
        `t` as a DMS notation

    Raises:
        ValueError: when conversion failed

    Examples:
        >>> to_dms(36.103774791666666)
        "360613.589250000023299"
        >>> to_dms(140.08785504166667)
        "1400516.278150000016467"
    """
    return DMS.from_dd(t).to_str()


def from_dms(s: str) -> float:
    """Returns a DD notation :obj:`float` from a DMS notation :obj:`str`.

    Args:
        s: the DMS notation latitude or longitude

    Returns:
        `s` as a DD notation `float`

    Raises:
        ValueError: when conversion failed

    Examples:
        >>> from_dms("360613.58925")
        36.103774791666666
        >>> from_dms("1400516.27815")
        140.08785504166664
    """
    return DMS.from_str(s).to_dd()


@dataclass(frozen=True)
class DMS:
    """Represents latitude and/or longitude in DMS notation.

    Raises:
        ValueError: when all the following conditions does not hold;

            - `degree` satisries 0 <= and <= 180,
            - `minute` does 0 <= and < 60,
            - `second` does 0 <= and < 60,
            - and `fract` does 0.0 <= and < 1.0.
            - Additionally, `minute`, `second` and `fract` is `0` when `degree` is 180.

    Examples:
        >>> dms = DMS(1, 36, 6, 13, 0.58925)
        >>> dms
        DMS(sign=1, degree=36, minute=6, second=13, fract=0.58925)
        >>> dms.sign, dms.degree, dms.minute, dms.second, dms.fract
        (1, 36, 6, 13, 0.58925)
        >>> dms.to_str()
        "360613.58925"
        >>> dms.to_dd()
        36.10377479166667
        >>> DMS.from_dd(36.10377479166667)
        DMS(sign=1, degree=36, minute=6, second=13, fract=0.58925)
    """

    sign: Literal[1, -1]
    """The sign of latitude or longitude."""
    degree: int
    """The degree of latitude or longitude."""
    minute: int
    """The minute of latitude or longitude."""
    second: int
    """The integer part of second of latitude or longitude."""
    fract: float
    """The fraction part of second of latitude or longitude."""

    def __post_init__(self):
        if self.sign not in (1, -1):
            raise ValueError(f"expected sign is 1 or -1, we got {self.sign}")
        elif not (0 <= self.degree <= 180):
            raise ValueError(f"expected degree satisfies 0 <= and <= 180, we got {self.degree}")
        elif not (0 <= self.minute < 60):
            raise ValueError(f"expected minute satisfies 0 <= and < 60, we got {self.minute}")
        elif not (0 <= self.second < 60):
            raise ValueError(f"expected second satisfies 0 <= and < 60, we got {self.second}")
        elif not (0 <= self.fract < 1):
            raise ValueError(f"expected fraction satisfies 0.0 <= and < 1.0, we got {self.fract}")
        elif self.degree == 180.0 and (self.minute != 0 or self.second != 0 or self.fract != 0):
            raise ValueError(f"invalid value given, we got {self.degree}, {self.minute}, {self.second}, {self.fract}")

    @staticmethod
    def _carry(sign: Literal[1, -1], degree: int, minute: int, second: int, fract: float):
        carry, second = divmod(second, 60)
        carry, minute = divmod(minute + carry, 60)
        return {
            "sign": sign,
            "degree": degree + carry,
            "minute": minute,
            "second": second,
            "fract": fract,
        }

    def __str__(self) -> str:
        """Returns a DMS notation :obj:`str` obj of `self`.

        Returns:
            a DMS notation :obj:`str` obj

        Examples:
            >>> str(DMS(1, 36, 6, 13, 0.58925))
            "360613.58925"
            >>> repr(DMS(1, 36, 6, 13, 0.58925))
            DMS(sign=1, degree=36, minute=6, second=13, fract=0.58925)
        """
        return self.to_str()

    @classmethod
    def from_str(cls, s: str) -> Self:  # noqa: C901
        """Makes a :class:`DMS` obj from DMS notation :obj:`str`.

        Args:
            s: latitude or longitude in DMS notation

        Returns:
            a :class:`DMS` obj

        Raises:
            ValueError: when `s` is invalid or out-of-range

        Examples:
            >>> DMS.from_str("360613.58925")
            DMS(sign=1, degree=36, minute=6, second=13, fract=0.58925)
            >>> DMS.from_str("1400516.27815")
            DMS(sign=1, degree=140, minute=5, second=16, fract=0.27815)
        """

        def _parser(_sign, _integer, _fraction):
            degree, rest = divmod(_integer, 10000)
            minute, second = divmod(rest, 100)
            return cls(sign=_sign, degree=degree, minute=minute, second=second, fract=_fraction)

        mo = re.match(r"^\s*([+-]?)(\d+(?:[_\d]*\d+|))(\.\d+(?:[_\d]*\d+|))\s*$", s)
        if mo:
            sign, integer, fraction = mo.groups()

            try:
                integer = int(integer)
                fraction = float(fraction)
            except ValueError:
                pass
            else:
                return _parser(-1 if sign == "-" else 1, integer, fraction)

        mo = re.match(r"^\s*([+-]?)(\.\d+(?:[_\d]*\d+|))\s*$", s)
        if mo:
            sign, fraction = mo.groups()

            try:
                fraction = float(fraction)
            except ValueError:
                pass
            else:
                return _parser(-1 if sign == "-" else 1, 0, fraction)

        mo = re.match(r"^\s*([+-]?)(\d+(?:[_\d]*\d+|))\.?\s*$", s)
        if mo:
            sign, integer = mo.groups()

            try:
                integer = int(integer)
            except ValueError:
                pass
            else:
                return _parser(-1 if sign == "-" else 1, integer, 0.0)

        raise ValueError(f"unexpected DMS notation angle, we got {repr(s)}") from None

    @classmethod
    def from_dd(cls, t: float) -> Self:
        """Makes a :class:`DMS` obj from DD notation :obj:`float`.

        Args:
            t: the latitude or longitude which satisfies -180.0 <= and <= 180.0

        Returns:
            a :obj:`DMS` obj

        Raises:
            ValueError: when `t` is out-of-range

        Examples:
            >>> DMS.from_dd(36.103774791666666)
            DMS(sign=1, degree=36, minute=6, second=13, fract=0.5892500000232985)
            >>> DMS.from_dd(140.08785504166667)
            DMS(sign=1, degree=140, minute=5, second=16, fract=0.2781500001187851)
        """
        if not (-180 <= t <= 180):
            raise ValueError(f"expected t is -180.0 <= and <= 180.0, we got {t}")

        mm, _ = math.modf(t)
        mm *= 60
        ss, _ = math.modf(mm)
        ss *= 60

        degree = math.trunc(t)
        minute = math.trunc(mm)
        second = math.trunc(ss)
        fract, _ = math.modf(ss)

        return cls(
            **DMS._carry(
                sign=1 if 0 <= t else -1, degree=abs(degree), minute=abs(minute), second=abs(second), fract=abs(fract)
            )
        )

    def _to_str(
        self,
    ) -> tuple[str, None, None, int, str] | tuple[str, None, int, int, str] | tuple[str, int, int, int, str]:
        s = "" if self.sign == 1 else "-"
        _, fract = f"{self.fract:.15f}".rstrip("0").split(".")
        if not fract:
            fract = "0"

        if not self.degree:
            if self.minute:
                return s, None, self.minute, self.second, fract
            else:
                return s, None, None, self.second, fract
        return s, self.degree, self.minute, self.second, fract

    def to_str(self) -> str:
        """Returns a DMS notation :obj:`str` obj of `self`.

        Returns:
            a DMS notation :obj:`str` obj

        Examples:
            >>> DMS(1, 36, 6, 13, 0.58925).to_str()
            "360613.58925"
            >>> DMS(1, 140, 5, 16, 0.27815).to_str()
            "1400516.27815"
        """
        sign, d, m, s, f = self._to_str()
        if d == 0 or d is None:
            if m == 0 or m is None:
                return f"{sign}{s}.{f}"
            else:
                return f"{sign}{m}{s:02}.{f}"
        return f"{sign}{d}{m:02}{s:02}.{f}"

    def to_primed_str(self) -> str:
        """Returns a DMS notation :obj:`str` obj of `self` with primes.

        Returns:
            a DMS notation :obj:`str` obj

        Examples:
            >>> DMS(1, 36, 6, 13, 0.58925).to_str()
            "36°06′13.58925″"
            >>> DMS(1, 140, 5, 16, 0.27815).to_str()
            "140°05′16.27815″"
        """
        sign, d, m, s, f = self._to_str()
        if d == 0 or d is None:
            if m == 0 or m is None:
                return f"{sign}{s}.{f}″"
            else:
                return f"{sign}{m}′{s:02}.{f}″"
        return f"{sign}{d}°{m:02}′{s:02}.{f}″"

    def to_dd(self) -> float:
        """Returns a DD notation :obj:`float` obj of `self`.

        Returns:
            a `self` in DD notation

        Examples:
            >>> DMS(1, 36, 6, 13, 0.58925).to_dd()
            36.103774791666666
            >>> DMS(1, 140, 5, 16, 0.27815).to_dd()
            140.08785504166667
        """
        return math.copysign(
            self.degree + self.minute / 60 + (self.second + self.fract) / 3600,
            self.sign,
        )


if __name__ == "__main__":
    pass
