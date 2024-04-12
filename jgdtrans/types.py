"""Provides types."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from typing_extensions import NotRequired, Required, TypeAlias, TypedDict

__all__ = [
    "FormatType",
    #
    "ParameterDict",
    "TransformerDict",
    #
    "ParameterLikeMapping",
    "TransformerLikeMapping",
]

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


class ParameterDict(TypedDict):
    """Type for :meth:`.Transformer.to_dict` output."""

    latitude: Required[float]
    """The latitude parameter on the point [sec]."""
    longitude: Required[float]
    """The longitude parameter on the point [sec]."""
    altitude: Required[float]
    """The altitude parameter on the point [m]."""


class ParameterLikeMapping(TypedDict):
    """Type for :meth:`.Transformer.from_dict` input."""

    latitude: Required[float]
    """The latitude parameter on the point [sec]."""
    longitude: Required[float]
    """The longitude parameter on the point [sec]."""
    altitude: Required[float]
    """The altitude parameter on the point [m]."""


class TransformerDict(TypedDict):
    """Type of :meth:`.Transformer.to_dict` output."""

    format: Required[FormatType]
    """The unit of the mesh, :obj:`1` or :obj:`5`."""
    parameter: Required[Mapping[int, ParameterDict]]
    """The parameters."""
    description: Required[str | None]
    """The description of the parameter."""


class TransformerLikeMapping(TypedDict):
    """Type of :meth:`.Transformer.from_dict` input."""

    format: Required[FormatType]
    """The unit of the mesh, :obj:`1` or :obj:`5`."""
    parameter: Required[Mapping[int | str, ParameterLikeMapping]]
    """The parameters, the key must be integer-like."""
    description: NotRequired[str | None]
    """The description of the parameter, optional."""


if __name__ == "__main__":
    pass
