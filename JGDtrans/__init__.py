from __future__ import annotations

from . import (
    error,  # noqa: F401
    mesh,  # noqa: F401
    parser,  # noqa: F401
    point,  # noqa: F401
    transformer,  # noqa: F401
    types,  # noqa: F401
    utils,  # noqa: F401
)
from .error import NotConvergeError, ParameterNotFoundError, ParseError
from .parser import load, loads
from .point import Point
from .transformer import Transformer, from_dict

__version__ = "0.1.0"

__home__ = ".jgdtrans"
__config__ = "config.toml"
__cli__ = "JGDtrans"

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
