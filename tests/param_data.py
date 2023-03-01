"""Parameter data classes used for testing."""

from __future__ import annotations
from dataclasses import dataclass, field
from paramdb import Struct, Param


DEFAULT_NUMBER = 1.23
DEFAULT_STRING = "test"


@dataclass
class CustomStruct(Struct):
    """Custom parameter structure."""

    number: float = DEFAULT_NUMBER
    string: str = DEFAULT_STRING
    param: CustomParam | None = None
    struct: CustomStruct | None = None
    param_list: list[CustomParam | list[CustomParam] | dict[str, CustomParam]] = field(
        default_factory=list
    )
    param_dict: dict[
        str, CustomParam | list[CustomParam] | dict[str, CustomParam]
    ] = field(default_factory=dict)


@dataclass
class CustomParam(Param):
    """Custom parameter."""

    number: float = DEFAULT_NUMBER
    string: str = DEFAULT_STRING
