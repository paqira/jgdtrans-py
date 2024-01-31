"""Provides :class:`Transformer` etc."""

from __future__ import annotations

import math
import textwrap
from dataclasses import dataclass
from functools import cached_property
from typing import Mapping, NamedTuple

from typing_extensions import Final, Literal, Self

from . import error as _error
from . import mesh as _mesh
from . import point as _point
from . import types as _types

__all__ = [
    "Transformer",
    "Parameter",
    "Correction",
    "StatisticalSummary",
    "Statistics",
    #
    "from_dict",
    #
]


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


def from_dict(obj: _types.TransformerLikeMapping) -> Transformer:
    """Makes a :class:`Transformer` obj from :obj:`Mapping` obj.

    Args:
        obj: the :obj:`Mapping` of the unit, the parameter,
             and the description (optional) fields

    Returns:
        the :class:`Transformer` obj

    Raises:
        ParseError: if fail to parse meshcode

    Examples:
        >>> data = {
        ...     'description': 'important my param',  # optional
        ...     'unit': 1,  # 1 or 5
        ...     'parameter': {
        ...         12345678: {
        ...             'latitude': 0.1
        ...             'longitude': 0.2
        ...             'altitude': 0.3
        ...         },
        ...         ...
        ...     }
        ... }
        >>> transformer = from_dict(data)
        >>> transformer.description
        'important my param'
        >>> transformer.unit
        1
        >>> transformer.parameter
        {12345678: Parameter(0.1, 0.2, 0.3), ...}

        >>> data = {
        ...     'unit': 1,
        ...     'parameter': {
        ...         '12345678': {
        ...             'latitude': 0.1
        ...             'longitude': 0.2
        ...             'altitude': 0.3
        ...         },
        ...         ...
        ...     }
        ... }
        >>> transformer = from_dict(data)
        >>> transformer.description
        None
        >>> transformer.unit
        1
        >>> transformer.parameter
        {12345678: Parameter(0.1, 0.2, 0.3), ...}

    See Also:
        - :meth:`Transformer.from_dict`
    """
    return Transformer.from_dict(obj)


class Correction(NamedTuple):
    """The transformation correction."""

    latitude: float
    """The latitude correction [deg]"""
    longitude: float
    """The longitude correction [deg]"""
    altitude: float
    """The altitude correction [m]"""

    @cached_property
    def horizontal(self) -> float:
        r""":math:`\sqrt{\text{latitude}^2 + \text{longitude}^2}` [deg]."""
        return math.hypot(self.latitude, self.longitude)


class Parameter(NamedTuple):
    """The parameter triplet.

    We emphasize that the unit is [sec], not [deg],
    for latitude and longitude.

    It should fill by :obj:`0.0` instead of :obj:`nan`
    if the parameter does not exist, as parsers does.
    """

    latitude: float
    """The latitude parameter [sec]"""
    longitude: float
    """The latitude parameter [sec]"""
    altitude: float
    """The altitude parameter [m]"""

    @cached_property
    def horizontal(self) -> float:
        r""":math:`\sqrt{\text{latitude}^2 + \text{longitude}^2}` [sec]."""
        return math.hypot(self.latitude, self.longitude)


class Statistics(NamedTuple):
    """The statistics of parameter.

    This is a component of the result that :meth:`Transformer.summary` returns.
    """

    count: int | None
    """The count"""
    mean: float | None
    """The mean ([sec] or [m])"""
    std: float | None
    """The standard variance ([sec] or [m])"""
    abs: float | None
    r""":math:`(1/n) \sum_{i=1}^n \left| \text{parameter}_i \right|` ([sec] or [m])"""
    min: float | None
    """The minimum ([sec] or [m])"""
    max: float | None
    """The maximum ([sec] or [m])"""


class StatisticalSummary(NamedTuple):
    """The statistical summary of parameter.

    This is a result that :meth:`Transformer.summary` returns.
    """

    latitude: Statistics
    """The statistics of latitude"""
    longitude: Statistics
    """The statistics of longitude"""
    altitude: Statistics
    """The statistics of altitude"""


@dataclass(frozen=True, slots=True)
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
        ...     unit=1,
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

        >>> tf.backward(36.103773017086695, 140.08785924333452, 2.4363138578102994)
        Point(latitude=36.10377479000002, longitude=140.087855041, altitude=2.339999999578243)

        Verified backward transformation

        >>> tf.backward_safe(36.103773017086695, 140.08785924333452, 2.4363138578103)
        Point(latitude=36.10377479, longitude=140.087855041, altitude=2.3399999999970085)
    """

    unit: Literal[1, 5]
    """The mesh unit, :obj:`1` or :obj:`5`"""

    parameter: Mapping[int, Parameter]
    """The transformation parameter

    The entry represents single line of par file's parameter section,
    the key is meshcode, and the value is a :class:`.Parameter`,
    a triplet of latitude [sec], longitude [sec] and altitude [m].
    """

    description: str | None = None
    """The description"""

    def __post_init__(self):
        if self.unit not in (1, 5):
            raise ValueError(f"expected unit is 1 or 5, we got {self.unit}")

    def __repr__(self):
        # the parameter is too long for display
        fmt = "{}(unit={}, parameter=<object ({} length) at 0x{:x}>, description={})"
        return fmt.format(
            self.__class__.__name__,
            self.unit,
            len(self.parameter),
            id(self.parameter),
            (
                repr(textwrap.shorten(self.description, width=11))
                if isinstance(self.description, str)
                else self.description
            ),
        )

    @classmethod
    def from_dict(cls, obj: _types.TransformerLikeMapping) -> Self:
        """Makes a :class:`Transformer` obj from :obj:`Mapping` obj.

        This parses meshcode, the key of `parameter`, into :obj:`int`.

        Args:
            obj: the :obj:`Mapping` of the unit, the parameters,
                 and the description (optional)

        Returns:
            the :class:`Transformer` obj

        Raises:
            ParseError: if fail to parse the meshcode

        Examples:
            >>> data = {
            ...     'description': 'important my param',  # optional
            ...     'unit': 1,  # 1 or 5
            ...     'parameter': {
            ...         12345678: {
            ...             'latitude': 0.1
            ...             'longitude': 0.2
            ...             'altitude': 0.3
            ...         },
            ...         ...
            ...     }
            ... }
            >>> transformer = Transformer.from_dict(data)
            >>> transformer.description
            'important my param'
            >>> transformer.unit
            1
            >>> transformer.parameter
            {12345678: Parameter(0.1, 0.2, 0.3), ...}

            >>> data = {
            ...     'unit': 1,
            ...     'parameter': {
            ...         '12345678': {
            ...             'latitude': 0.1
            ...             'longitude': 0.2
            ...             'altitude': 0.3
            ...         },
            ...         ...
            ...     }
            ... }
            >>> transformer = Transformer.from_dict(data)
            >>> transformer.description
            None
            >>> transformer.unit
            1
            >>> transformer.parameter
            {12345678: Parameter(0.1, 0.2, 0.3), ...}

        See Also:
            - :meth:`Transformer.to_dict`.
        """
        parameter = {}
        for k, v in obj["parameter"].items():
            try:
                parameter[int(k)] = Parameter(
                    latitude=v["latitude"],
                    longitude=v["longitude"],
                    altitude=v["altitude"],
                )
            except ValueError:
                raise _error.ParseError(
                    f"expected a parsable value for the key of the parameter field, we got {repr(k)}"
                ) from None

        return cls(
            unit=obj["unit"],
            parameter=parameter,
            description=obj.get("description"),
        )

    def to_dict(self) -> _types.TransformerDict:
        """Returns a :obj:`dict` which represents `self`.

        This method is an inverse of :meth:`Transformer.from_dict`.

        Returns:
            the :obj:`dict` obj which typed as :obj:`.TransformerDict`

        Examples:
            >>> transformer = Transformer(
            ...     description='my param',
            ...     unit=1,
            ...     parameter={12345678: Parameter(0.1, 0.2, 0.3)}
            ... )
            >>> transformer.to_dict()
            {
                'description': 'my param',
                'unit': 1,
                'parameter': {
                    12345678: {
                        'latitude': 0.1,
                        'longitude': 0.2,
                        'altitude': 0.3,
                    }
                }
            }

        See Also:
            - :meth:`Transformer.from_dict`
        """
        return {
            "description": self.description,
            "unit": self.unit,
            "parameter": {k: v._asdict() for k, v in self.parameter.items()},
        }

    def summary(self) -> StatisticalSummary:
        """Returns the statistical summary.

        This fills the result by :obj:`None` if the population is empty,
        and drops :obj:`nan` from the population of the summary.

        See :class:`Statistics` for details of result's components.

        Returns:
            the statistics of the parameter

        Examples:
            From `SemiDynaEXE2023.par`

            >>> tf = Transformer(
            ...     unit=1,
            ...     parameter={
            ...         54401005: Parameter(-0.00622, 0.01516, 0.0946),
            ...         54401055: Parameter(-0.0062, 0.01529, 0.08972),
            ...         54401100: Parameter(-0.00663, 0.01492, 0.10374),
            ...         54401150: Parameter(-0.00664, 0.01506, 0.10087),
            ...     }
            ... )
            >>> tf.summary()
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

        latitude = tuple(filter(lambda v: not math.isnan(v), map(lambda p: p.latitude, self.parameter.values())))
        longitude = tuple(filter(lambda v: not math.isnan(v), map(lambda p: p.longitude, self.parameter.values())))
        altitude = tuple(filter(lambda v: not math.isnan(v), map(lambda p: p.altitude, self.parameter.values())))

        kwargs = {}
        for name, arr in (("latitude", latitude), ("longitude", longitude), ("altitude", altitude)):
            if not arr:
                kwargs[name] = Statistics(None, None, None, None, None, None)
                continue

            length = len(arr)

            sum_ = math.fsum(arr)
            mean = sum_ / length
            std = math.sqrt(math.fsum((mean - x) ** 2 for x in arr) / length)

            kwargs[name] = Statistics(
                count=length,
                mean=mean,
                std=std,
                abs=math.fsum(map(abs, arr)) / length,
                min=min(arr),
                max=max(arr),
            )

        return StatisticalSummary(**kwargs)

    def transform(
        self,
        latitude: float,
        longitude: float,
        altitude: float = 0.0,
        backward: bool = False,
    ) -> _point.Point:
        """Returns the transformed position.

        Backward-transformation is *not* exact
        as the original *TKY2JGD for Windows Ver.1.3.79* and the web APIs are.

        There are points where unable to perform backward transformation
        even if they are the results of the forward transformation,
        because the forward transformation moves them to the area where the parameter does not support.

        We note that :meth:`Transformer.backward_safe` performs verified backward transformation.

        Args:
            latitude: the latitude [deg] of the point which satisfies 0.00333... <= and <= 66.666...
            longitude: the longitude [deg] of the point which satisfies 100.0 <= and <= 180.0
            altitude: the altitude [m] of the point
            backward: this performs backward transformation if :obj:`True` given

        Returns:
            the transformed point

        Raises:
            ParameterNotFoundError: if `latitude` and `longitude` points to an area
                                    where the parameter does not support
            ValueError: if `latitude` or `longitude` is unsupported value

        Examples:
            From `SemiDynaEXE2023.par`

            >>> tf = Transformer(
            ...     unit=5,
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
            Point(latitude=36.10377479000002, longitude=140.087855041, altitude=2.339999999578243)
        """
        func = self.backward if backward else self.forward
        return func(latitude, longitude, altitude=altitude)  # type: ignore

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
            ParameterNotFoundError: if `latitude` and `longitude` points to an area
                                    where the parameter does not support
            ValueError: if `latitude` or `longitude` is unsupported value

        Examples:
            From `SemiDynaEXE2023.par`

            >>> tf = Transformer(
            ...     unit=5,
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

    def backward(
        self,
        latitude: float,
        longitude: float,
        altitude: float = 0.0,
    ) -> _point.Point:
        """Returns the backward-transformed position.

        This is *not* exact as the original *TKY2JGD for Windows Ver.1.3.79*
        and the web APIs are (as far as we researched).

        There are points where unable to perform backward transformation
        even if they are the results of the forward transformation,
        because the forward transformation moves them to the area where the parameter does not support.

        We note that :meth:`Transformer.backward_safe` performs verified backward transformation.

        Args:
            latitude: the latitude [deg] of the point which satisfies 0.00333... <= and <= 66.666...
            longitude: the longitude [deg] of the point which satisfies 100.0 <= and <= 180.0
            altitude: the altitude [m] of the point

        Returns:
            the transformed point

        Raises:
            ParameterNotFoundError: if `latitude` and `longitude` points to an area
                                    where the parameter does not support
            ValueError: if `latitude` or `longitude` is unsupported value

        Examples:
            From `SemiDynaEXE2023.par`

            >>> tf = Transformer(
            ...     unit=1,
            ...     parameter={
            ...         54401005: Parameter(-0.00622, 0.01516, 0.0946),
            ...         54401055: Parameter(-0.0062, 0.01529, 0.08972),
            ...         54401100: Parameter(-0.00663, 0.01492, 0.10374),
            ...         54401150: Parameter(-0.00664, 0.01506, 0.10087),
            ...     }
            ... )
            >>> tf.backward(36.103773017086695, 140.08785924333452, 2.4363138578103)
            Point(latitude=36.10377479000002, longitude=140.087855041, altitude=2.339999999578243)
        """
        corr = self.backward_corr(latitude, longitude)
        return _point.Point(
            latitude=latitude + corr.latitude,
            longitude=longitude + corr.longitude,
            altitude=altitude + corr.altitude,
        )

    def backward_safe(self, latitude: float, longitude: float, altitude: float = 0.0):
        """Returns the validated backward-transformed position.

        The result's drifting from the exact solution
        is less than error of the GIAJ latitude and longitude parameter,
        2.7e-9 [deg], for each latitude and longitude.
        The altitude's drifting is less than 1e-5 [m] wihch is error of the GIAJ altitude parameter.

        Args:
            latitude: the latitude [deg] of the point which satisfies 0.0 <= and <= 66.666...
            longitude: the longitude [deg] of the point which satisfies 100.0 <= and <= 180.0
            altitude: the altitude [m] of the point

        Returns:
            the transformed point

        Raises:
            ParameterNotFoundError: if `latitude` and `longitude` points to an area
                                    where the parameter does not support
            NotConvergeError: if verification failed
            ValueError: if `latitude` or `longitude` is unsupported value

        Examples:
            From `SemiDynaEXE2023.par`

            >>> tf = Transformer(
            ...     unit=1,
            ...     parameter={
            ...         54401005: Parameter(-0.00622, 0.01516, 0.0946),
            ...         54401055: Parameter(-0.0062, 0.01529, 0.08972),
            ...         54401100: Parameter(-0.00663, 0.01492, 0.10374),
            ...         54401150: Parameter(-0.00664, 0.01506, 0.10087),
            ...     }
            ... )
            >>> tf.backward_safe(36.103773017086695, 140.08785924333452, 2.4363138578103)
            Point(latitude=36.10377479, longitude=140.087855041, altitude=2.3399999999970085)

            The error is small enough,
            it's zero for latitude and longitude in this case;

            >>> origin = Point(36.10377479, 140.087855041, 2.34)
            >>> result = tf.backward_safe(*tf.forward(*origin))
            >>> result.latitude - origin.latitude
            0.0
            >>> result.longitude - origin.longitude
            0.0
            >>> result.altitude - origin.altitude
            2.9913849175500218e-12
        """
        corr = self.backward_corr_safe(latitude, longitude)
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
            sw = self.parameter[cell.sw.to_meshcode()]
        except KeyError as e:
            raise _error.ParameterNotFoundError(e.args[0], "sw") from None

        try:
            se = self.parameter[cell.se.to_meshcode()]
        except KeyError as e:
            raise _error.ParameterNotFoundError(e.args[0], "se") from None

        try:
            nw = self.parameter[cell.nw.to_meshcode()]
        except KeyError as e:
            raise _error.ParameterNotFoundError(e.args[0], "nw") from None

        try:
            ne = self.parameter[cell.ne.to_meshcode()]
        except KeyError as e:
            raise _error.ParameterNotFoundError(e.args[0], "ne") from None

        return sw, se, nw, ne

    def forward_corr(self, latitude: float, longitude: float) -> Correction:
        """Return the correction on forward-transformation.

        This is used by :meth:`Transformer.forward_corr`.

        Args:
            latitude: the latitude [deg] of the point which satisfies 0.0 <= and <= 66.666...
            longitude: the longitude [deg] of the point which satisfies 100.0 <= and <= 180.0

        Returns:
            the correction on forward transformation

        Raises:
            ParameterNotFoundError: if `latitude` and `longitude` points to an area
                                    where the parameter does not support
            ValueError: if `latitude` or `longitude` is unsupported value

        Examples:
            From `SemiDynaEXE2023.par`

            >>> tf = Transformer(
            ...     unit=1,
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
        cell = _mesh.MeshCell.from_pos(latitude, longitude, unit=self.unit)

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

    def backward_corr(self, latitude: float, longitude: float) -> Correction:
        """Return the correction on backward-transformation.

        This is used by :meth:`Transformer.backward_corr`.

        Args:
            latitude: the latitude [deg] of the point which satisfies 0.00333... <= and <= 66.666...
            longitude: the longitude [deg] of the point which satisfies 100.0 <= and <= 180.0

        Returns:
            the correction on backward transformation

        Raises:
            ParameterNotFoundError: if `latitude` and `longitude` points to an area
                                    where the parameter does not support
            ValueError: if `latitude` or `longitude` is unsupported value

        Examples:
            From `SemiDynaEXE2023.par`

            >>> tf = Transformer(
            ...     unit=1,
            ...     parameter={
            ...         54401005: Parameter(-0.00622, 0.01516, 0.0946),
            ...         54401055: Parameter(-0.0062, 0.01529, 0.08972),
            ...         54401100: Parameter(-0.00663, 0.01492, 0.10374),
            ...         54401150: Parameter(-0.00664, 0.01506, 0.10087),
            ...     }
            ... )
            >>> tf.backward_corr(36.103773017086695, 140.08785924333452)
            Correction(latitude=1.7729133219831587e-06, longitude=-4.202334509042613e-06, altitude=-0.0963138582320569)
        """
        a: Final = 1 / 300  # 12. / 3600.
        lat, lng = latitude - a, longitude + a

        if lat < 0:
            raise ValueError(f"latitude is too small, we got {latitude}") from None

        lat_corr, lng_corr, _ = self.forward_corr(lat, lng)
        lat, lng = latitude - lat_corr, longitude - lng_corr

        if lat < 0:
            raise ValueError(f"latitude is too small, we got {latitude}") from None

        corr = self.forward_corr(lat, lng)
        return Correction(-corr.latitude, -corr.longitude, -corr.altitude)

    def backward_corr_safe(
        self,
        latitude: float,
        longitude: float,
    ) -> Correction:
        """Return the verified correction on backward-transformation.

        This is used by :meth:`Transformer.backward_safe`.

        Args:
            latitude: the latitude [deg] of the point which satisfies 0.0 <= and <= 66.666...
            longitude: the longitude [deg] of the point which satisfies 100.0 <= and <= 180.0

        Returns:
            the correction on backward transformation

        Raises:
            ParameterNotFoundError: if `latitude` and `longitude` points to an area
                                    where the parameter does not support
            NotConvergeError: if verification failed
            ValueError: if `latitude` or `longitude` is unsupported value

        Examples:
            From `SemiDynaEXE2023.par`

            >>> tf = Transformer(
            ...     unit=1,
            ...     parameter={
            ...         54401005: Parameter(-0.00622, 0.01516, 0.0946),
            ...         54401055: Parameter(-0.0062, 0.01529, 0.08972),
            ...         54401100: Parameter(-0.00663, 0.01492, 0.10374),
            ...         54401150: Parameter(-0.00664, 0.01506, 0.10087),
            ...     }
            ... )
            >>> tf.backward_corr_safe(36.103773017086695, 140.08785924333452)
            Correction(latitude=1.772913310099049e-06, longitude=-4.202334510033827e-06, altitude=-0.0963138578132916)
        """
        #
        # Newton's Method
        #
        # This is sufficient for most practical parameters,
        # but, technically, there are (a lot of) parameters
        # unable to find a solution near enough the exact solution
        # even if it increases the iteration.

        # the GIAJ parameter error is 1e-5 [sec] ~ 2.7e-9 [deg]
        criteria = 2.5e-9

        # Effectively sufficient, we verified with
        # - TKY2JGD.par.
        # - touhokutaiheiyouoki2011.par,
        # - and pos2jgd_202307_ITRF2014.par
        iteration = 3

        # for [sec] to [deg]
        scale: Final = 3600

        # Xn
        yn = latitude
        xn = longitude

        for _ in range(iteration):
            cell = _mesh.MeshCell.from_pos(yn, xn, unit=self.unit)
            sw, se, nw, ne = self._parameter_quadruple(cell)

            y, x = cell.position(yn, xn)

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

            # f(x, y) of the newton method
            fx = longitude - (xn + corr_x)
            fy = latitude - (yn + corr_y)

            # which Jacobian
            fx_x = -1 - ((se.longitude - sw.longitude) * (1 - yn) + (ne.longitude - nw.longitude) * yn) / scale
            fx_y = -((nw.longitude - sw.longitude) * (1 - xn) + (ne.longitude - se.longitude) * xn) / scale
            fy_x = -((se.latitude - sw.latitude) * (1 - yn) + (ne.latitude - nw.latitude) * yn) / scale
            fy_y = -1 - ((ne.latitude - sw.latitude) * (1 - xn) + (ne.latitude - se.latitude) * xn) / scale

            # and its determinant
            det = fx_x * fy_y - fy_x * fy_x

            # update Xn
            xn -= (fy_y * fx - fx_y * fy) / det
            yn -= (fx_x * fy - fy_x * fx) / det

            # verify
            corr = self.forward_corr(yn, xn)
            if abs(latitude - (yn + corr.latitude)) <= criteria and abs(longitude - (xn + corr.longitude)) <= criteria:
                return Correction(-corr.latitude, -corr.longitude, -corr.altitude)

        raise _error.NotConvergeError(
            f"exhaust {iteration} iterations but error is still high, "
            f"we finally got {yn} and {xn} from {latitude} and {longitude}"
        ) from None


if __name__ == "__main__":
    pass
