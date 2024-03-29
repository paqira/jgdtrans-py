from __future__ import annotations

from typing import Final

from . import (
    dms,  # noqa: F401
    error,  # noqa: F401
    mesh,  # noqa: F401
    parser,  # noqa: F401
    point,  # noqa: F401
    transformer,  # noqa: F401
    types,  # noqa: F401
)
from .error import NotConvergeError, ParameterNotFoundError, ParseError
from .parser import load, loads
from .point import Point
from .transformer import Transformer, from_dict

__version__: Final = "0.1.1"

__home__: Final = ".jgdtrans"
__config__: Final = "config.toml"
__cli__: Final = "JGDtrans"

__all__ = [
    #
    "load",
    "loads",
    #
    "from_dict",
    #
    "Transformer",
    #
    "Point",
    #
    "ParseError",
    "ParameterNotFoundError",
    "NotConvergeError",
]
