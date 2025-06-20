"""Provides :class:`Transformer` etc."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Literal, NamedTuple, Protocol, TextIO

if TYPE_CHECKING:
    from typing import Final

    try:
        from typing import Self  # typing @ >= 3.11
    except ImportError:
        from typing_extensions import Self

    from . import types as _types

from . import error as _error
from . import mesh as _mesh
from . import par as _par
from . import point as _point

__all__ = [
    "Transformer",
    "Correction",
    "ParameterSet",
    "load",
    "loads",
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


def loads(  # noqa: C901
    s: str,
    format: _types.FormatType,
    *,
    description: str | None = None,
) -> Transformer:
    """Deserialize a par-formatted :obj:`str` into a :class:`Transformer`.

    This fills by 0.0 for altituse parameter when :obj:`'TKY2JGD'` or :obj:`'PatchJGD'` given to `format`,
    and for latitude and longitude when :obj:`'PatchJGD_H'` or :obj:`'HyokoRev'` given.

    See :obj:`.FormatType` for detail of :obj:`'PatchJGD_HV'`.

    Args:
        s: a par-formatted text
        format: the format of `s`
        description: the description of the parameter, defaulting the `s` header

    Returns:
        the :class:`Transformer` obj

    Raises:
        ParseParFileError: when invalid data found

    Examples:
        >>> s = '''<15 lines>
        ... MeshCode dB(sec)  dL(sec) dH(m)
        ... 12345678   0.00001   0.00002   0.00003'''
        >>> tf = loads(s, format="SemiDynaEXE")
        >>> result = tf.transform(35.0, 145.0)

        >>> s = '''<15 lines>
        ... MeshCode dB(sec)  dL(sec) dH(m)
        ... 12345678   0.00001   0.00002   0.00003'''
        >>> loads(s, format="SemiDynaEXE").parameter[12345678]
        Parameter(latitude=0.00001, longitude=0.0002, altitude=0.0003)
    """
    return Transformer(data=_par.loads(s, format=format, description=description))


def load(
    fp: TextIO,
    format: _types.FormatType,
    *,
    description: str | None = None,
) -> Transformer:
    """Deserialize a par-formatted file-like obj into a :class:`Transformer`.

    This fills by 0.0 for altituse parameter when :obj:`'TKY2JGD'` or :obj:`'PatchJGD'` given to `format`,
    and for latitude and longitude when :obj:`'PatchJGD_H'` or :obj:`'HyokoRev'` given.

    See :obj:`.FormatType` for detail of :obj:`'PatchJGD_HV'`.

    Args:
        fp: a par-formatted file-like obj
        format: the format of `fp`
        description: the description of the parameter, defaulting the `fp` header

    Returns:
        the :class:`Transformer` obj

    Raises:
        ParseParFileError: when invalid data found

    Examples:
        >>> with open("SemiDyna2023.par") as fp:
        ...     tf = load(fp, format="SemiDynaEXE")
        >>> result = tf.transform(35.0, 145.0)

        >>> s = '''<15 lines>
        ... MeshCode dB(sec)  dL(sec) dH(m)
        ... 12345678   0.00001   0.00002   0.00003'''
        >>> with io.StringIO(s) as fp:
        ...     tf = load(fp, format="SemiDynaEXE")
        Parameter(latitude=0.00001, longitude=0.0002, altitude=0.0003)
    """
    return loads(fp.read(), format=format, description=description)


def from_dict(obj) -> Transformer:
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
        >>> mapping = {
        ...     'format': 'SemiDynaEXE',
        ...     'parameter': {
        ...         12345678: {
        ...             'latitude': 0.1,
        ...             'longitude': 0.2,
        ...             'altitude': 0.3,
        ...         },
        ...         ...
        ...     },
        ...     'description': 'important my param',  # optional
        ... }
        >>> tf = from_dict(mapping)
        >>> tf.data
        ParData(
            format='SemiDynaEXE',
            parameter={
                12345678: Parameter('latitude': 0.1, 'longitude': 0.2, 'altitude': 0.3),
                ...
            },
            description='important my param'
        )

        >>> mapping = {
        ...     'format': 'SemiDynaEXE',
        ...     'parameter': {
        ...         '12345678': {
        ...             'latitude': 0.1,
        ...             'longitude': 0.2,
        ...             'altitude': 0.3,
        ...         },
        ...         ...
        ...     },
        ... }
        >>> tf = from_dict(mapping)
        >>> tf.data
        ParData(
            format='SemiDynaEXE',
            parameter={
                12345678: Parameter('latitude': 0.1, 'longitude': 0.2, 'altitude': 0.3),
                ...
            },
            description=None
        )
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


class ParameterSet(Protocol):
    """Interface for :class:`Transformer`."""

    def get(self, meshcode: int) -> _par.Parameter | None:
        """Returns :class:`Parameter` associated with `meshcode`, otherwise :class:`None`."""
        pass

    def mesh_unit(self) -> Literal[1, 5]:
        """Returns a mesh unit."""
        pass


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
        ...     data=ParData(
        ...         format="SemiDynaEXE",
        ...         parameter={
        ...             54401005: Parameter(-0.00622, 0.01516, 0.0946),
        ...             54401055: Parameter(-0.0062, 0.01529, 0.08972),
        ...             54401100: Parameter(-0.00663, 0.01492, 0.10374),
        ...             54401150: Parameter(-0.00664, 0.01506, 0.10087),
        ...         },
        ...     )
        ... )

        Forward transformation

        >>> tf.forward(36.10377479, 140.087855041, 2.34)
        Point(latitude=36.103773017086695, longitude=140.08785924333452, altitude=2.4363138578103)

        Backward transformation

        >>> tf.backward(36.103773017086695, 140.08785924333452, 2.4363138578103)
        Point(latitude=36.10377479, longitude=140.087855041, altitude=2.34)

        Backward transformation compatible to GIAJ web app/APIs

        >>> tf.backward_compat(36.103773017086695, 140.08785924333452, 2.4363138578103)
        Point(latitude=36.10377479000002, longitude=140.087855041, altitude=2.339999999578243)
    """

    data: ParameterSet
    MAX_ERROR: ClassVar[float] = 5e-14
    """Max error of :meth:`Transformer.backward` and :meth:`Transformer.backward_corr`."""

    def __repr__(self):
        # the parameter is too long for display
        fmt = "{}(data={!r})"
        return fmt.format(
            self.__class__.__qualname__,
            self.data,
        )

    @classmethod
    def from_dict(cls, obj: _types.ParDataLikeMappingType) -> Self:
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
            >>> mapping = {
            ...     'format': 'SemiDynaEXE',
            ...     'parameter': {
            ...         12345678: {
            ...             'latitude': 0.1,
            ...             'longitude': 0.2,
            ...             'altitude': 0.3,
            ...         },
            ...         ...
            ...     },
            ...     'description': 'important my param',  # optional
            ... }
            >>> tf = Transformer.from_dict(mapping)
            >>> tf.data
            ParData(
                format='SemiDynaEXE',
                parameter={
                    12345678: Parameter('latitude': 0.1, 'longitude': 0.2, 'altitude': 0.3),
                    ...
                },
                description='important my param'
            )

            >>> mapping = {
            ...     'format': 'SemiDynaEXE',
            ...     'parameter': {
            ...         '12345678': {
            ...             'latitude': 0.1,
            ...             'longitude': 0.2,
            ...             'altitude': 0.3,
            ...         },
            ...         ...
            ...     },
            ... }
            >>> tf = Transformer.from_dict(mapping)
            >>> tf.data
            ParData(
                format='SemiDynaEXE',
                parameter={
                    12345678: Parameter('latitude': 0.1, 'longitude': 0.2, 'altitude': 0.3),
                    ...
                },
                description='important my param'
            )
        """
        return cls(data=_par.ParData.from_dict(obj))

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
            ...     data=Pardata(
            ...         format="SemiDynaEXE",
            ...         parameter={
            ...             54401005: Parameter(-0.00622, 0.01516, 0.0946),
            ...             54401055: Parameter(-0.0062, 0.01529, 0.08972),
            ...             54401100: Parameter(-0.00663, 0.01492, 0.10374),
            ...             54401150: Parameter(-0.00664, 0.01506, 0.10087),
            ...         },
            ...     )
            ... )
            >>> tf.transform(36.10377479, 140.087855041, 2.34, backward=False)
            Point(latitude=36.103773017086695, longitude=140.08785924333452, altitude=2.4363138578103)
            >>> tf.transform(
            ...     36.103773017086695, 140.08785924333452, 2.4363138578102994, backward=True
            ... )
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
            ...     data=ParData(
            ...         format="SemiDynaEXE",
            ...         parameter={
            ...             54401005: Parameter(-0.00622, 0.01516, 0.0946),
            ...             54401055: Parameter(-0.0062, 0.01529, 0.08972),
            ...             54401100: Parameter(-0.00663, 0.01492, 0.10374),
            ...             54401150: Parameter(-0.00664, 0.01506, 0.10087),
            ...         },
            ...     )
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
            ...     data=ParData(
            ...         format="SemiDynaEXE",
            ...         parameter={
            ...             54401005: Parameter(-0.00622, 0.01516, 0.0946),
            ...             54401055: Parameter(-0.0062, 0.01529, 0.08972),
            ...             54401100: Parameter(-0.00663, 0.01492, 0.10374),
            ...             54401150: Parameter(-0.00664, 0.01506, 0.10087),
            ...         },
            ...     )
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
        This implies that altitude's error is (practically) less than 1e-5 [m],
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
                                     than :attr:`Transformer.ERROR_MAX`.
            PointOutOfBoundsError: when `latitude` or `longitude` is out-of-bounds

        Examples:
            From `SemiDynaEXE2023.par`

            Notes, the exact solution is :obj:`Point(36.10377479, 140.087855041, 2.34)`.
            In this case, no error remains.

            >>> tf = Transformer(
            ...     data=ParData(
            ...         format="SemiDynaEXE",
            ...         parameter={
            ...             54401005: Parameter(-0.00622, 0.01516, 0.0946),
            ...             54401055: Parameter(-0.0062, 0.01529, 0.08972),
            ...             54401100: Parameter(-0.00663, 0.01492, 0.10374),
            ...             54401150: Parameter(-0.00664, 0.01506, 0.10087),
            ...         },
            ...     )
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
        sw = self.data.get(cell.south_west.to_meshcode())
        if sw is None:
            raise _error.ParameterNotFoundError("sw") from None

        se = self.data.get(cell.south_east.to_meshcode())
        if se is None:
            raise _error.ParameterNotFoundError("se") from None

        nw = self.data.get(cell.north_west.to_meshcode())
        if nw is None:
            raise _error.ParameterNotFoundError("nw") from None

        ne = self.data.get(cell.north_east.to_meshcode())
        if ne is None:
            raise _error.ParameterNotFoundError("ne") from None

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
            ...     data=ParData(
            ...         format="SemiDynaEXE",
            ...         parameter={
            ...             54401005: Parameter(-0.00622, 0.01516, 0.0946),
            ...             54401055: Parameter(-0.0062, 0.01529, 0.08972),
            ...             54401100: Parameter(-0.00663, 0.01492, 0.10374),
            ...             54401150: Parameter(-0.00664, 0.01506, 0.10087),
            ...         },
            ...     )
            ... )
            >>> tf.forward_corr(36.10377479, 140.087855041)
            Correction(latitude=-1.7729133100878255e-06, longitude=4.202334510058886e-06, altitude=0.09631385781030007)
        """
        # resolving cell
        try:
            cell = _mesh.MeshCell.from_pos(latitude, longitude, mesh_unit=self.data.mesh_unit())
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
            ...     data=ParData(
            ...         format="SemiDynaEXE",
            ...         parameter={
            ...             54401005: Parameter(-0.00622, 0.01516, 0.0946),
            ...             54401055: Parameter(-0.0062, 0.01529, 0.08972),
            ...             54401100: Parameter(-0.00663, 0.01492, 0.10374),
            ...             54401150: Parameter(-0.00664, 0.01506, 0.10087),
            ...         },
            ...     )
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
            ...     data=ParData(
            ...         format="SemiDynaEXE",
            ...         parameter={
            ...             54401005: Parameter(-0.00622, 0.01516, 0.0946),
            ...             54401055: Parameter(-0.0062, 0.01529, 0.08972),
            ...             54401100: Parameter(-0.00663, 0.01492, 0.10374),
            ...             54401150: Parameter(-0.00664, 0.01506, 0.10087),
            ...         },
            ...     )
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
                cell = _mesh.MeshCell.from_pos(yn, xn, mesh_unit=self.data.mesh_unit())
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
