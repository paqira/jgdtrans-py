"""Provides par file parsers."""

from __future__ import annotations

from typing import Callable, TextIO

from . import error as _error
from . import transformer as _trans
from . import types as _types

__all__ = [
    "is_format",
    "load",
    "loads",
]


def is_format(format: _types.FormatType) -> bool:
    """Returns :obj:`True` when `format` is valid.

    Args:
        format: a test value

    Returns:
        :obj:`True` when `format` is valid

    Examples:
        >>> is_format('TKY2JGD')
        True
        >>> is_format('SemiDynaEXE')
        True
        >>> is_format('Hi!')
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


# TODO: typing error
def parse(
    text: str,
    header: slice,
    mesh_code: Callable[[str], int],
    latitude: Callable[[str], float],
    longitude: Callable[[str], float],
    altitude: Callable[[str], float],
    format: _types.FormatType,
    description: str | None = None,
):
    """Returns the arguments of :class:`.Transformer` constructor by parsing `s`.

    Args:
        text: the input test
        header: the header lines
        mesh_code: the parser of meshcode
        latitude: the parser of latitude
        longitude: the parser of longitude
        altitude: the parser of altitude
        format: the format of par file
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

    description = "\n".join(lines[header]) + "\n" if description is None else description

    parameters: dict[int, _trans.Parameter] = {}
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

        parameters[_mesh_code] = _trans.Parameter(latitude=_latitude, longitude=_longitude, altitude=_altitude)

    return {
        "description": description,
        "format": format,
        "parameter": parameters,
    }


def loads(
    s: str,
    format: _types.FormatType,
    *,
    description: str | None = None,
):
    """Deserialize a par-formatted :obj:`str` into a :class:`.Transformer`.

    This fills by 0.0 for altituse parameter when :obj:`'TKY2JGD'` or :obj:`'PatchJGD'` given to `format`,
    and for latitude and longitude when :obj:`'PatchJGD_H'` or :obj:`'HyokoRev'` given.

    See :obj:`.FormatType` for detail of :obj:`'PatchJGD_HV'`.

    Args:
        s: a par-formatted text
        format: the format of `s`
        description: the description of the parameter, defaulting the `s` header

    Returns:
        the :class:`.Transformer` obj

    Raises:
        ParseParFileError: when invalid data found

    Examples:
        >>> s = '''<15 lines>
        ... MeshCode dB(sec)  dL(sec) dH(m)
        ... 12345678   0.00001   0.00002   0.00003'''
        >>> tf = loads(s, format='SemiDynaEXE')
        >>> result = tf.transform(35.0, 145.0)

        >>> s = '''<15 lines>
        ... MeshCode dB(sec)  dL(sec) dH(m)
        ... 12345678   0.00001   0.00002   0.00003'''
        >>> loads(s, format='SemiDynaEXE').parameter[12345678]
        Parameter(latitude=0.00001, longitude=0.0002, altitude=0.0003)
    """
    if format == "TKY2JGD":
        kwargs = dict(
            text=s,
            header=slice(None, 2),
            mesh_code=lambda line: int(line[0:8]),
            latitude=lambda line: float(line[9:18]),
            longitude=lambda line: float(line[19:28]),
            altitude=lambda line: 0.0,
            format=format,
            description=description,
        )
    elif format == "PatchJGD":
        kwargs = dict(
            text=s,
            header=slice(None, 16),
            mesh_code=lambda line: int(line[0:8]),
            latitude=lambda line: float(line[9:18]),
            longitude=lambda line: float(line[19:28]),
            altitude=lambda line: 0,
            format=format,
            description=description,
        )
    elif format == "PatchJGD_H":
        kwargs = dict(
            text=s,
            header=slice(None, 16),
            mesh_code=lambda line: int(line[0:8]),
            latitude=lambda line: 0,
            longitude=lambda line: 0,
            altitude=lambda line: float(line[9:18]),
            format=format,
            description=description,
        )
    elif format == "HyokoRev":
        kwargs = dict(
            text=s,
            header=slice(None, 16),
            mesh_code=lambda line: int(line[0:8]),
            latitude=lambda line: 0,
            longitude=lambda line: 0,
            altitude=lambda line: float(line[12:21]),
            format=format,
            description=description,
        )
    elif format in ("SemiDynaEXE", "PatchJGD_HV"):
        kwargs = dict(
            text=s,
            header=slice(None, 16),
            mesh_code=lambda line: int(line[0:8]),
            latitude=lambda line: float(line[9:18]),
            longitude=lambda line: float(line[19:28]),
            altitude=lambda line: float(line[29:38]),
            format=format,
            description=description,
        )
    elif format in ("geonetF3", "ITRF2014"):
        kwargs = dict(
            text=s,
            header=slice(None, 18),
            mesh_code=lambda line: int(line[0:8]),
            latitude=lambda line: float(line[12:21]),
            longitude=lambda line: float(line[22:31]),
            altitude=lambda line: float(line[32:41]),
            format=format,
            description=description,
        )
    else:
        raise ValueError(f"unexpected format give, we got '{format}'")

    return _trans.Transformer(**parse(**kwargs))  # type: ignore


def load(
    fp: TextIO,
    format: _types.FormatType,
    *,
    description: str | None = None,
):
    """Deserialize a par-formatted file-like obj into a :class:`.Transformer`.

    This fills by 0.0 for altituse parameter when :obj:`'TKY2JGD'` or :obj:`'PatchJGD'` given to `format`,
    and for latitude and longitude when :obj:`'PatchJGD_H'` or :obj:`'HyokoRev'` given.

    See :obj:`.FormatType` for detail of :obj:`'PatchJGD_HV'`.

    Args:
        fp: a par-formatted file-like obj
        format: the format of `fp`
        description: the description of the parameter, defaulting the `fp` header

    Returns:
        the :class:`.Transformer` obj

    Raises:
        ParseParFileError: when invalid data found

    Examples:
        >>> with open('SemiDyna2023.par') as fp:
        ...     tf = load(fp, format='SemiDynaEXE')
        >>> result = tf.transform(35.0, 145.0)

        >>> s = '''<15 lines>
        ... MeshCode dB(sec)  dL(sec) dH(m)
        ... 12345678   0.00001   0.00002   0.00003'''
        >>> with io.StringIO(s) as fp:
        ...     load(fp, format='SemiDynaEXE').parameter[12345678]
        Parameter(latitude=0.00001, longitude=0.0002, altitude=0.0003)
    """
    return loads(fp.read(), format=format, description=description)


if __name__ == "__main__":
    pass
