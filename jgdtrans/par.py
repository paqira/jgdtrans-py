"""Provides par file parsers."""

from __future__ import annotations

import math
import textwrap
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, NamedTuple

if TYPE_CHECKING:
    from typing import Callable, TextIO

    try:
        from typing import Self  # typing @ >= 3.11
    except ImportError:
        from typing_extensions import Self

    from . import types as _types

from . import error as _error
from . import mesh as _mesh

__all__ = [
    "is_format",
    "load",
    "loads",
    "Parameter",
    "ParData",
    "StatisticData",
    "Statistics",
]


def is_format(format: _types.FormatType) -> bool:
    """Returns :obj:`True` when `format` is valid.

    Args:
        format: a test value

    Returns:
        :obj:`True` when `format` is valid

    Examples:
        >>> is_format("TKY2JGD")
        True
        >>> is_format("SemiDynaEXE")
        True
        >>> is_format("Hi!")
        False
    """
    return format in (
        "TKY2JGD",
        "PatchJGD",
        "PatchJGD_H",
        "PatchJGD_HV",
        "HyokoRev",
        "SemiDynaEXE",
        "geonetF3",
        "ITRF2014",
    )


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


@dataclass(frozen=True, repr=False)
class ParData:
    """Par data obj."""

    format: _types.FormatType
    """The format of par file.

    See :obj:`.FormatType` for detail of :obj:`'PatchJGD_HV'`.
    """

    parameter: dict[int, Parameter]
    """The transformation parameter.

    The entry represents single line of the par file's parameter section,
    the key is meshcode, and the value is a :class:`.Parameter`
    (a triplet of latitude [sec], longitude [sec] and altitude [m]).
    """

    description: str | None = None
    """The description."""

    def __repr__(self):
        # the parameter is too long for display
        fmt = "{}(format={}, parameter=<{} ({} length) at 0x{:x}>, description={})"
        return fmt.format(
            self.__class__.__qualname__,
            self.format,
            self.parameter.__class__.__qualname__,
            len(self.parameter),
            id(self.parameter),
            (
                repr(textwrap.shorten(self.description, width=11))
                if isinstance(self.description, str)
                else self.description
            ),
        )

    def get(self, meshcode: int) -> Parameter | None:
        """Returns :class:`Parameter` associated with `meshcode`, otherwise :class:`None`."""
        return self.parameter.get(meshcode)

    def mesh_unit(self) -> Literal[1, 5]:
        """Returns a mesh unit."""
        return _mesh.mesh_unit(self.format)

    @classmethod
    def from_dict(cls, obj: _types.ParDataLikeMappingType) -> Self:
        """Makes a :class:`ParData` obj from :obj:`Mapping` obj.

        This parses meshcode, the key of `parameter`, into :obj:`int`.

        See :obj:`.FormatType` for detail of :obj:`'PatchJGD_HV'`.

        Args:
            obj: the :obj:`Mapping` of the format, the parameters,
                 and the description (optional)

        Returns:
            the :class:`ParData` obj

        Raises:
            DeserializeError: when fail to parse the meshcode

        Examples:
            >>> mapping = {
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
            >>> data = ParData.from_dict(mapping)
            >>> data.format
            'SemiDynaEXE'
            >>> data.parameter
            {12345678: Parameter(0.1, 0.2, 0.3), ...}
            >>> data.description
            'important my param'

            >>> mapping = {
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
            >>> data = ParData.from_dict(mapping)
            >>> data.format
            'SemiDynaEXE'
            >>> data.parameter
            {12345678: Parameter(0.1, 0.2, 0.3), ...}
            >>> data.description
            None

        See Also:
            - :meth:`ParData.to_dict`
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

    def to_dict(self) -> _types.ParDataDictType:
        """Returns a :obj:`dict` which represents `self`.

        This method is an inverse of :meth:`ParData.from_dict`.

        Returns:
            the :obj:`dict` obj which typed as :obj:`.TransformerDict`

        Examples:
            >>> data = ParData(
            ...     description="my param",
            ...     format="SemiDynaEXE",
            ...     parameter={12345678: Parameter(0.1, 0.2, 0.3)},
            ... )
            >>> data.to_dict()
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

        def convert(v: Parameter) -> _types.ParameterDictType:
            return _types.ParameterDictType(latitude=v.latitude, longitude=v.longitude, altitude=v.altitude)

        return _types.ParDataDictType(
            format=self.format,
            parameter={k: convert(v) for k, v in self.parameter.items()},
            description=self.description,
        )

    def statistics(self) -> Statistics:
        """Returns the statistics of the parameter.

        See :class:`StatisticData` for details of result's components.

        Returns:
            the statistics of the parameter

        Examples:
            From `SemiDynaEXE2023.par`

            >>> data = ParData(
            ...     format='SemiDynaEXE'
            ...     parameter={
            ...         54401005: Parameter(-0.00622, 0.01516, 0.0946),
            ...         54401055: Parameter(-0.0062, 0.01529, 0.08972),
            ...         54401100: Parameter(-0.00663, 0.01492, 0.10374),
            ...         54401150: Parameter(-0.00664, 0.01506, 0.10087),
            ...     }
            ... )
            >>> data.statistics()
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


def parse(
    text: str,
    header: slice,
    mesh_code: Callable[[str], int],
    latitude: Callable[[str], float],
    longitude: Callable[[str], float],
    altitude: Callable[[str], float],
    description: str | None = None,
) -> tuple[dict[int, Parameter], str | None]:
    """Returns the arguments of :class:`.Transformer` constructor by parsing `s`.

    Args:
        text: the input test
        header: the header lines
        mesh_code: the parser of meshcode
        latitude: the parser of latitude
        longitude: the parser of longitude
        altitude: the parser of altitude
        description: the description

    Returns:
        the arguments of :class:`.Transformer` constructor

    Raises:
        ParseParFileError: when unexpected data found
    """
    lines = text.splitlines()

    if len(lines) < header.stop:
        raise _error.ParseParFileError(
            f"too short text, we got {len(lines)} line(s), we expected {header.stop} at least"
        ) from None

    desc = ("\n".join(lines[header]) + "\n") if description is None else description

    parameters: dict[int, Parameter] = {}
    lineno = header.stop
    for line in lines[lineno:]:
        lineno += 1

        try:
            _mesh_code = mesh_code(line)
        except ValueError:
            raise _error.ParseParFileError(
                f"unexpected value for 'meshcode', we got a line '{line}' [lineno {lineno}]"
            ) from None

        try:
            _latitude = latitude(line)
        except ValueError:
            raise _error.ParseParFileError(
                f"unexpected value for 'latitude', we got a line '{line}' [lineno {lineno}]"
            ) from None

        try:
            _longitude = longitude(line)
        except ValueError:
            raise _error.ParseParFileError(
                f"unexpected value for 'longitude', we got a line '{line}' [lineno {lineno}]"
            ) from None

        try:
            _altitude = altitude(line)
        except ValueError:
            raise _error.ParseParFileError(
                f"unexpected value for 'altitude', we got a line '{line}' [lineno {lineno}]"
            ) from None

        parameters[_mesh_code] = Parameter(latitude=_latitude, longitude=_longitude, altitude=_altitude)

    return parameters, desc


def loads(  # noqa: C901
    s: str,
    format: _types.FormatType,
    *,
    description: str | None = None,
) -> ParData:
    """Deserialize a par-formatted :obj:`str` into a :class:`ParData`.

    This fills by 0.0 for altituse parameter when :obj:`'TKY2JGD'` or :obj:`'PatchJGD'` given to `format`,
    and for latitude and longitude when :obj:`'PatchJGD_H'` or :obj:`'HyokoRev'` given.

    See :obj:`.FormatType` for detail of :obj:`'PatchJGD_HV'`.

    Args:
        s: a par-formatted text
        format: the format of `s`
        description: the description of the parameter, defaulting the `s` header

    Returns:
        the :class:`ParData` obj

    Raises:
        ParseParFileError: when invalid data found

    Examples:
        >>> s = '''<15 lines>
        ... MeshCode dB(sec)  dL(sec) dH(m)
        ... 12345678   0.00001   0.00002   0.00003'''
        >>> data = loads(s, format="SemiDynaEXE")
        >>> tf = Tramsformer(data=data)
        >>> result = tf.transform(35.0, 145.0)

        >>> s = '''<15 lines>
        ... MeshCode dB(sec)  dL(sec) dH(m)
        ... 12345678   0.00001   0.00002   0.00003'''
        >>> loads(s, format="SemiDynaEXE").parameter[12345678]
        Parameter(latitude=0.00001, longitude=0.0002, altitude=0.0003)
    """
    if format == "TKY2JGD":
        header = slice(None, 2)

        # fmt: off
        def mesh_code(line: str): return int(line[0:8])
        def latitude(line: str): return float(line[9:18])
        def longitude(line: str): return float(line[19:28])
        def altitude(line: str): return 0.0
        # fmt: on
    elif format == "PatchJGD":
        header = slice(None, 16)

        # fmt: off
        def mesh_code(line: str): return int(line[0:8])
        def latitude(line: str): return float(line[9:18])
        def longitude(line: str): return float(line[19:28])
        def altitude(line: str): return 0.0
        # fmt: on
    elif format == "PatchJGD_H":
        header = slice(None, 16)

        # fmt: off
        def mesh_code(line: str): return int(line[0:8])
        def latitude(line: str): return 0.0
        def longitude(line: str): return 0.0
        def altitude(line: str): return float(line[9:18])
        # fmt: on
    elif format == "HyokoRev":
        header = slice(None, 16)

        # fmt: off
        def mesh_code(line: str): return int(line[0:8])
        def latitude(line: str): return 0.0
        def longitude(line: str): return 0.0
        def altitude(line: str): return float(line[12:21])
        # fmt: on
    elif format in ("SemiDynaEXE", "PatchJGD_HV"):
        header = slice(None, 16)

        # fmt: off
        def mesh_code(line: str): return int(line[0:8])
        def latitude(line: str): return float(line[9:18])
        def longitude(line: str): return float(line[19:28])
        def altitude(line: str): return float(line[29:38])
        # fmt: on
    elif format in ("geonetF3", "ITRF2014"):
        header = slice(None, 18)

        # fmt: off
        def mesh_code(line: str): return int(line[0:8])
        def latitude(line: str): return float(line[12:21])
        def longitude(line: str): return float(line[22:31])
        def altitude(line: str): return float(line[32:41])
        # fmt: on
    else:
        raise ValueError(f"unexpected format give, we got '{format}'")

    parameter, desc = parse(
        text=s,
        header=header,
        mesh_code=mesh_code,
        latitude=latitude,
        longitude=longitude,
        altitude=altitude,
        description=description,
    )
    return ParData(format=format, parameter=parameter, description=desc)


def load(
    fp: TextIO,
    format: _types.FormatType,
    *,
    description: str | None = None,
) -> ParData:
    """Deserialize a par-formatted file-like obj into a :class:`ParData`.

    This fills by 0.0 for altituse parameter when :obj:`'TKY2JGD'` or :obj:`'PatchJGD'` given to `format`,
    and for latitude and longitude when :obj:`'PatchJGD_H'` or :obj:`'HyokoRev'` given.

    See :obj:`.FormatType` for detail of :obj:`'PatchJGD_HV'`.

    Args:
        fp: a par-formatted file-like obj
        format: the format of `fp`
        description: the description of the parameter, defaulting the `fp` header

    Returns:
        the :class:`ParData` obj

    Raises:
        ParseParFileError: when invalid data found

    Examples:
        >>> with open("SemiDyna2023.par") as fp:
        ...     data = load(fp, format="SemiDynaEXE")
        >>> tf = Tramsformer(data=data)
        >>> result = tf.transform(35.0, 145.0)

        >>> s = '''<15 lines>
        ... MeshCode dB(sec)  dL(sec) dH(m)
        ... 12345678   0.00001   0.00002   0.00003'''
        >>> with io.StringIO(s) as fp:
        ...     load(fp, format="SemiDynaEXE").parameter[12345678]
        Parameter(latitude=0.00001, longitude=0.0002, altitude=0.0003)
    """
    return loads(fp.read(), format=format, description=description)


if __name__ == "__main__":
    pass
