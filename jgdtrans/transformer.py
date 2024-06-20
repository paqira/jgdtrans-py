"""Provides :class:`Transformer` etc."""

from __future__ import annotations

import math
import textwrap
from collections.abc import Mapping
from dataclasses import dataclass
from typing import ClassVar, Final, NamedTuple

from typing_extensions import Self  # typing @ >= 3.11

from . import error as _error
from . import mesh as _mesh
from . import point as _point
from . import types as _types

__all__ = [
    "Transformer",
    "Parameter",
    "Correction",
    "Statistics",
    "StatisticData",
    #
    "from_dict",
]

FORMAT: Final = (
    "TKY2JGD",
    "PatchJGD",
    "PatchJGD_H",
    "PatchJGD_HV",
    "HyokoRev",
    "SemiDynaEXE",
    "geonetF3",
    "ITRF2014",
)


def bilinear_interpolation(sw: float, se: float, nw: float, ne: float, lat: float, lng: float) -> float:
    """Bilinear interpolation on the unit square.

    The resulting value is given by
    :math:`f(0, 0) (1 - x) (1 - y) + f(1, 0) x (1 - y) + f(0, 1) (1 - x) y + f(0, 0) x y`.

    Args:
        sw: denotes :math:`f(0, 0)`
        se: denotes :math:`f(1, 0)`
        nw: denotes :math:`f(0, 1)`
        ne: denotes :math:`f(1, 1)`
        lat: denotes :math:`y`
        lng: denotes :math:`x`

    Returns:
        the estimated value

    Examples:
        >>> bilinear_interpolation(0.0, 0.5, 0.5, 1.0, lat=0.5, lng=0.5)
        0.5
        >>> bilinear_interpolation(0.0, 0.5, 0.5, 1.0, lat=1.0, lng=0.0)
        0.5
        >>> bilinear_interpolation(0.0, 0.5, 0.5, 1.0, lat=0.0, lng=0.0)
        0.5
        >>> bilinear_interpolation(0.0, 0.5, 0.5, 1.0, lat=1.0, lng=1.0)
        1.0
    """
    # a = sw
    # b = -sw + nw
    # c = -sw + se
    # d = sw - se - nw + ne
    # res = a + b * lng + c * lat + d * lng * lat
    # statistically more precise than above
    return sw * (1 - lng) * (1 - lat) + se * lng * (1 - lat) + nw * (1 - lng) * lat + ne * lng * lat


def from_dict(obj: _types.TransformerLikeMappingType) -> Transformer:
    """Makes a :class:`Transformer` obj from :obj:`Mapping` obj.

    See :obj:`.FormatType` for detail of :obj:`'PatchJGD_HV'`.

    Args:
        obj: the :obj:`Mapping` of the unit, the parameter,
             and the description (optional) fields

    Returns:
        the :class:`Transformer` obj

    Raises:
        ParseError: when fail to parse meshcode

    Examples:
        >>> data = {
        ...     'format': 'TKY2JGD',
        ...     'parameter': {
        ...         12345678: {
        ...             'latitude': 0.1
        ...             'longitude': 0.2
        ...             'altitude': 0.3
        ...         },
        ...         ...
        ...     },
        ...     'description': 'important my param',  # optional
        ... }
        >>> tf = from_dict(data)
        >>> tf.format
        1
        >>> tf.parameter
        {12345678: Parameter(0.1, 0.2, 0.3), ...}
        >>> tf.description
        'important my param'

        >>> data = {
        ...     'format': 'TKY2JGD',
        ...     'parameter': {
        ...         '12345678': {
        ...             'latitude': 0.1
        ...             'longitude': 0.2
        ...             'altitude': 0.3
        ...         },
        ...         ...
        ...     },
        ... }
        >>> tf = from_dict(data)
        >>> tf.format
        1
        >>> tf.parameter
        {12345678: Parameter(0.1, 0.2, 0.3), ...}
        >>> tf.description
        None

    See Also:
        - :meth:`Transformer.from_dict`
    """
    return Transformer.from_dict(obj)


class Correction(NamedTuple):
    """The transformation correction."""

    latitude: float
    """The latitude correction [deg]."""
    longitude: float
    """The longitude correction [deg]."""
    altitude: float
    """The altitude correction [m]."""

    @property
    def horizontal(self) -> float:
        r""":math:`\sqrt{\text{latitude}^2 + \text{longitude}^2}` [deg]."""
        return math.hypot(self.latitude, self.longitude)


class Parameter(NamedTuple):
    """The parameter triplet.

    We emphasize that the unit of latitude and longitude is [sec], not [deg].

    It should fill by :obj:`0.0` instead of :obj:`nan`
    when the parameter does not exist, as parsers does.
    """

    latitude: float
    """The latitude parameter [sec]."""
    longitude: float
    """The latitude parameter [sec]."""
    altitude: float
    """The altitude parameter [m]."""

    @property
    def horizontal(self) -> float:
        r""":math:`\sqrt{\text{latitude}^2 + \text{longitude}^2}` [sec]."""
        return math.hypot(self.latitude, self.longitude)


@dataclass(frozen=True)
class StatisticData:
    """The statistics of parameter.

    This is a component of the result that :meth:`Transformer.statistics` returns.
    """

    count: int | None
    """The count."""
    mean: float | None
    """The mean ([sec] or [m])."""
    std: float | None
    """The standard variance ([sec] or [m])."""
    abs: float | None
    r""":math:`(1/n) \sum_{i=1}^n \left| \text{parameter}_i \right|` ([sec] or [m])."""
    min: float | None
    """The minimum ([sec] or [m])."""
    max: float | None
    """The maximum ([sec] or [m])."""


@dataclass(frozen=True)
class Statistics:
    """The statistical summary of parameter.

    This is a result that :meth:`Transformer.statistics` returns.
    """

    latitude: StatisticData
    """The statistics of latitude."""
    longitude: StatisticData
    """The statistics of longitude."""
    altitude: StatisticData
    """The statistics of altitude."""
    horizontal: StatisticData
    """The statistics of horizontal."""


@dataclass(frozen=True)
class Transformer:
    """The coordinate Transformer, and represents a deserializing result of par file.

    If the parameters is zero, such as the unsupported components,
    the transformations are identity transformation on such components.
    For example, the transformation by the TKY2JGD and the PatchJGD par is
    identity transformation on altitude, and by the PatchJGD(H) par is
    so on latitude and longitude.

    Examples:
        From `SemiDynaEXE2023.par`

        >>> tf = Transformer(
        ...     format='SemiDynaEXE',
        ...     parameter={
        ...         54401005: Parameter(-0.00622, 0.01516, 0.0946),
        ...         54401055: Parameter(-0.0062, 0.01529, 0.08972),
        ...         54401100: Parameter(-0.00663, 0.01492, 0.10374),
        ...         54401150: Parameter(-0.00664, 0.01506, 0.10087),
        ...     }
        ... )

        Forward transformation

        >>> tf.forward(36.10377479, 140.087855041, 2.34)
        Point(latitude=36.103773017086695, longitude=140.08785924333452, altitude=2.4363138578103)

        Backward transformation

        >>> tf.backward(36.103773017086695, 140.08785924333452, 2.4363138578103)
        Point(latitude=36.10377479, longitude=140.087855041, altitude=2.34)

        Compatible backward transformation to GIAJ web app/APIs

        >>> tf.backward_compat(36.103773017086695, 140.08785924333452, 2.4363138578103)
        Point(latitude=36.10377479000002, longitude=140.087855041, altitude=2.339999999578243)
    """

    format: _types.FormatType
    """The format of par file.

    See :obj:`.FormatType` for detail of :obj:`'PatchJGD_HV'`.
    """

    parameter: Mapping[int, Parameter]
    """The transformation parameter.

    The entry represents single line of the par file's parameter section,
    the key is meshcode, and the value is a :class:`.Parameter`,
    a triplet of latitude [sec], longitude [sec] and altitude [m].
    """

    description: str | None = None
    """The description."""

    MAX_ERROR: ClassVar[float] = 5e-14
    """Max error of :meth:`Transformer.backward` and :meth:`Transformer.backward_corr`."""

    def __post_init__(self):
        if self.format not in FORMAT:
            raise ValueError(f"unexpected format give, we got '{self.format}'")

    def __repr__(self):
        # the parameter is too long for display
        fmt = "{}(format={}, parameter=<{} ({} length) at 0x{:x}>, description={})"
        return fmt.format(
            self.__class__.__name__,
            self.format,
            self.parameter.__class__.__name__,
            len(self.parameter),
            id(self.parameter),
            (
                repr(textwrap.shorten(self.description, width=11))
                if isinstance(self.description, str)
                else self.description
            ),
        )

    def mesh_unit(self) -> _types.MeshUnitType:
        """Returns the mesh unit of the format.

        Returns:
            1 or 5

        Examples:
            >>> tf = Transformer(format='TKY2JGD', parameter={})
            >>> tf.mesh_unit()
            1
            >>> tf = Transformer(format='SemiDynaEXE', parameter={})
            >>> tf.mesh_unit()
            5
        """
        return _mesh.mesh_unit(self.format)

    @classmethod
    def from_dict(cls, obj: _types.TransformerLikeMappingType) -> Self:
        """Makes a :class:`Transformer` obj from :obj:`Mapping` obj.

        This parses meshcode, the key of `parameter`, into :obj:`int`.

        See :obj:`.FormatType` for detail of :obj:`'PatchJGD_HV'`.

        Args:
            obj: the :obj:`Mapping` of the format, the parameters,
                 and the description (optional)

        Returns:
            the :class:`Transformer` obj

        Raises:
            DeserializeError: when fail to parse the meshcode

        Examples:
            >>> data = {
            ...     'format': 'SemiDynaEXE',
            ...     'parameter': {
            ...         12345678: {
            ...             'latitude': 0.1
            ...             'longitude': 0.2
            ...             'altitude': 0.3
            ...         },
            ...         ...
            ...     },
            ...     'description': 'important my param',  # optional
            ... }
            >>> tf = Transformer.from_dict(data)
            >>> tf.format
            'SemiDynaEXE'
            >>> tf.parameter
            {12345678: Parameter(0.1, 0.2, 0.3), ...}
            >>> tf.description
            'important my param'

            >>> data = {
            ...     'format': 'SemiDynaEXE',
            ...     'parameter': {
            ...         '12345678': {
            ...             'latitude': 0.1
            ...             'longitude': 0.2
            ...             'altitude': 0.3
            ...         },
            ...         ...
            ...     },
            ... }
            >>> tf = Transformer.from_dict(data)
            >>> tf.format
            'SemiDynaEXE'
            >>> tf.parameter
            {12345678: Parameter(0.1, 0.2, 0.3), ...}
            >>> tf.description
            None

        See Also:
            - :meth:`Transformer.to_dict`
        """
        parameter = {}
        for k, v in obj["parameter"].items():
            try:
                key = int(k)
            except ValueError:
                raise ValueError(f"expected integer for the key of the parameter field, we got {repr(k)}") from None

            parameter[key] = Parameter(
                latitude=v["latitude"],
                longitude=v["longitude"],
                altitude=v["altitude"],
            )

        return cls(
            format=obj["format"],
            parameter=parameter,
            description=obj.get("description"),
        )

    def to_dict(self) -> _types.TransformerDictType:
        """Returns a :obj:`dict` which represents `self`.

        This method is an inverse of :meth:`Transformer.from_dict`.

        Returns:
            the :obj:`dict` obj which typed as :obj:`.TransformerDict`

        Examples:
            >>> tf = Transformer(
            ...     description='my param',
            ...     format='SemiDynaEXE',
            ...     parameter={12345678: Parameter(0.1, 0.2, 0.3)},
            ... )
            >>> tf.to_dict()
            {
                'format': 'SemiDynaEXE',
                'parameter': {
                    12345678: {
                        'latitude': 0.1,
                        'longitude': 0.2,
                        'altitude': 0.3,
                    }
                },
                'description': 'my param',
            }

        See Also:
            - :meth:`Transformer.from_dict`
        """
        return {
            "format": self.format,
            "parameter": {k: v._asdict() for k, v in self.parameter.items()},  # type: ignore
            "description": self.description,
        }

    def statistics(self) -> Statistics:
        """Returns the statistics of the parameter.

        See :class:`StatisticData` for details of result's components.

        Returns:
            the statistics of the parameter

        Examples:
            From `SemiDynaEXE2023.par`

            >>> tf = Transformer(
            ...     format='SemiDynaEXE'
            ...     parameter={
            ...         54401005: Parameter(-0.00622, 0.01516, 0.0946),
            ...         54401055: Parameter(-0.0062, 0.01529, 0.08972),
            ...         54401100: Parameter(-0.00663, 0.01492, 0.10374),
            ...         54401150: Parameter(-0.00664, 0.01506, 0.10087),
            ...     }
            ... )
            >>> tf.statistics()
            StatisticalSummary(
                latitude=Statistics(
                    count=4,
                    mean=-0.006422499999999999,
                    std=0.00021264700797330775,
                    abs=0.006422499999999999,
                    min=-0.00664,
                    max=-0.0062
                ),
                longitude=Statistics(
                    count=4,
                    mean=0.0151075,
                    std=0.00013553136168429814,
                    abs=0.0151075,
                    min=0.01492,
                    max=0.01529
                ),
                altitude=Statistics(
                    count=4,
                    mean=0.0972325,
                    std=0.005453133846697696,
                    abs=0.0972325,
                    min=0.08972,
                    max=0.10374
                )
            )
        """
        # Surprisingly, the following code is fast enough.

        # ensure summation order
        params = sorted(((k, v) for k, v in self.parameter.items()), key=lambda t: t[0])

        kwargs = {}
        for name, arr in (
            ("latitude", tuple(map(lambda p: p[1].latitude, params))),
            ("longitude", tuple(map(lambda p: p[1].longitude, params))),
            ("altitude", tuple(map(lambda p: p[1].altitude, params))),
            ("horizontal", tuple(map(lambda p: p[1].horizontal, params))),
        ):
            if not arr:
                kwargs[name] = StatisticData(None, None, None, None, None, None)
                continue

            sum_ = math.fsum(arr)
            length = len(arr)

            if math.isnan(sum_):
                kwargs[name] = StatisticData(length, math.nan, math.nan, math.nan, math.nan, math.nan)
                continue

            mean = sum_ / length
            std = math.sqrt(math.fsum(tuple((mean - x) ** 2 for x in arr)) / length)

            kwargs[name] = StatisticData(
                count=length,
                mean=mean,
                std=std,
                abs=math.fsum(map(abs, arr)) / length,
                min=min(arr),
                max=max(arr),
            )

        return Statistics(**kwargs)

    def transform(
        self,
        latitude: float,
        longitude: float,
        altitude: float = 0.0,
        backward: bool = False,
    ) -> _point.Point:
        """Returns the transformed position.

        Args:
            latitude: the latitude [deg] of the point which satisfies 0.00333... <= and <= 66.666...
            longitude: the longitude [deg] of the point which satisfies 100.0 <= and <= 180.0
            altitude: the altitude [m] of the point
            backward: when :obj:`True`, this performs backward transformation

        Returns:
            the transformed point

        Raises:
            ParameterNotFoundError: when `latitude` and `longitude` points to an area
                                    where the parameter does not support
            ValueError: when `latitude` or `longitude` is unsupported value

        Examples:
            From `SemiDynaEXE2023.par`

            >>> tf = Transformer(
            ...     format='SemiDynaEXE',
            ...     parameter={
            ...         54401005: Parameter(-0.00622, 0.01516, 0.0946),
            ...         54401055: Parameter(-0.0062, 0.01529, 0.08972),
            ...         54401100: Parameter(-0.00663, 0.01492, 0.10374),
            ...         54401150: Parameter(-0.00664, 0.01506, 0.10087),
            ...     }
            ... )
            >>> tf.transform(36.10377479, 140.087855041, 2.34, backward=False)
            Point(latitude=36.103773017086695, longitude=140.08785924333452, altitude=2.4363138578103)
            >>> tf.transform(36.103773017086695, 140.08785924333452, 2.4363138578102994, backward=True)
            Point(latitude=36.10377479, longitude=140.087855041, altitude=2.34)

            Following identities hold:

            >>> tf.transform(*point, backward=False) == tf.forward(*point)
            True
            >>> tf.transform(*point, backward=True) == tf.backward(*point)
            True
        """
        func = self.backward if backward else self.forward
        return func(latitude, longitude, altitude=altitude)

    def forward(
        self,
        latitude: float,
        longitude: float,
        altitude: float = 0.0,
    ) -> _point.Point:
        """Returns the forward-transformed position.

        Args:
            latitude: the latitude [deg] of the point which satisfies 0.0 <= and <= 66.666...
            longitude: the longitude [deg] of the point which satisfies 100.0 <= and <= 180.0
            altitude: the altitude [m] of the point

        Returns:
            the transformed point

        Raises:
            ParameterNotFoundError: when `latitude` and `longitude` points to an area
                                    where the parameter does not support
            PointOutOfBoundsError: when `latitude` or `longitude` is out-of-bounds

        Examples:
            From `SemiDynaEXE2023.par`

            >>> tf = Transformer(
            ...     format='SemiDynaEXE',
            ...     parameter={
            ...         54401005: Parameter(-0.00622, 0.01516, 0.0946),
            ...         54401055: Parameter(-0.0062, 0.01529, 0.08972),
            ...         54401100: Parameter(-0.00663, 0.01492, 0.10374),
            ...         54401150: Parameter(-0.00664, 0.01506, 0.10087),
            ...     }
            ... )
            >>> tf.forward(36.10377479, 140.087855041, 2.34)
            Point(latitude=36.103773017086695, longitude=140.08785924333452, altitude=2.4363138578103)
        """
        corr = self.forward_corr(latitude, longitude)
        return _point.Point(
            latitude=latitude + corr.latitude,
            longitude=longitude + corr.longitude,
            altitude=altitude + corr.altitude,
        )

    def backward_compat(
        self,
        latitude: float,
        longitude: float,
        altitude: float = 0.0,
    ) -> _point.Point:
        """Returns the backward-transformed position compatible to GIAJ web app/APIs.

        This is compatible to GIAJ web app/APIs,
        and is **not** exact as the original as.

        Args:
            latitude: the latitude [deg] of the point which satisfies 0.00333... <= and <= 66.666...
            longitude: the longitude [deg] of the point which satisfies 100.0 <= and <= 180.0
            altitude: the altitude [m] of the point

        Returns:
            the transformed point

        Raises:
            ParameterNotFoundError: when `latitude` and `longitude` points to an area
                                    where the parameter does not support
            PointOutOfBoundsError: when `latitude` or `longitude` is out-of-bounds

        Examples:
            From `SemiDynaEXE2023.par`

            Notes, the exact solution is :obj:`Point(36.10377479, 140.087855041, 2.34)`.

            >>> tf = Transformer(
            ...     format='SemiDynaEXE',
            ...     parameter={
            ...         54401005: Parameter(-0.00622, 0.01516, 0.0946),
            ...         54401055: Parameter(-0.0062, 0.01529, 0.08972),
            ...         54401100: Parameter(-0.00663, 0.01492, 0.10374),
            ...         54401150: Parameter(-0.00664, 0.01506, 0.10087),
            ...     }
            ... )
            >>> tf.backward_compat(36.103773017086695, 140.08785924333452, 2.4363138578103)
            Point(latitude=36.10377479000002, longitude=140.087855041, altitude=2.339999999578243)
        """
        corr = self.backward_compat_corr(latitude, longitude)
        return _point.Point(
            latitude=latitude + corr.latitude,
            longitude=longitude + corr.longitude,
            altitude=altitude + corr.altitude,
        )

    def backward(self, latitude: float, longitude: float, altitude: float = 0.0):
        """Returns the backward-transformed position.

        The result's error from an exact solution is suppressed under :attr:`Transformer::ERROR_MAX`.

        Notes, the error is less than 1e-9 deg, which is
        error of GIAJ latitude and longitude parameter.
        This implies that altitude's error is less than 1e-5 [m],
        which is error of the GIAJ altitude parameter.

        Notes, this is not compatible to GIAJ web app/APIs (but more accurate).

        Args:
            latitude: the latitude [deg] of the point which satisfies 0.0 <= and <= 66.666...
            longitude: the longitude [deg] of the point which satisfies 100.0 <= and <= 180.0
            altitude: the altitude [m] of the point

        Returns:
            the transformed point

        Raises:
            ParameterNotFoundError: when `latitude` and `longitude` points to an area
                                    where the parameter does not support
            CorrectionNotFoundError: when the error from the exact solution is larger
                                     than :attr:`Transformer::ERROR_MAX`.
            PointOutOfBoundsError: when `latitude` or `longitude` is out-of-bounds

        Examples:
            From `SemiDynaEXE2023.par`

            Notes, the exact solution is :obj:`Point(36.10377479, 140.087855041, 2.34)`.
            In this case, no error remains.

            >>> tf = Transformer(
            ...     format='SemiDynaEXE',
            ...     parameter={
            ...         54401005: Parameter(-0.00622, 0.01516, 0.0946),
            ...         54401055: Parameter(-0.0062, 0.01529, 0.08972),
            ...         54401100: Parameter(-0.00663, 0.01492, 0.10374),
            ...         54401150: Parameter(-0.00664, 0.01506, 0.10087),
            ...     }
            ... )
            >>> tf.backward(36.103773017086695, 140.08785924333452, 2.4363138578103)
            Point(latitude=36.10377479, longitude=140.087855041, altitude=2.34)
        """
        corr = self.backward_corr(latitude, longitude)
        return _point.Point(
            latitude=latitude + corr.latitude,
            longitude=longitude + corr.longitude,
            altitude=altitude + corr.altitude,
        )

    def _parameter_quadruple(
        self,
        cell: _mesh.MeshCell,
    ):
        # finding parameter
        try:
            sw = self.parameter[cell.south_west.to_meshcode()]
        except KeyError as e:
            raise _error.ParameterNotFoundError(e.args[0], "sw") from None

        try:
            se = self.parameter[cell.south_east.to_meshcode()]
        except KeyError as e:
            raise _error.ParameterNotFoundError(e.args[0], "se") from None

        try:
            nw = self.parameter[cell.north_west.to_meshcode()]
        except KeyError as e:
            raise _error.ParameterNotFoundError(e.args[0], "nw") from None

        try:
            ne = self.parameter[cell.north_east.to_meshcode()]
        except KeyError as e:
            raise _error.ParameterNotFoundError(e.args[0], "ne") from None

        return sw, se, nw, ne

    def forward_corr(self, latitude: float, longitude: float) -> Correction:
        """Return the correction on forward-transformation.

        Used by :meth:`Transformer.forward`.

        Args:
            latitude: the latitude [deg] of the point which satisfies 0.0 <= and <= 66.666...
            longitude: the longitude [deg] of the point which satisfies 100.0 <= and <= 180.0

        Returns:
            the correction on forward transformation

        Raises:
            ParameterNotFoundError: when `latitude` and `longitude` points to an area
                                    where the parameter does not support
            PointOutOfBoundsError: when `latitude` or `longitude` is out-of-bounds

        Examples:
            From `SemiDynaEXE2023.par`

            >>> tf = Transformer(
            ...     format='SemiDynaEXE',
            ...     parameter={
            ...         54401005: Parameter(-0.00622, 0.01516, 0.0946),
            ...         54401055: Parameter(-0.0062, 0.01529, 0.08972),
            ...         54401100: Parameter(-0.00663, 0.01492, 0.10374),
            ...         54401150: Parameter(-0.00664, 0.01506, 0.10087),
            ...     }
            ... )
            >>> tf.forward_corr(36.10377479, 140.087855041)
            Correction(latitude=-1.7729133100878255e-06, longitude=4.202334510058886e-06, altitude=0.09631385781030007)
        """
        # resolving cell
        try:
            cell = _mesh.MeshCell.from_pos(latitude, longitude, mesh_unit=self.mesh_unit())
        except ValueError as e:
            raise _error.PointOutOfBoundsError from e

        # finding parameter
        sw, se, nw, ne = self._parameter_quadruple(cell)

        #
        # Main-Process: bilinear interpolation
        #

        # Note that;
        # y: latitude
        # x: longitude
        y, x = cell.position(latitude, longitude)

        #
        # bilinear interpolation
        #

        # Make the unit of lat and lng [deg] from [sec]
        # by diving by the scale, 3600.
        scale: Final = 3600

        # The following lat and lng have [sec] unit
        # because the unit of parameters is [sec], not [deg].
        lat = (
            bilinear_interpolation(
                sw=sw.latitude,
                se=se.latitude,
                nw=nw.latitude,
                ne=ne.latitude,
                lat=y,
                lng=x,
            )
            / scale
        )

        lng = (
            bilinear_interpolation(
                sw=sw.longitude,
                se=se.longitude,
                nw=nw.longitude,
                ne=ne.longitude,
                lat=y,
                lng=x,
            )
            / scale
        )

        alt = bilinear_interpolation(
            sw=sw.altitude,
            se=se.altitude,
            nw=nw.altitude,
            ne=ne.altitude,
            lat=y,
            lng=x,
        )

        return Correction(lat, lng, alt)

    def backward_compat_corr(self, latitude: float, longitude: float) -> Correction:
        """Return the correction on backward-transformation compatible to GIAJ web app/APIs.

        Used by :meth:`Transformer.backward_compat`.

        Args:
            latitude: the latitude [deg] of the point which satisfies 0.00333... <= and <= 66.666...
            longitude: the longitude [deg] of the point which satisfies 100.0 <= and <= 180.0

        Returns:
            the correction on backward transformation

        Raises:
            ParameterNotFoundError: when `latitude` and `longitude` points to an area
                                    where the parameter does not support
            PointOutOfBoundsError: when `latitude` or `longitude` is out-of-bounds

        Examples:
            From `SemiDynaEXE2023.par`

            >>> tf = Transformer(
            ...     format='SemiDynaEXE',
            ...     parameter={
            ...         54401005: Parameter(-0.00622, 0.01516, 0.0946),
            ...         54401055: Parameter(-0.0062, 0.01529, 0.08972),
            ...         54401100: Parameter(-0.00663, 0.01492, 0.10374),
            ...         54401150: Parameter(-0.00664, 0.01506, 0.10087),
            ...     }
            ... )
            >>> tf.backward_compat_corr(36.103773017086695, 140.08785924333452)
            Correction(latitude=1.7729133219831587e-06, longitude=-4.202334509042613e-06, altitude=-0.0963138582320569)
        """
        delta: Final = 1 / 300  # 12. / 3600.
        lat, lng = latitude - delta, longitude + delta

        if lat < 0 <= latitude:
            raise _error.PointOutOfBoundsError(f"latitude is too small, we got {latitude}") from None

        lat_corr, lng_corr, _ = self.forward_corr(lat, lng)
        lat, lng = latitude - lat_corr, longitude - lng_corr

        if lat < 0 <= latitude:
            raise _error.PointOutOfBoundsError(f"latitude is too small, we got {latitude}") from None

        corr = self.forward_corr(lat, lng)
        return Correction(-corr.latitude, -corr.longitude, -corr.altitude)

    def backward_corr(
        self,
        latitude: float,
        longitude: float,
    ) -> Correction:
        """Return the correction on backward-transformation.

        Used by :meth:`Transformer.backward`.

        Args:
            latitude: the latitude [deg] of the point which satisfies 0.0 <= and <= 66.666...
            longitude: the longitude [deg] of the point which satisfies 100.0 <= and <= 180.0

        Returns:
            the correction on backward transformation

        Raises:
            ParameterNotFoundError: when `latitude` and `longitude` points to an area
                                    where the parameter does not support
            CorrectionNotFoundError: when verification failed
            PointOutOfBoundsError: when `latitude` or `longitude` is out-of-bounds

        Examples:
            From `SemiDynaEXE2023.par`

            >>> tf = Transformer(
            ...     format='SemiDynaEXE',
            ...     parameter={
            ...         54401005: Parameter(-0.00622, 0.01516, 0.0946),
            ...         54401055: Parameter(-0.0062, 0.01529, 0.08972),
            ...         54401100: Parameter(-0.00663, 0.01492, 0.10374),
            ...         54401150: Parameter(-0.00664, 0.01506, 0.10087),
            ...     }
            ... )
            >>> tf.backward_corr(36.103773017086695, 140.08785924333452)
            Correction(latitude=1.7729133100878255e-06, longitude=-4.202334510058886e-06, altitude=-0.09631385781030007)
        """
        #
        # Newton's Method
        #
        # This is sufficient for most practical parameters,
        # but, technically, there are (a lot of) parameters
        # unable to find a solution near enough the exact solution
        # even if it increases the iteration.

        # Effectively sufficient, we verified with
        # - TKY2JGD.par.
        # - touhokutaiheiyouoki2011.par,
        # - and pos2jgd_202307_ITRF2014.par
        iteration: Final = 4

        # for [sec] to [deg]
        scale: Final = 3600

        # Xn
        xn = longitude
        yn = latitude

        for _ in range(iteration):
            try:
                cell = _mesh.MeshCell.from_pos(yn, xn, mesh_unit=self.mesh_unit())
            except ValueError as e:
                raise _error.PointOutOfBoundsError from e

            sw, se, nw, ne = self._parameter_quadruple(cell)
            y, x = cell.position(yn, xn)

            corr_x = (
                bilinear_interpolation(
                    sw=sw.longitude,
                    se=se.longitude,
                    nw=nw.longitude,
                    ne=ne.longitude,
                    lat=y,
                    lng=x,
                )
                / scale
            )
            corr_y = (
                bilinear_interpolation(
                    sw=sw.latitude,
                    se=se.latitude,
                    nw=nw.latitude,
                    ne=ne.latitude,
                    lat=y,
                    lng=x,
                )
                / scale
            )

            # f(x, y) of the newton method
            fx = longitude - (xn + corr_x)
            fy = latitude - (yn + corr_y)

            # which Jacobian
            fx_x = -1 - ((se.longitude - sw.longitude) * (1 - yn) + (ne.longitude - nw.longitude) * yn) / scale
            fx_y = -((nw.longitude - sw.longitude) * (1 - xn) + (ne.longitude - se.longitude) * xn) / scale
            fy_x = -((se.latitude - sw.latitude) * (1 - yn) + (ne.latitude - nw.latitude) * yn) / scale
            fy_y = -1 - ((nw.latitude - sw.latitude) * (1 - xn) + (ne.latitude - se.latitude) * xn) / scale

            # and its determinant
            det = fx_x * fy_y - fx_y * fy_x

            # update Xn
            xn -= (fy_y * fx - fx_y * fy) / det
            yn -= (fx_x * fy - fy_x * fx) / det

            # verify
            corr = self.forward_corr(yn, xn)
            if (
                abs(latitude - (yn + corr.latitude)) < self.MAX_ERROR
                and abs(longitude - (xn + corr.longitude)) < self.MAX_ERROR
            ):
                return Correction(-corr.latitude, -corr.longitude, -corr.altitude)

        raise _error.CorrectionNotFoundError(
            f"exhaust {iteration} iterations but error is still high, "
            f"we finally got {yn} and {xn} from {latitude} and {longitude}"
        ) from None


if __name__ == "__main__":
    pass
