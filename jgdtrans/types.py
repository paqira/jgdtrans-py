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
    "TKY2JGD", "PatchJGD", "PatchJGD_H", "PatchJGD_HV", "HyokoRev", "SemiDynaEXE", "geonetF3", "ITRF2014"
]
"""Type of par file's format"""


class ParameterDict(TypedDict):
    """Type for :meth:`.Transformer.to_dict` output."""

    latitude: Required[float]
    """The latitude parameter on the point [sec]"""
    longitude: Required[float]
    """The longitude parameter on the point [sec]"""
    altitude: Required[float]
    """The altitude parameter on the point [m]"""


class ParameterLikeMapping(TypedDict):
    """Type for :meth:`.Transformer.from_dict` input."""

    latitude: Required[float]
    """The latitude parameter on the point [sec]"""
    longitude: Required[float]
    """The longitude parameter on the point [sec]"""
    altitude: Required[float]
    """The altitude parameter on the point [m]"""


class TransformerDict(TypedDict):
    """Type of :meth:`.Transformer.to_dict` output."""

    unit: Required[Literal[1, 5]]
    """The unit of the mesh, 1 or 5"""
    parameter: Required[Mapping[int, ParameterDict]]
    """The parameters"""
    description: Required[str | None]
    """The description of the parameter"""


class TransformerLikeMapping(TypedDict):
    """Type of :meth:`.Transformer.from_dict` input."""

    unit: Required[Literal[1, 5]]
    """The unit of the mesh, 1 or 5"""
    parameter: Required[Mapping[int | str, ParameterLikeMapping]]
    """The parameters, the key must be integer-like"""
    description: NotRequired[str | None]
    """The description of the parameter, optional"""


if __name__ == "__main__":
    pass
