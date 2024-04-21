"""Provides :class:`Point`."""

from __future__ import annotations

import math
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Literal, overload

from typing_extensions import Self  # typing @ >= 3.11

from . import dms as _dms
from . import mesh as _mesh
from . import transformer as _trans
from . import types as _types

__all__ = [
    "Point",
]


def normalize_latitude(t: float) -> float:
    """Returns the normalized latitude into -90.0 <= and <= 90.0.

    Args:
        t: the latitude

    Returns:
        the latitude which satisfies -90.0 <= and <= 90.0

    Examples:
        >>> normalize_latitude(35.0)
        35.0
        >>> normalize_latitude(100.0)
        80.0
        >>> normalize_latitude(190.0)
        -10.0
        >>> normalize_latitude(-100.0)
        -80.0
        >>> normalize_latitude(-190.0)
        10.0
    """
    if math.isnan(t) or -90.0 <= t <= 90.0:
        return t

    t = t % 360.0
    if t < -270.0 or 270.0 < t:
        return t - math.copysign(360.0, t)
    elif t < -90.0 or 90.0 < t:
        return math.copysign(180.0, t) - t
    return t


def normalized_longitude(t: float) -> float:
    """Returns the normalized longitude -180.0 <= and <= 180.0.

    Args:
        t: the longitude

    Returns:
        the longitude which satisfies -180.0 <= and <= 180.0

    Examples:
        >>> normalized_longitude(145.0)
        145.0
        >>> normalized_longitude(190.0)
        -170.0
        >>> normalized_longitude(-190.0)
        170.0
    """
    if math.isnan(t) or -180.0 <= t <= 180.0:
        return t

    t = t % 360.0
    if t < -180.0 or 180.0 < t:
        return t - math.copysign(360.0, t)
    return t


@dataclass(frozen=True, unsafe_hash=True)
class Point(Sequence[float]):
    """A triplet of latitude, longitude and altitude.

    This is :obj:`Sequence[float]` of lengh 3.

    We note that `latitude` and `longitude` is DD notation,
    use :meth:`Point.to_dms` and :meth:`Point.from_dms` for converting to/from DMS notation.

    Examples:
        >>> Point(36.10377479, 140.087855041)
        Point(latitude=36.10377479, longitude=140.087855041, altitude=0.0)
        >>> Point(36.10377479, 140.087855041, 2.340)
        Point(latitude=36.10377479, longitude=140.087855041, altitude=2.340)

        >>> point = Point(36.10377479, 140.087855041)
        >>> len(point)
        3
        >>> for v in point:
        ...     print(v)
        36.10377479
        140.087855041
        0.0
        >>> point[0], point[1], point[2]
        (36.10377479, 140.087855041, 0.0)
        >>> lat, lng, alt = point
        >>> lat, lng, alt
        (36.10377479, 140.087855041, 0.0)
    """

    latitude: float
    """The latitude [deg] of the point which satisfies -90.0 <= and <= 90.0."""
    longitude: float
    """The longitude [deg] of the point which satisfies -180.0 <= and <= 180.0."""
    altitude: float = 0.0
    """The altitude [m] of the point, defaulting :obj:`0.0`."""

    def __len__(self) -> Literal[3]:
        return 3

    @overload
    def __getitem__(self, item: int) -> float: ...
    @overload
    def __getitem__(self, item: slice) -> Sequence[float]: ...
    def __getitem__(self, item: int | slice) -> float | Sequence[float]:
        return (self.latitude, self.longitude, self.altitude)[item]

    def __iter__(self) -> Iterator[float]:
        yield from (self.latitude, self.longitude, self.altitude)

    def __reversed__(self) -> Iterator[float]:
        yield from (self.altitude, self.longitude, self.latitude)

    def add(self, corr: _trans.Correction) -> Point:
        """Returns a :class:`Point` which is `self` plus `corr` for each component.

        This is not inplace.

        Returns:
            a :class:`Point` obj

        Examples:
            >>> point = Point(0.0, 0.0, 0.0)
            >>> point.add(Correction(1.0, 2.0, 3.0))
            Point(latitude=1.0, longitude=2.0, altitude=3.0)
            >>> point
            Point(latitude=0.0, longitude=0.0, altitude=0.0)
        """
        return Point(
            latitude=self.latitude + corr.latitude,
            longitude=self.longitude + corr.longitude,
            altitude=self.altitude + corr.altitude,
        )

    def sub(self, corr: _trans.Correction) -> Point:
        """Returns a :class:`Point` which is `self` substruct `corr` for each component.

        This is not inplace.

        Returns:
            a :class:`Point` obj

        Examples:
            >>> point = Point(0.0, 0.0, 0.0)
            >>> point.sub(Correction(1.0, 2.0, 3.0))
            Point(latitude=-1.0, longitude=-2.0, altitude=-3.0)
            >>> point
            Point(latitude=0.0, longitude=0.0, altitude=0.0)
        """
        return Point(
            latitude=self.latitude - corr.latitude,
            longitude=self.longitude - corr.longitude,
            altitude=self.altitude - corr.altitude,
        )

    def normalize(self) -> Point:
        """Returns a new normalized :class:`Point` obj.

        The resulting :class:`Point` obj has normalized latitude and longitude
        which value -90.0 <= and <= 90.0, and -180.0 <= and <= 180.0 respectively.

        Returns:
            The normalized point, not null.

        Examples:
            >>> Point(100.0, 200.0, 5.0).normalize()
            Point(latitude=80.0, longitude=-160.0, altitude=5.0)
        """
        return Point(
            latitude=normalize_latitude(self.latitude),
            longitude=normalized_longitude(self.longitude),
            altitude=self.altitude,
        )

    @classmethod
    def from_node(cls, node: _mesh.MeshNode) -> Self:
        """Makes a :class:`Point` which pointing a node represented by meshcode.

        The resulting altitude is 0.0.

        Args:
            node: the mesh node

        Returns:
            the point (the altitude is 0.0)

        Examples:
            >>> node = MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7))
            >>> Point.from_node(node)
            Point(latitude=36.1, longitude=140.0875, altitude=0.0)

        See Also:
            - :meth:`.MeshNode.to_point`
        """
        return cls(node.latitude.to_latitude(), node.longitude.to_longitude(), 0.0)

    @classmethod
    def from_meshcode(cls, meshcode: int) -> Self:
        """Makes a :class:`Point` (the latitude and the longitude) of the node represented by `code`.

        Args:
            meshcode: the meshcode

        Returns:
            a :class:`Point` obj

        Raises:
            ValueError: when invalid `code` given

        Examples:
            >>> Point.from_meshcode(54401027)
            Point(latitude=36.1, longitude=140.0875, altitude=0.0)

        See Also:
            - :meth:`.MeshNode.from_meshcode`
        """
        node = _mesh.MeshNode.from_meshcode(meshcode)
        return cls.from_node(node)

    @classmethod
    def from_dms(cls, latitude: _dms.DMS | str, longitude: _dms.DMS | str, altitude: float = 0.0) -> Self:
        """Makes a :class:`Point` from DMS notation latitude and longitdue (and altitude).

        Args:
            latitude: the latitude in DMS notation
            longitude: the longitude in DMS notation
            altitude: the altitude [m], defaulting :obj:`0.0`

        Returns:
            a :class:`Point` obj with the DD notation latitude and longitude

        Raises:
            ValueError: when `latitude` and/or `longitude` is invalied

        Examples:
            >>> Point.from_dms('360613.58925', '1400516.27815')
            Point(latitude=36.10377479166667, longitude=140.08785504166664, altitude=0.0)
        """
        if isinstance(latitude, str):
            latitude = _dms.DMS.from_str(latitude)

        if isinstance(longitude, str):
            longitude = _dms.DMS.from_str(longitude)

        return cls(
            latitude=latitude.to_dd(),
            longitude=longitude.to_dd(),
            altitude=altitude,
        )

    def to_dms(self) -> tuple[str, str, float]:
        """Returns the point with the DMS notation latitude and longitude.

        Returns:
            a tuple of latitude, longtitude and altitude

        Examples:
            >>> point = Point.from_dms('360613.58925', '1400516.27815')
            >>> point.to_dms()
            ('360613.58925', '1400516.27815', 0.0)
        """
        return (
            _dms.DMS.from_dd(self.latitude).to_str(),
            _dms.DMS.from_dd(self.longitude).to_str(),
            self.altitude,
        )

    def to_meshcode(self, mesh_unit: _types.MeshUnitType) -> int:
        """Returns the meshcode of the nearest south-east mesh node of `self`.

        Args:
            mesh_unit: The mesh unit, :obj:`1` or :obj:`5`

        Returns:
            the meshcode

        Raises:
            ValueError: when `latitude` and/or `longitude` is negative

        Examples:
            >>> point = Point(36.103774791666666, 140.08785504166664, 10.0)
            >>> point.to_meshcode(1)
            54401027
            >>> point = Point(36.103774791666666, 140.08785504166664, 10.0)
            >>> point.to_meshcode(5)
            54401005
        """
        return self.mesh_node(mesh_unit).to_meshcode()

    def mesh_node(self, mesh_unit: _types.MeshUnitType) -> _mesh.MeshNode:
        """Returns the nearest south-east mesh node of `self`.

        We note that the result does not depend on the :attr:`Point.altitude`.

        Args:
            mesh_unit: The mesh unit, :obj:`1` or :obj:`5`

        Returns:
            a :class:`.MeshNode`

        Raises:
            ValueError: when `latitude` and/or `longitude` is negative

        Examples:
            >>> point = Point(36.103774791666666, 140.08785504166664, 10.0)
            >>> point.mesh_node(point, 1)
            MeshNode(MeshCode(54, 1, 2), MeshCode(40, 0, 7))
            >>> point.mesh_node(point, 5)
            MeshNode(MeshCode(54, 1, 0), MeshCode(40, 0, 5))

        See Also:
            - :meth:`.MeshNode.from_point`
        """
        return _mesh.MeshNode.from_point(self, mesh_unit=mesh_unit)

    def mesh_cell(self, mesh_unit: _types.MeshUnitType) -> _mesh.MeshCell:
        """Returns the unit mesh cell containing `self`.

        Args:
            mesh_unit: The mesh unit, :obj:`1` or :obj:`5`

        Returns:
            the unit mesh cell containing `self`

        Raises:
            ValueError: when `latitude` and/or `longitude` is negative,
                        or such :class:`.MeshCell` is not found

        Examples:
            >>> point = Point(36.10377479, 140.087855041)
            >>> point.mesh_cell(mesh_unit=1)
            MeshCell(
                south_west=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7)),
                south_east=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 8)),
                north_west=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 7)),
                north_east=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 8)),
                unit=1,
            )
            >>> point.mesh_cell(mesh_unit=5)
            MeshCell(
                south_west=MeshNode(MeshCoord(54, 1, 0), MeshCoord(40, 0, 5)),
                south_east=MeshNode(MeshCoord(54, 1, 0), MeshCoord(40, 1, 0)),
                north_west=MeshNode(MeshCoord(54, 1, 5), MeshCoord(40, 0, 5)),
                north_east=MeshNode(MeshCoord(54, 1, 5), MeshCoord(40, 1, 0)),
                unit=5,
            )

        See Also:
            - :meth:`.MeshNode.from_point`
        """
        return _mesh.MeshCell.from_point(self, mesh_unit=mesh_unit)


if __name__ == "__main__":
    pass
