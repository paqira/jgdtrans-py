"""Provides utilities handling the mesh.

We note that :class:`MeshCoord` supports non-negative latitude and longitude only.
Therefore, :class:`MeshNode` and :class:`MeshCell` have the same restriction of :class:`MeshCoord`.

The third digit of :class:`MeshCoord` depends on mesh.
If the mesh unit is :obj:`5`, it takes :obj:`0` or :obj:`5` only.
Hence, the methods/operations that relate with :class:`MeshCoord` throws an exception,
if :obj:`5` is given even though the third digit is neither :obj:`0` nor :obj:`5`,
in general.
"""

from __future__ import annotations

import ctypes
import math
from dataclasses import dataclass
from enum import IntEnum
from typing import Final, Literal

from typing_extensions import Self

from . import point as _point
from . import types as _types

__all__ = [
    "unit",
    # "MeshUnit",
    "MeshCoord",
    "MeshNode",
    "MeshCell",
]


def unit(format: _types.FormatType) -> Literal[1, 5]:
    """Returns the unit of the format.

    Returns:
        1 or 5

    Examples:
        >>> unit('TKY2JGD')
        1
        >>> unit('SemiDynaEXE')
        5
    """
    if format in (
        "TKY2JGD",
        "PatchJGD",
        "PatchJGD_H",
        "PatchJGD_HV",
        "HyokoRev",
    ):
        return 1
    elif format in ("SemiDynaEXE", "geonetF3", "ITRF2014"):
        return 5

    raise ValueError(f"invalid format, we got {format}")


class MeshUnit(IntEnum):
    """The mesh unit (unit shortly), or approximate length of cell's edge."""

    ONE = 1
    """1 [km]"""
    FIVE = 5
    """5 [km]"""


@dataclass(frozen=True)
class MeshCoord:
    """Represents mesh coordinate, namely, discrete latitude and/or longitude.

    This supports total ordering,
    and non-negative latitude and/or longitude only.

    The coordinate has three digits, `first`, `second` and `third`,
    the `first` values 0 to 9, the `second` does 0 to 7
    and the `third` does 0 to 99 inclusive.

    The constructor throws :obj:`ValueError` if the digits are out-of-range.

    We note that the third digits takes either 0 or 5 only
    on the mesh with unit :obj:`5`.

    Raises:
        ValueError: any of `first`, `second` and `third` is out-of-range

    Examples:
        The selection of MeshCoord depends on unit

        >>> MeshCoord.from_latitude(36.103774791666666, 1)
        MeshCoord(first=54, second=1, third=2)

        Every fifth MeshCoord is taken, if unit is MeshUnit::Five

        >>> MeshCoord.from_latitude(36.103774791666666, 5)
        MeshCoord(first=54, second=1, third=0)

        Total orderd

        >>> MeshCoord(45, 7, 9) < MeshCoord(45, 7, 9)
        False
        >>> MeshCoord(45, 7, 9) < MeshCoord(45, 7, 10)
        True
        >>> MeshCoord(45, 7, 9) <= MeshCoord(45, 7, 9)
        True

        Increment/decrement (not inplace)

        >>> MeshCoord(54, 1, 2).next_up(1)
        MeshCoord(first=54, second=1, third=3)
        >>> MeshCoord(54, 1, 2).next_down(1)
        MeshCoord(first=54, second=1, third=1)
    """

    first: int
    """takes values :obj:`0`, ..., :obj:`99`."""
    second: int
    """takes values :obj:`0`, ..., :obj:`7`."""
    third: int
    """takes values :obj:`0`, ..., :obj:`9`."""

    def __post_init__(self):
        if not (0 <= self.first < 100):
            raise ValueError(f"expected first is 0, ..., 99, we got {self.first}") from None
        elif not (0 <= self.second < 8):
            raise ValueError(f"expected second is 0, ..., 7, we got {self.second}") from None
        elif not (0 <= self.third < 10):
            raise ValueError(f"expected second is 0, ..., 9, we got {self.third}") from None

    def __lt__(self, other: Self) -> bool:
        if not isinstance(other, MeshCoord):
            raise TypeError(
                f"'<' not supported between instances of '{type(self).__name__}' and '{type(self).__name__}'"
            ) from None

        if self.first == other.first:
            if self.second == other.second:
                return self.third < other.third
            else:
                return self.second < other.second
        else:
            return self.first < other.first

    def __le__(self, other: Self) -> bool:
        if not isinstance(other, MeshCoord):
            raise TypeError(
                f"'<=' not supported between instances of '{type(self).__name__}' and '{type(self).__name__}'"
            ) from None

        if self.first == other.first:
            if self.second == other.second:
                return self.third <= other.third
            else:
                return self.second < other.second
        else:
            return self.first < other.first

    def __gt__(self, other: Self) -> bool:
        if not isinstance(other, MeshCoord):
            raise TypeError(
                f"'>' not supported between instances of '{type(self).__name__}' and '{type(self).__name__}'"
            ) from None

        if self.first == other.first:
            if self.second == other.second:
                return self.third > other.third
            else:
                return self.second > other.second
        else:
            return self.first > other.first

    def __ge__(self, other: Self) -> bool:
        if not isinstance(other, MeshCoord):
            raise TypeError(
                f"'>=' not supported between instances of '{type(self).__name__}' and '{type(self).__name__}'"
            ) from None

        if self.first == other.first:
            if self.second == other.second:
                return self.third >= other.third
            else:
                return self.second > other.second
        else:
            return self.first > other.first

    @classmethod
    def _from_degree(cls, value: float, unit: Literal[1, 5]) -> Self:
        integer = math.floor(value)
        first = integer % 100

        second = math.floor(8 * value) - 8 * integer
        third = math.floor(80 * value) - 80 * integer - 10 * second

        if unit == 1:
            return cls(first, second, third)
        return cls(first, second, 0 if third < 5 else 5)

    @classmethod
    def from_latitude(cls, v: float, unit: Literal[1, 5]) -> Self:
        """Makes the greatest :class:`MeshCoord` obj less than the latitude `v` with `unit`.

        Args:
            v: the latitude [deg] which satisfies 0.0 <= and <= 66.666...
            unit: the mesh unit, ::`1` or :obj:`5`

        Returns:
            the :class:`MeshCoord` obj

        Raises:
            ValueError: if `v` is out-of-range

        Examples:
            >>> MeshCoord.from_latitude(36.103774791666666, 1)
            MeshCoord(first=54, second=1, third=2)
            >>> MeshCoord.from_latitude(36.103774791666666, 5)
            MeshCoord(first=54, second=1, third=0)

        See Also:
            - :meth:`MeshCoord.to_latitude`
        """
        # Minimum add-hook trick to ensure the identity,
        # 1. MeshCoord.from_latitude(coord.to_latitude(), 1)
        # 2. MeshCoord.from_longitude(coord.to_longitude(), 1)

        _value = 3 * v / 2
        # float to int trick
        if ctypes.c_uint64.from_buffer(ctypes.c_double(v)).value % 2 == 1:
            _value = math.nextafter(_value, math.inf)

        if unit not in (1, 5):
            raise ValueError(f"expected unit is 1 or 5, we got {unit}") from None
        elif not (0 <= _value < 100):
            raise ValueError(f"expected 0.0 <= value and value < 66.666..., we got {v}") from None

        return cls._from_degree(_value, unit=unit)

    @classmethod
    def from_longitude(cls, v: float, unit: Literal[1, 5]) -> Self:
        """Makes the greatest :class:`MeshCoord` obj less than the longitude `v` with `unit`.

        Args:
            v: the longitude [deg] which satisfies 100.0 <= and <= 180.0
            unit: the mesh unit, :obj:`1` or :obj:`5`

        Returns:
            the :class:`MeshCoord` obj

        Raises:
            ValueError: if `v` is out-of-range

        Examples:
            >>> MeshCoord.from_longitude(140.08785504166664, 1)
            MeshCoord(first=40, second=0, third=7)
            >>> MeshCoord.from_longitude(140.08785504166664, 5)
            MeshCoord(first=40, second=0, third=5)

        See Also:
            - :meth:`MeshCoord.to_longitude`
        """
        if unit not in (1, 5):
            raise ValueError(f"expected unit is 1 or 5, we got {unit}") from None
        elif not (100 <= v <= 180):
            raise ValueError(f"expected 100.0 <= value and value <= 180.0, we got {v}") from None

        return cls._from_degree(v, unit=unit)

    def is_unit(self, unit: Literal[1, 5]) -> bool:
        """Returns :obj:`True` if `self` is compatible to the `unit`.

        Always returns :obj:`True` if `unit` is :obj:`1`.

        Args:
            unit: the mesh unit, :obj:`1` or :obj:`5`

        Returns:
            :obj:`True` if `self` is compatible to the `unit`.

        Examples:
            >>> MeshCoord(1, 2, 3).is_unit(1)
            True
            >>> MeshCoord(1, 2, 3).is_unit(5)
            False
        """
        if unit not in (1, 5):
            raise ValueError(f"expected unit is 1 or 5, we got {unit}") from None
        return self.third % unit == 0

    def _to_degree(self) -> float:
        return self.first + self.second / 8 + self.third / 80

    def to_latitude(self) -> float:
        """Returns the latitude that `self` converts into.

        This does not check `self` represents latitude.

        Returns:
            the latitude [deg]

        Examples:
            >>> latitude = 36.103774791666666
            >>> MeshCoord.from_latitude(latitude, 1).to_latitude()
            36.1
            >>> MeshCoord.from_latitude(latitude, 5).to_latitude()
            36.083333333333336

        See Also:
            - :meth:`MeshCoord.from_latitude`
        """
        return 2 * self._to_degree() / 3

    def to_longitude(self) -> float:
        """Returns the longitude that `self` converts into.

        This does not check `self` represents longitude.

        Returns:
            the longitude [deg]

        Examples:
            >>> longitude = 140.08785504166664
            >>> MeshCoord.from_longitude(longitude, 1).to_longitude()
            140.0875
            >>> MeshCoord.from_longitude(longitude, 5).to_longitude()
            140.0625

        See Also:
            - :meth:`MeshCoord.from_longitude`
        """
        return 100 + self._to_degree()

    def next_up(self, unit: Literal[1, 5]) -> MeshCoord:
        """Returns the smallest :class:`MeshCoord` obj greater than `self`.

        Args:
            unit: the mesh unit, :obj:`1` or :obj:`5`

        Returns:
            the up-next :class:`MeshCoord`

        Raises:
            ValueError: if `unit` is :obj:`5` although `self.third` is either :obj:`0` or :obj:`5`
            OverflowError: if `self` is :code:`MeshCoord(first=99, second=7, third=9)`

        Examples:
            >>> MeshCoord(0, 0, 0).next_up(1)
            MeshCoord(0, 0, 1)
            >>> MeshCoord(0, 0, 0).next_up(5)
            MeshCoord(0, 0, 5)

            >>> MeshCoord(0, 0, 9).next_up(1)
            MeshCoord(0, 1, 0)
            >>> MeshCoord(0, 7, 9).next_up(1)
            MeshCoord(1, 0, 0)
        """
        if unit not in (1, 5):
            raise ValueError(f"expected unit is 1 or 5, we got {unit}") from None
        elif not self.is_unit(unit):
            raise ValueError(
                f"expected unit is 1 when third is neither 0 nor 5, we got {unit} (third is {self.third})"
            ) from None

        # that is 10 - self.unit
        bound: Final = 9 if unit == 1 else 5

        # increment
        if self.third == bound:
            if self.second == 7:
                if self.first == 99:
                    raise OverflowError(f"unable to add {unit} to {self}") from None
                return MeshCoord(self.first + 1, 0, 0)
            return MeshCoord(self.first, self.second + 1, 0)
        return MeshCoord(self.first, self.second, self.third + unit)

    def next_down(self, unit: Literal[1, 5]) -> MeshCoord:
        """Returns the greatest :class:`MeshCoord` obj less than `self`.

        Args:
            unit: the mesh unit, :obj:`1` or :obj:`5`

        Raises:
            ValueError: if `unit` is :obj:`5` although `self.third` is either :obj:`0` or :obj:`5`
            OverflowError: if `self` is :code:`MeshCoord(first=0, second=0, third=0)`

        Returns:
            the down-next :class:`MeshCoord`

        Examples:
            >>> MeshCoord(0, 0, 1).next_down(1)
            MeshCoord(0, 0, 0)
            >>> MeshCoord(0, 0, 5).next_down(5)
            MeshCoord(0, 0, 5)

            >>> MeshCoord(0, 1, 0).next_down(1)
            MeshCoord(0, 0, 9)
            >>> MeshCoord(1, 0, 0).next_down(1)
            MeshCoord(0, 7, 9)
        """
        if unit not in (1, 5):
            raise ValueError(f"expected unit is 1 or 5, we got {unit}") from None
        elif not self.is_unit(unit):
            raise ValueError(
                f"expected unit is 1 when third is neither 0 nor 5, we got {unit} (third is {self.third})"
            ) from None

        # that is 10 - self.unit
        bound: Final = 9 if unit == 1 else 5

        if self.third == 0:
            if self.second == 0:
                if self.first == 0:
                    raise OverflowError(f"unable to subtract {unit} from {self}") from None
                return MeshCoord(self.first - 1, 7, bound)
            return MeshCoord(self.first, self.second - 1, bound)
        return MeshCoord(self.first, self.second, self.third - unit)


@dataclass(frozen=True)
class MeshNode:
    """Represents mesh node, a pair of the :class:`MeshCoord` objs.

    We note that this supports non-negative latitude and longitude only,
    and `longitude` satisfies :code:`MeshCoord(0, 0, 0)` <=
    and <= :code:`MeshCoord(80, 0, 0)`.

    Raises:
        If `longitude` is out-of-range.

    Examples:
        Construct from latitude and longitude

        >>> MeshNode.from_pos(36.10377479, 140.087855041, unit=1)
        MeshNode(latitude=MeshCoord(54, 1, 2), longitude=MeshCoord(40, 0, 7))

        The result depends on the selection of the mesh unit

        >>> MeshNode.from_pos(36.10377479, 140.087855041, unit=5)
        MeshNode(latitude=MeshCoord(54, 1, 0), longitude=MeshCoord(40, 0, 5))

        Construct from meshcode

        >>> MeshNode.from_meshcode(54401027)
        MeshNode(latitude=MeshCoord(54, 1, 2), longitude=MeshCoord(40, 0, 7))
    """

    latitude: MeshCoord
    """The mesh coord of latitude."""
    longitude: MeshCoord
    """The mesh coord of longitude.

    This satisfies :code:`MeshCoord(0, 0, 0)` <= and <= :code:`MeshCoord(80, 0, 0)`.
    """

    def __post_init__(self):
        if self.longitude.first == 80:
            if self.longitude.second == 0:
                if 0 < self.longitude.third:
                    raise ValueError(
                        f"expected latitude is less than or equal MeshCoord(80, 0, 0), we got {self.longitude}"
                    ) from None
            elif 0 < self.longitude.second:
                raise ValueError(
                    f"expected latitude is less than or equal MeshCoord(80, 0, 0), we got {self.longitude}"
                ) from None
        elif 80 < self.longitude.first:
            raise ValueError(
                f"expected latitude is less than or equal MeshCoord(80, 0, 0), we got {self.longitude}"
            ) from None

    def is_unit(self, unit: Literal[1, 5]) -> bool:
        """Returns :obj:`True` if `self` is compatible to the `unit`.

        Always returns :obj:`True` if `unit` is :obj:`1`.

        Args:
            unit: the mesh unit, :obj:`1` or :obj:`5`

        Returns:
            :obj:`True` if `self` is compatible to the `unit`.

        Examples:
            >>> MeshNode.from_meshcode(54401027).is_unit(1)
            True
            >>> MeshNode.from_meshcode(54401027).is_unit(5)
            False
        """
        return self.latitude.is_unit(unit) and self.longitude.is_unit(unit)

    @classmethod
    def from_meshcode(cls, code: int) -> MeshNode:
        """Makes a :class:`MeshNode` obj represented by meshcode `code`.

        This method is an inverse of :meth:`MeshNode.to_meshcode`.

        Args:
            code: the meshcode

        Returns:
            the :class:`MeshNode`

        Raises:
            ValueError: if `code` is invalid.

        Examples:
            >>> MeshNode.from_meshcode(54401027)
            MeshNode(latitude=MeshCoord(54, 1, 2), longitude=MeshCoord(40, 0, 7))

        See Also:
            - :meth:`MeshNode.to_meshcode`
        """
        if code < 0 or 10000_00_00 <= code:
            raise ValueError(f"too large meshcode, we got {code}")

        lat_first, rest = divmod(code, 100_00_00)
        lng_first, rest = divmod(rest, 100_00)

        lat_second, rest = divmod(rest, 10_00)
        lng_second, rest = divmod(rest, 100)

        lat_third, lng_third = divmod(rest, 10)

        try:
            return MeshNode(
                MeshCoord(lat_first, lat_second, lat_third),
                MeshCoord(lng_first, lng_second, lng_third),
            )
        except ValueError as exc:
            raise ValueError(f"invalid meshcode, we got {code}") from exc

    @classmethod
    def from_point(cls, p: _point.Point, unit: Literal[1, 5]) -> Self:
        """Makes the nearest north-west :class:`MeshNode` of :class:`~JGDtrans.Point` p.

        We note that the result is independend of the :attr:`.Point.altitude`.

        Args:
            p: the point
            unit: the mesh unit, :obj:`1` or :obj:`5`

        Returns:
            the :class:`MeshNode` obj

        Raises:
            ValueError: `p.latitude` and/or `p.longitude` is out-of-range

        Examples:
            >>> p = Point(36.103774791666666, 140.08785504166664, 10.0)
            >>> MeshNode.from_point(p, 1)
            MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7))
            >>> MeshNode.from_point(p, 5)
            MeshNode(MeshCoord(54, 1, 0), MeshCoord(40, 0, 5))

        See Also:
            - :meth:`MeshNode.from_pos`
            - :meth:`MeshNode.to_point`
            - :meth:`.Point.mesh_node`
        """
        return cls.from_pos(p.latitude, p.longitude, unit=unit)

    @classmethod
    def from_pos(cls, latitude: float, longitude: float, unit: Literal[1, 5]) -> Self:
        """Makes the nearest north-west :class:`MeshNode` of point.

        Args:
            latitude: the latitude [deg] of the point which satisfies 0.0 <= and <= 66.6...
            longitude: the longitude [deg] of the point which satisfies 100.0 <= and <= 180.0
            unit: the mesh unit, :obj:`1` or :obj:`5`

        Returns:
            the :class:`MeshNode` obj

        Raises:
            ValueError: `latitude` or `longitude` is out-of-range

        Examples:
            >>> lat, lng = 36.103774791666666, 140.08785504166664
            >>> MeshNode.from_pos(lat, lng, 1)
            MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7))
            >>> MeshNode.from_pos(lat, lng, 5)
            MeshNode(MeshCoord(54, 1, 0), MeshCoord(40, 0, 5))

        See Also:
            - :meth:`MeshNode.from_point`
            - :meth:`MeshNode.to_pos`
        """
        return cls(
            MeshCoord.from_latitude(latitude, unit=unit),
            MeshCoord.from_longitude(longitude, unit=unit),
        )

    def to_meshcode(self) -> int:
        """Returns a meshcode represents `self`.

        The result is up to 8 digits.

        This method is an inverse of :meth:`MeshNode.from_meshcode`.

        Returns:
            the meshcode

        Examples:
            >>> node = MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7))
            >>> node.to_meshcode()
            54401027

        See Also:
            - :meth:`MeshNode.from_meshcode`
        """
        return (
            (self.latitude.first * 100 + self.longitude.first) * 10_000
            + (self.latitude.second * 10 + self.longitude.second) * 100
            + (self.latitude.third * 10 + self.longitude.third)
        )

    def to_point(self) -> _point.Point:
        """Returns a :class:`.Point` (latitude and longitude) where `self` locates.

        The resulting altitude is 0.0.

        Returns:
            a :class:`.Point` of the mesh node

        Examples:
            >>> node = MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7))
            >>> node.to_point()
            Point(latitude=36.1, longitude=140.0875, altitude=0.0)

        See Also:
            - :meth:`MeshNode.to_pos`
            - :meth:`MeshNode.from_point`
            - :meth:`.Point.from_node`
        """
        return _point.Point.from_node(self)

    def to_pos(self) -> tuple[float, float]:
        """Return the latitude and the longitude where `self` locates.

        Returns:
            the latitude [deg] and the longitude [deg] of the mesh node

        Examples:
            >>> node = MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7))
            >>> node.to_pos()
            (36.1, 140.0875)

        See Also:
            - :meth:`MeshNode.to_point`
            - :meth:`MeshNode.from_pos`
        """
        point = self.to_point()
        return point.latitude, point.longitude


@dataclass(frozen=True)
class MeshCell:
    """Represents the unit mesh cell (mesh cell or cell shortly).

    This is a quadruplet of the mesh nodes (and unit),
    and has no other :class:`MeshNode` inside `self` in the `unit`.

    The cell must be a *unit cell* in the `unit`,
    otherwise, this constructor throws :obj:`ValueError`.
    Also, :attr:`MeshCoord.third` of the nodes must be 1 or 5  if `unit` is :obj:`5`.

    The cell is, roughly, a square with `unit` [km] length edges.

    Raises:
        ValueError: if `unit` is inconsistent with nodes,
                    or the nodes does not construct a unit mesh cell with `unit`.

    Examples:
        Construct from latitude and longitude, and altitude ignores
        (the result depends on the selection of the mesh unit)

        >>> cell = MeshCell.from_pos(36.10377479, 140.087855041, unit=1)
        >>> cell
        MeshCell(
            south_west=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7)),
            south_east=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 8)),
            north_west=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 7)),
            north_east=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 8)),
            unit=1,
        )

        Construct from node

        >>> node = MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7))
        >>> cell == MeshCell.from_node(node, unit=1)
        True

        Construct from meshcode

        >>> cell == MeshCell.from_meshcode(54401027, unit=1)
        True

        Find the position within cell, from 0.0 to 1.0
        (again, the result depends on the selection of the mesh unit)

        >>> cell.position(36.10377479, 140.087855041)
        (0.4529748000001632, 0.028403280000475206)
    """

    south_west: MeshNode
    """The south-west node of the cell."""
    south_east: MeshNode
    """The south-east node of the cell."""
    north_west: MeshNode
    """The north-west node of the cell."""
    north_east: MeshNode
    """The north-east node of the cell."""
    unit: Literal[1, 5]
    """The mesh unit, :obj:`1` or :obj:`5`."""

    def __post_init__(self):
        if self.unit not in (1, 5):
            raise ValueError(f"expected unit is 1 or 5, we got {self.unit}") from None

        elif self.unit == 5:
            if self.south_west.latitude.third not in (0, 5) or self.south_west.longitude.third not in (0, 5):
                raise ValueError(
                    f"expected unit is 1 when third is neither 0 nor 5, "
                    f"we got a mesh node (south-west) as {self.south_west}"
                ) from None
            elif self.south_east.latitude.third not in (0, 5) or self.south_east.longitude.third not in (0, 5):
                raise ValueError(
                    f"expected unit is 1 when third is neither 0 nor 5, "
                    f"we got a mesh node (south-east) as {self.south_east}"
                ) from None
            elif self.north_west.latitude.third not in (0, 5) or self.north_west.longitude.third not in (0, 5):
                raise ValueError(
                    f"expected unit is 1 when third is neither 0 nor 5, "
                    f"we got a mesh node (north-west) as {self.north_west}"
                ) from None
            elif self.north_east.latitude.third not in (0, 5) or self.north_east.longitude.third not in (0, 5):
                raise ValueError(
                    f"expected unit is 1 when third is neither 0 nor 5, "
                    f"we got a mesh node (north-east) as {self.north_east}"
                ) from None

        next_lat = self.south_west.latitude.next_up(self.unit)
        next_lng = self.south_west.longitude.next_up(self.unit)
        if not MeshNode(next_lat, self.south_west.longitude) == self.north_west:
            raise ValueError(
                f"inconsistent on south-west vs north-west with unit {self.unit}, "
                f"we got south-west {self.south_west} and nw {self.north_west}"
            ) from None
        elif not MeshNode(self.south_west.latitude, next_lng) == self.south_east:
            raise ValueError(
                f"inconsistent on south-west vs south-east with unit {self.unit}, "
                f"we got south-west {self.south_west} and se {self.south_east}"
            ) from None
        elif not MeshNode(next_lat, next_lng) == self.north_east:
            raise ValueError(
                f"inconsistent on south-west vs south-east with unit {self.unit}, "
                f"we got south-west {self.south_west} and ne {self.north_east}"
            ) from None

    @classmethod
    def from_meshcode(cls, code: int, unit: Literal[1, 5]) -> Self:
        """Makes a :class:`MeshCell` with the south-east :class:`MeshNode` which represented by meshcode `code`.

        Args:
            code: the meshcode
            unit: the mesh unit, :obj:`1` or :obj:`5`

        Returns:
            the meth cell

        Raises:
            ValueError: if `code` is invalid, or `unit` is inconsistent meshcode

        Examples:
            >>> meshcode = 54401027
            >>> MeshCell.from_meshcode(code, unit=1)
            MeshCell(
                south_west=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7)),
                south_east=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 8)),
                north_west=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 7)),
                north_east=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 8)),
                unit=1,
            )
            >>> meshcode = 54401005
            >>> MeshCell.from_meshcode(code, unit=5)
            MeshCell(
                south_west=MeshNode(MeshCoord(54, 1, 0), MeshCoord(40, 0, 5)),
                south_east=MeshNode(MeshCoord(54, 1, 0), MeshCoord(40, 1, 0)),
                north_west=MeshNode(MeshCoord(54, 1, 5), MeshCoord(40, 0, 5)),
                north_east=MeshNode(MeshCoord(54, 1, 5), MeshCoord(40, 1, 0)),
                unit=5,
            )
        """
        south_west = MeshNode.from_meshcode(code=code)
        return cls.from_node(south_west, unit=unit)

    @classmethod
    def from_point(cls, p: _point.Point, unit: Literal[1, 5]) -> Self:
        """Makes a :class:`MeshCell` which contains the :class:`.Point`.

        We note that the result does not depend on :attr:`.Point.altitude`.

        Args:
            p: the point
            unit: the mesh unit, :obj:`1` or :obj:`5`

        Returns:
            the mesh cell

        Raises:
            ValueError: `p.latitude` and/or `p.longitude` is out-of-range,
                        or one of nodes constructing the cell is out-of-range.
            OverflowError: the south-west node points (90, x) for latitude and longitude.

        Examples:
            >>> point = Point(36.10377479, 140.087855041, 10.0)
            >>> MeshCell.from_point(p, unit=1)
            MeshCell(
                south_west=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7)),
                south_east=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 8)),
                north_west=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 7)),
                north_east=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 8)),
                unit=1,
            )
            >>> MeshCell.from_pos(p, unit=5)
            MeshCell(
                south_west=MeshNode(MeshCoord(54, 1, 0), MeshCoord(40, 0, 5)),
                south_east=MeshNode(MeshCoord(54, 1, 0), MeshCoord(40, 1, 0)),
                north_west=MeshNode(MeshCoord(54, 1, 5), MeshCoord(40, 0, 5)),
                north_east=MeshNode(MeshCoord(54, 1, 5), MeshCoord(40, 1, 0)),
                unit=5,
            )
        """
        return cls.from_pos(p.latitude, p.longitude, unit=unit)

    @classmethod
    def from_pos(cls, latitude: float, longitude: float, unit: Literal[1, 5]) -> Self:
        """Makes a :class:`MeshCell` which contains the point.

        Args:
            latitude: the latitude [deg] of the point which satisries 0 <= and <= 66.666...
            longitude: the longitude [deg] of the point which satisries 100 <= and <= 180
            unit: the mesh unit, :obj:`1` or :obj:`5`

        Returns:
            the mesh cell

        Raises:
            ValueError: if `latitude` or `longitude` is out-of-range,
                        or one of nodes constructing the cell is out-of-range.
            OverflowError: the south-west node points (90, x) for latitude and longitude.

        Examples:
            >>> lat, lng = 36.10377479, 140.087855041
            >>> MeshCell.from_pos(lat, lng, unit=1)
            MeshCell(
                south_west=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7)),
                south_east=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 8)),
                north_west=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 7)),
                north_east=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 8)),
                unit=1,
            )
            >>> MeshCell.from_pos(lat, lng, unit=5)
            MeshCell(
                south_west=MeshNode(MeshCoord(54, 1, 0), MeshCoord(40, 0, 5)),
                south_east=MeshNode(MeshCoord(54, 1, 0), MeshCoord(40, 1, 0)),
                north_west=MeshNode(MeshCoord(54, 1, 5), MeshCoord(40, 0, 5)),
                north_east=MeshNode(MeshCoord(54, 1, 5), MeshCoord(40, 1, 0)),
                unit=5,
            )
        """
        south_west = MeshNode.from_pos(latitude, longitude, unit=unit)
        return cls.from_node(south_west, unit=unit)

    @classmethod
    def from_node(cls, node: MeshNode, unit: Literal[1, 5]) -> Self:
        """Return the unit cell which has `node` as a south-east node.

        Args:
            node: the south-west mesh node of the resulting cell
            unit: the mesh unit, :obj:`1` or :obj:`5`

        Returns:
            the mesh cell

        Raises:
            ValueError: if `unit` is inconsistent `node`,
                        or one of nodes constructing the cell is out-of-range
            OverflowError: the south-west node points (90, x) for latitude and longitude.

        Examples:
            >>> node = MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7))
            >>> MeshCell.from_node(node, unit=1)
            MeshCell(
                south_west=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7)),
                south_east=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 8)),
                north_west=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 7)),
                north_east=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 8)),
                unit=1,
            )
            >>> node = MeshNode(MeshCoord(54, 1, 0), MeshCoord(40, 0, 5))
            >>> MeshCell.from_node(node, unit=5)
            MeshCell(
                south_west=MeshNode(MeshCoord(54, 1, 0), MeshCoord(40, 0, 5)),
                south_east=MeshNode(MeshCoord(54, 1, 0), MeshCoord(40, 1, 0)),
                north_west=MeshNode(MeshCoord(54, 1, 5), MeshCoord(40, 0, 5)),
                north_east=MeshNode(MeshCoord(54, 1, 5), MeshCoord(40, 1, 0)),
                unit=5,
            )
        """
        if unit == 5:
            if node.latitude.third not in (0, 5):
                raise ValueError(
                    "expected unit is 1 when third is neither 0 nor 5, "
                    f"we got {unit} and third of latitude is {node.latitude.third} for latitude"
                ) from None
            if node.longitude.third not in (0, 5):
                raise ValueError(
                    "expected unit is 1 when third is neither 0 nor 5, "
                    f"we got {unit} and third is {node.longitude.third} for longitude"
                ) from None

        next_lat = node.latitude.next_up(unit)
        next_lng = node.longitude.next_up(unit)
        return cls(
            south_west=node,
            south_east=MeshNode(node.latitude, next_lng),
            north_west=MeshNode(next_lat, node.longitude),
            north_east=MeshNode(next_lat, next_lng),
            unit=unit,
        )

    def position(self, latitude: float, longitude: float) -> tuple[float, float]:
        """Return the position in the cell.

        The result's components takes values from 0.0 to 1.0 (inclusive),
        if `latitude` and/or `longitude` is inside `self`.

        We note that the result is a (latitude, longitude) pair,
        not a (right-handed) (x, y) pair.

        Sample latitude and longitude

        >>> lat, lng = 36.10377479, 140.087855041
        >>> cell = MeshCell.from_pos(lat, lng, unit=1)

        The south-west of the cell is (0, 0), origin

        >>> cell.position(*cell.south_west.to_pos())
        (0, 0)

        The south-east is (0, 1)

        >>> cell.position(*cell.south_east.to_pos())
        (0.0, 0.9999999999990905)

        The north-west is (1, 0)

        >>> cell.position(*cell.north_west.to_pos())
        (0.9999999999999432, 0.0)

        The north-east is (1, 1)

        >>> cell.position(*cell.north_east.to_pos())
        (0.9999999999999432, 0.9999999999990905)

        Args:
            latitude: the latitude of the point
            longitude: the longitude of the point

        Returns:
            the position, a pair of the latitude and the longitude, in the cell

        Examples:
            The reuslt depends on unit

            >>> lat, lng = 36.10377479, 140.087855041
            >>> cell = MeshCell.from_pos(lat, lng, unit=1)
            >>> cell.position(lat, lng)
            (0.4529748000001632, 0.028403280000475206)
            >>> cell = MeshCell.from_pos(lat, lng, unit=5)
            >>> cell.position(lat, lng)
            (0.4905949600000099, 0.405680656000186)
        """
        # The cell stretches 1.5 times in the latitude direction
        # compared to the longitude direction,
        # then here uses 120 = 1.5 * 80.
        lat = latitude - self.south_west.latitude.to_latitude()
        lng = longitude - self.south_west.longitude.to_longitude()
        if self.unit == 1:
            return 120 * lat, 80 * lng
        return 24 * lat, 16 * lng


if __name__ == "__main__":
    pass
