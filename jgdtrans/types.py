"""Provides types."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, TypedDict

from typing_extensions import (
    Required,  # typing @ >= 3.11
    TypeAlias,  # typing @ >= 3.10
)

__all__ = [
    "MeshUnitType",
    "FormatType",
    #
    "ParameterDictType",
    "TransformerDictType",
    "TransformerLikeMappingType",
]

MeshUnitType: TypeAlias = Literal[1, 5]
"""Type of mesh unit."""


FormatType: TypeAlias = Literal[
    "TKY2JGD",
    "PatchJGD",
    "PatchJGD_H",
    "PatchJGD_HV",
    "HyokoRev",
    "SemiDynaEXE",
    "geonetF3",
    "ITRF2014",
]
"""Type of par file's format.

Notes:
    The format :obj:`'PatchJGD_HV'` is for composition of PatchJGD and PatchJGD(H) par files
    for the same event, e.g. `touhokutaiheiyouoki2011.par` and `touhokutaiheiyouoki2011_h.par`.
    We note that transformation works fine with such data,
    and GIAJ does not distribute such file.

    It should fill by zero for the parameters of remaining transformation
    in areas where it supports only part of the transformation as a result of composition
    in order to support whole area of each parameter,
    e.g. altitude of Chubu (中部地方) on the composition of
    `touhokutaiheiyouoki2011.par` and `touhokutaiheiyouoki2011_h.par`.

    The composite data should be in the same format as SemiDynaEXE.
"""


class ParameterDictType(TypedDict):
    """Type for :meth:`.Transformer.to_dict` and :meth:`.Transformer.from_dict`."""

    latitude: float
    """The latitude parameter on the point [sec]."""
    longitude: float
    """The longitude parameter on the point [sec]."""
    altitude: float
    """The altitude parameter on the point [m]."""


class TransformerDictType(TypedDict):
    """Return type of :meth:`.Transformer.to_dict`."""

    format: FormatType
    """The format of par file."""
    parameter: dict[int, ParameterDictType]
    """The parameters."""
    description: str | None
    """The description of the parameter."""


class TransformerLikeMappingType(TypedDict, total=False):
    """Argument type of :meth:`.Transformer.from_dict`."""

    format: Required[FormatType]
    """The format of par file."""
    parameter: Required[Mapping[int | str, ParameterDictType]]
    """The parameters, the key must be integer-like."""
    description: str | None
    """The description of the parameter, optional."""


if __name__ == "__main__":
    pass
