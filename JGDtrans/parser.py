"""Provides parsers."""

from __future__ import annotations

import datetime as dt
import re
from typing import Callable, NamedTuple, TextIO

from typing_extensions import Literal

from . import error as _error
from . import transformer as _trans
from . import types as _types

__all__ = [
    "load",
    "loads",
    #
    "Version",
    "FormatVersion",
    "MetaData",
    #
    "metadata",
    "version",
    #
    "parse_par",
    #
    "TKY2JGD",
    "PatchJGD",
    "PatchJGD_H",
    "PatchJGD_HV",
    "HyokoRev",
    "SemiDynaEXE",
    "geonetF3",
    "ITRF2014",
]


class Version(NamedTuple):
    """Version of par file."""

    major: int
    """The major number"""
    minor: int
    """The minor number"""
    patch: int
    """The patch number"""
    supplemental: str | None
    """The supplemental information (?), :obj:`'001'`, :obj:`'010'` etc."""


class FormatVersion(NamedTuple):
    """Format version of par file."""

    major: int
    """The major number"""
    minor: int
    """The minor number"""


class MetaData(NamedTuple):
    """Metadata of par file."""

    format_version: FormatVersion
    published_by: str
    national_datum: str
    positioning_datum: str
    version_of_parameter: Version
    epoch_of_parameter: dt.date
    release_date: dt.date
    applicable_area: str
    start_of_applicable_period: dt.date
    end_of_applicable_period: dt.date
    data_fields: str
    data_field_separator: str
    based_on: str


def version(text: str) -> tuple[str, Version]:
    """Returnd the version data from TKY2JGD, PatchJGD, PatchJGD(H), HyokoRev and SemiDyna header.

    Args:
        text: the version test, tipically first line of par file
              of TKY2JGD, PatchJGD, PatchJGD(H), HyokoRev and SemiDyna header

    Returns:
        the version data

    Raises:
        ParseError: if failed to parse

    Examples:
        >>> version('JGD2000-TokyoDatum Ver.2.1.2')
        ('JGD2000-TokyoDatum', Version(major=0, minor=1, patch=2, supplemental=None))
        >>> version('for PatchJGD        Ver.1.0.0　 010')
        ('PatchJGD', Version(major=1, minor=2, patch=3, supplemental='010'))
        >>> version('for PatchJGD(H)     Ver.1.0.0　 010')
        ('PatchJGD(H)', Version(major=1, minor=0, patch=0, supplemental='010'))
        >>> version('for SemiDynaEXE    Ver.1.0.0')
        ('SemiDynaEXE', Version(major=1, minor=0, patch=0, supplemental=None))
    """
    pattern = re.compile(
        r"^(?:for\s+)?(?P<name>[\w\W]+?)"
        r"\s+[vV]er[.](?P<major>\d+)[.](?P<minor>\d+)[.](?P<patch>\d+)"
        r"(?:\s+(?P<sub>\d+))?\s*$"
    )
    mo = pattern.match(text)
    if mo:
        name, major, minor, patch, sub = mo.groups()
        return name, Version(int(major), int(minor), int(patch), sub)
    raise _error.ParseError(text)


def metadata(text: str) -> MetaData:
    r"""Returns parsed metadata of geonetF3 and ITRF2014.

    This supports `FORMAT_VERSION >= 1.01`.

    Args:
        text: the header of geonetF3 or ITRF2014 par file

    Returns:
        the persed data

    Raises:
        ParseError: if failed to parse

    Examples:
        >>> s = '''GRIDDED CORRECTION PARAMETER FOR POS2JGD
        ... FORMAT_VERSION             = 1.01
        ... PUBLISHED_BY               = GEOSPATIAL INFORMATION AUTHORITY OF JAPAN
        ... NATIONAL_DATUM             = JGD2011
        ... POSITIONING_DATUM          = ITRF2014+GRS80
        ... VERSION_OF_PARAMETER       = Ver.1.0.0
        ... EPOCH_OF_PARAMETER         = 20230401
        ... RELEASE_DATE               = 20230531
        ... APPLICABLE_AREA            = INHABITED AREA OF JAPAN
        ... START_OF_APPLICABLE_PERIOD = 20230601
        ... END_OF_APPLICABLE_PERIOD   = 20230831
        ... DATA_FIELDS                = '4 MeshCode dB dL dH'
        ... DATA_FIELD_SEPARATOR       = \s+
        ... BASED_ON                   = GEONET_CORS'''
        >>> metadata(s)
        MetaData(
            format_version=FormatVersion(major=1, minor=1),
            published_by='GEOSPATIAL INFORMATION AUTHORITY OF JAPAN',
            national_datum='JGD2011',
            positioning_datum='ITRF2014+GRS80',
            version_of_parameter=Version(major=1, minor=0, patch=0, supplemental=None),
            epoch_of_parameter=date(2023, 4, 1),
            release_date=date(2023, 5, 31),
            applicable_area='INHABITED AREA OF JAPAN',
            start_of_applicable_period=date(2023, 6, 1),
            end_of_applicable_period=date(2023, 8, 31),
            data_fields="'4 MeshCode dB dL dH'",
            data_field_separator='\s+',
            based_on='GEONET_CORS'
        )
    """
    specs = (
        ("FORMAT_VERSION", r"\d+[.]\d+"),
        ("PUBLISHED_BY", r"[\w\W]+?"),
        ("NATIONAL_DATUM", r"[\w\W]+?"),
        ("POSITIONING_DATUM", r"[\w\W]+?"),
        (
            "VERSION_OF_PARAMETER",
            r"[vV]er[.]\d+[.]\d+[.]\d+",
        ),
        (
            "EPOCH_OF_PARAMETER",
            r"\d{8}",
        ),
        (
            "RELEASE_DATE",
            r"\d{8}",
        ),
        (
            "APPLICABLE_AREA",
            r"[\w\W]+?",
        ),
        (
            "START_OF_APPLICABLE_PERIOD",
            r"\d{8}",
        ),
        (
            "END_OF_APPLICABLE_PERIOD",
            r"\d{8}",
        ),
        ("DATA_FIELDS", r"[\w\W]+?"),
        ("DATA_FIELD_SEPARATOR", r"[\w\W]+?"),
        ("BASED_ON", r"[\w\W]+?"),
    )
    pattern = re.compile(
        "|".join("(?:^ *{0} *= *(?P<{0}>{1}) *$)".format(name, ptn) for name, ptn in specs),
        flags=re.MULTILINE,
    )

    res = {}
    for mo in pattern.finditer(text):
        name = mo.lastgroup
        value = mo.group(name)

        if name in ("FORMAT_VERSION",):
            major, minor = value.split(".")
            value = FormatVersion(int(major), int(minor))
        elif name in ("VERSION_OF_PARAMETER",):
            _, major, minor, patch = value.split(".")
            value = Version(int(major), int(minor), int(patch), None)
        elif name in (
            "EPOCH_OF_PARAMETER",
            "RELEASE_DATE",
            "START_OF_APPLICABLE_PERIOD",
            "END_OF_APPLICABLE_PERIOD",
        ):
            value = dt.datetime.strptime(value, "%Y%m%d").date()

        res[name] = value

    try:
        return MetaData(*tuple(res[name] for name, *_ in specs))  # type: ignore
    except KeyError as e:
        raise _error.ParseError(f"field '{e.args[0]}' not found, or value may be inappropriate") from None


def parse_par(
    text: str,
    header: slice,
    mesh_code: Callable[[str], int],
    latitude: Callable[[str], float],
    longitude: Callable[[str], float],
    altitude: Callable[[str], float],
    unit: Literal[1, 5],
    description: str | None = None,
) -> dict[str, str | None | int | _trans.Parameter]:
    """Returns the arguments of :class:`.Transformer` constructor by parsing `s`.

    Args:
        text: the input test
        header: the header lines
        mesh_code: the parser of meshcode
        latitude: the parser of latitude
        longitude: the parser of longitude
        altitude: the parser of altitude
        unit: the unit of the mesh, :obj:`1` or :obj:`5`
        description: the description

    Returns:
        the arguments of :class:`.Transformer` constructor

    Raises:
        ParseError: if unexpected data found
    """
    lines = text.splitlines()

    parameters: dict[int, _trans.Parameter] = {}
    lineno = header.stop
    for line in lines[lineno:]:
        lineno += 1

        try:
            _mesh_code = mesh_code(line)
        except ValueError:
            raise _error.ParseError(
                f"unexpected value for 'meshcode', " f"we got a line '{line}' [lineno {lineno}]"
            ) from None

        try:
            _latitude = latitude(line)
        except ValueError:
            raise _error.ParseError(
                f"unexpected value for 'latitude', " f"we got a line '{line}' [lineno {lineno}]"
            ) from None

        try:
            _longitude = longitude(line)
        except ValueError:
            raise _error.ParseError(
                f"unexpected value for 'longitude', " f"we got a line '{line}' [lineno {lineno}]"
            ) from None

        try:
            _altitude = altitude(line)
        except ValueError:
            raise _error.ParseError(
                f"unexpected value for 'altitude', " f"we got a line '{line}' [lineno {lineno}]"
            ) from None

        parameters[_mesh_code] = _trans.Parameter(latitude=_latitude, longitude=_longitude, altitude=_altitude)

    return {
        "description": "\n".join(lines[header]) if description is None else description,
        "unit": unit,
        "parameter": parameters,
    }


def loads(
    s: str,
    format: _types.FormatType,
    description: str | None = None,
):
    """Deserialize a par-formatted :obj:`str` into a :class:`.Transformer`.

    This fills by 0.0 for altituse parameter when :obj:`"TKY2JGD"` or :obj:`"PatchJGD"` given to `format`,
    and for latitude and longitude when :obj:`"PatchJGD_H"` or :obj:`"HyokoRev"` given.

    See :func:`.PatchJGD_HV` for detail on the :obj:`"PatchJGD_HV"` case.

    Args:
        s: a par-formatted text
        format: the format of `s`
        description: the description of the parameter, defaulting the `s` header

    Returns:
        the :class:`.Transformer` obj

    Raises:
        ParseError: if invalid data found

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
    if format == "TKY2JGD":
        return TKY2JGD(s, description=description)
    elif format == "PatchJGD":
        return PatchJGD(s, description=description)
    elif format == "PatchJGD_H":
        return PatchJGD_H(s, description=description)
    elif format == "PatchJGD_HV":
        return PatchJGD_HV(s, description=description)
    elif format == "SemiDynaEXE":
        return SemiDynaEXE(s, description=description)
    elif format == "geonetF3":
        return geonetF3(s, description=description)
    elif format == "ITRF2014":
        return ITRF2014(s, description=description)
    raise ValueError(f"unexpected format give, we got '{format}'")


def load(
    fp: TextIO[str],
    format: _types.FormatType,
    description: str | None = None,
):
    """Deserialize a par-formatted file-like obj into a :class:`.Transformer`.

    This fills by 0.0 for altituse parameter when :obj:`"TKY2JGD"` or :obj:`"PatchJGD"` given to `format`,
    and for latitude and longitude when :obj:`"PatchJGD_H"` or :obj:`"HyokoRev"` given.

    See :func:`.PatchJGD_HV` for detail on the :obj:`"PatchJGD_HV"` case.

    Args:
        fp: a par-formatted file-like obj
        format: the format of `fp`
        description: the description of the parameter, defaulting the `fp` header

    Returns:
        the :class:`.Transformer` obj

    Raises:
        ParseError: if invalid data found

    Examples:
        >>> with open('SemiDyna2023.par') as fp:
        ...     tf = load(fp, format="SemiDynaEXE")
        >>> result = tf.transform(35.0, 145.0)

        >>> s = '''<15 lines>
        ... MeshCode dB(sec)  dL(sec) dH(m)
        ... 12345678   0.00001   0.00002   0.00003'''
        >>> with io.StringIO(s) as fp:
        ...     load(fp, format="SemiDynaEXE").parameter[12345678]
        Parameter(latitude=0.00001, longitude=0.0002, altitude=0.0003)
    """
    return loads(fp.read(), format=format, description=description)


def TKY2JGD(  # noqa: N802
    s: str,
    description: str | None = None,
) -> _trans.Transformer:
    """Deserialize *TKY2JGD*-formatted :obj:`str` into a :class:`.Transformer`:.

    This fills by 0.0 for altituse parameter.

    Args:
        s: a TKY2JGD-formatted text
        description: the description of the parameter,
                     defaulting the `s` header (the first 2 lines)

    Returns:
        the :class:`.Transformer` obj

    Raises:
        ParseError: if invalid data found

    Examples:
        >>> with open('TKY2JGD.par') as f:
        ...     tf = TKY2JGD(f.read())
        >>> result = tf.transform(35.0, 145.0)

        >>> s = '''<1 line>
        ... MeshCode   dB(sec)   dL(sec)
        ... 12345678   0.00001   0.00002'''
        >>> TKY2JGD(s).parameter[12345678]
        Parameter(latitude=0.00001, longitude=0.00002, altitude=0.0)
    """
    return _trans.Transformer(
        **parse_par(
            s,
            header=slice(None, 2),
            mesh_code=lambda line: int(line[0:8]),
            latitude=lambda line: float(line[9:18]),
            longitude=lambda line: float(line[19:28]),
            altitude=lambda line: 0.0,
            unit=1,
            description=description,
        )
    )


def PatchJGD(s: str, description: str | None = None) -> _trans.Transformer:  # noqa: N802
    """Deserialize *PatchJGD*-formatted :obj:`str` into a :class:`.Transformer`.

    This fills by 0.0 for altituse parameter.

    Args:
        s: the PatchJGD-formatted text
        description: the description of the parameter,
                     defaulting the `s` header (the first 16 lines)

    Returns:
        the :class:`.Transformer` obj

    Raises:
        ParseError: if invalid data found

    Examples:
        >>> with open('PatchJGD.par') as f:
        ...     tf = PatchJGD(f.read())
        >>> result = tf.transform(35.0, 145.0)

        >>> s = '''<15 lines>
        ... MeshCode   dB(sec)   dL(sec)
        ... 12345678   0.00001   0.00002'''
        >>> PatchJGD(s).parameter[12345678]
        Parameter(latitude=0.00001, longitude=0.00002, altitude=0.0)
    """
    return _trans.Transformer(
        **parse_par(
            s,
            header=slice(None, 16),
            mesh_code=lambda line: int(line[0:8]),
            latitude=lambda line: float(line[9:18]),
            longitude=lambda line: float(line[19:28]),
            altitude=lambda line: 0,
            unit=1,
            description=description,
        )
    )


def PatchJGD_H(s: str, description: str | None = None) -> _trans.Transformer:  # noqa: N802
    """Deserialize *PatchJGD(H)*-formatted :obj:`str` into a :class:`.Transformer`.

    This fills by 0.0 for latitude and longitude parameter.

    Args:
        s: the PatchJGD(H)-formatted text
        description: the description of the parameter,
                     defaulting the `s` header (the first line)

    Returns:
        the :class:`.Transformer` obj

    Raises:
        ParseError: if invalid data found

    Examples:
        >>> with open('PatchJGD(H).par') as f:
        ...     tf = PatchJGD_H(f.read())
        >>> result = tf.transform(35.0, 145.0)

        >>> s = '''<15 lines>
        ... MeshCode   dH(m)     0.00000
        ... 12345678   0.00001   0.00000'''
        >>> PatchJGD_H(s).parameter[12345678]
        Parameter(latitude=0.0, longitude=0.0, altitude=0.00001)
    """
    return _trans.Transformer(
        **parse_par(
            s,
            header=slice(None, 16),
            mesh_code=lambda line: int(line[0:8]),
            latitude=lambda line: 0,
            longitude=lambda line: 0,
            altitude=lambda line: float(line[9:18]),
            unit=1,
            description=description,
        )
    )


def PatchJGD_HV(s: str, description: str | None = None) -> _trans.Transformer:  # noqa: N802
    """Deserialize *PatchJGD(HV)*-formatted :obj:`str` into a :class:`.Transformer`.

    This is a deserializer of a composition of PatchJGD and PatchJGD(H) par files
    for the same event, e.g. `touhokutaiheiyouoki2011.par` and `touhokutaiheiyouoki2011_h.par`.
    We note that transformation works fine with such data,
    and GIAJ does not distribute such file.

    It should fill by zero for the parameters of remaining transformation
    in areas where it supports only part of the transformation as a result of composition
    in order to support whole area of each parameter,
    e.g. altitude of Chubu (中部地方) on the composition of
    `touhokutaiheiyouoki2011.par` and `touhokutaiheiyouoki2011_h.par`.

    The composite data should be in the same format as SemiDynaEXE.

    Args:
        s: the PatchJGD(HV)-formatted text
        description: description of the parameter,
                     defaulting .par header (first 16 lines)

    Returns:
        the :class:`.Transformer` obj

    Raises:
        ParseError: if invalid data found

    Examples:
        >>> with open('PatchJGD(HV).par') as f:
        ...     tf = PatchJGD_HV(f.read())
        >>> result = tf.transform(35.0, 145.0)

        >>> s = '''<15 lines>
        ... MeshCode      dB(sec)   dL(sec)   dH(m)
        ... 12345678      0.00001   0.00002   0.00003'''
        >>> PatchJGD_HV(s).parameter[12345678]
        Parameter(latitude=0.00001, longitude=0.00002, altitude=0.00003)
    """
    return _trans.Transformer(
        **parse_par(
            s,
            header=slice(None, 16),
            mesh_code=lambda line: int(line[0:8]),
            latitude=lambda line: float(line[9:18]),
            longitude=lambda line: float(line[19:28]),
            altitude=lambda line: float(line[29:38]),
            unit=1,
            description=description,
        )
    )


def HyokoRev(s: str, description: str | None = None) -> _trans.Transformer:  # noqa: N802
    """Deserialize *HyokoRev*-formatted :obj:`str` into a :class:`.Transformer`.

    This fills by 0.0 for latitude and longitude parameter.

    Args:
        s: the HyokoRev-formatted text
        description: the description of the parameter,
                     defaulting the `s` header (the first line)

    Returns:
        the :class:`.Transformer` obj

    Raises:
        ParseError: if invalid data found

    Examples:
        >>> with open('HyokoRev.par') as f:
        ...     tf = HyokoRev(f.read())
        >>> result = tf.transform(35.0, 145.0)

        >>> s = '''<15 lines>
        ... MeshCode      dH(m)        0.00000
        ... 12345678      0.00001      0.00000'''
        >>> HyokoRev(s).parameter[12345678]
        Parameter(latitude=0.0, longitude=0.0, altitude=0.0001)
    """
    return _trans.Transformer(
        **parse_par(
            s,
            header=slice(None, 16),
            mesh_code=lambda line: int(line[0:8]),
            latitude=lambda line: 0,
            longitude=lambda line: 0,
            altitude=lambda line: float(line[12:21]),
            unit=1,
            description=description,
        )
    )


def SemiDynaEXE(s: str, description: str | None = None) -> _trans.Transformer:  # noqa: N802
    """Deserialize *SemiDynaEXE*-formatted :obj:`str` into a :class:`.Transformer`.

    Args:
        s: the SemiDynaEXE-formatted text
        description: the description of the parameter,
                     defaulting the `s` header (the first 16 lines)

    Returns:
        the :class:`.Transformer` obj

    Raises:
        ParseError: if invalid data found

    Examples:
        >>> with open('SemiDynaEXE.par') as f:
        ...     tf = SemiDynaEXE(f.read())
        >>> result = tf.transform(35.0, 145.0)

        >>> s = '''<15 lines>
        ... MeshCode dB(sec)  dL(sec) dH(m)
        ... 12345678   0.00001   0.00002   0.00003'''
        >>> SemiDynaEXE(s).parameter[12345678]
        Parameter(latitude=0.00001, longitude=0.0002, altitude=0.0003)
    """
    return _trans.Transformer(
        **parse_par(
            s,
            header=slice(None, 16),
            mesh_code=lambda line: int(line[0:8]),
            latitude=lambda line: float(line[9:18]),
            longitude=lambda line: float(line[19:28]),
            altitude=lambda line: float(line[29:38]),
            unit=5,
            description=description,
        )
    )


def geonetF3(s: str, description: str | None = None) -> _trans.Transformer:  # noqa: N802
    """Deserialize *geonetF3*-formatted :obj:`str` into a :class:`.Transformer`.

    Args:
        s: the geonetF3-formatted text
        description: the description of the parameter,
                     defaulting the `s` header (the first 18 lines)

    Returns:
        the :class:`.Transformer` obj

    Raises:
        ParseError: if invalid data found

    Examples:
        >>> with open('geonetF3.par') as f:
        ...     tf = geonetF3(f.read())
        >>> result = tf.transform(35.0, 145.0)

        >>> s = '''<17 lines>
        ... END OF HEADER
        ... 12345678      0.00001   0.00002   0.00003'''
        >>> geonetF3(s).parameter[12345678]
        Parameter(latitude=0.00001, longitude=0.00002, altitude=0.00003)
    """
    return _trans.Transformer(
        **parse_par(
            s,
            header=slice(None, 18),
            mesh_code=lambda line: int(line[0:8]),
            latitude=lambda line: float(line[12:21]),
            longitude=lambda line: float(line[22:31]),
            altitude=lambda line: float(line[32:41]),
            unit=5,
            description=description,
        )
    )


def ITRF2014(s: str, description: str | None = None) -> _trans.Transformer:  # noqa: N802
    """Deserialize *ITRF2014*-formatted :obj:`str` into a :class:`.Transformer`.

    Args:
        s: the ITRF2014-formatted text
        description: the description of the parameter,
                     defaulting the `s` header (first 18 lines)

    Returns:
        the :class:`.Transformer` obj

    Raises:
        ParseError: if invalid data found

    Examples:
        >>> with open('ITRF2014.par') as f:
        ...     tf = ITRF2014(f.read())
        >>> result = tf.transform(35.0, 145.0)

        >>> s = '''<17 lines>
        ... END OF HEADER
        ... 12345678      0.00001   0.00002   0.00003'''
        >>> ITRF2014(s).parameter[12345678]
        Parameter(latitude=0.00001, longitude=0.00002, altitude=0.00003)
    """
    return _trans.Transformer(
        **parse_par(
            s,
            header=slice(None, 18),
            mesh_code=lambda line: int(line[0:8]),
            latitude=lambda line: float(line[12:21]),
            longitude=lambda line: float(line[22:31]),
            altitude=lambda line: float(line[32:41]),
            unit=5,
            description=description,
        )
    )


if __name__ == "__main__":
    pass
