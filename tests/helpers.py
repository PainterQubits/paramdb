"""Helper functions for paramdb tests."""

from __future__ import annotations
from typing import Any
from dataclasses import dataclass, field
import time
from paramdb import ParamData, Param, Struct, ParamList, ParamDict

DEFAULT_NUMBER = 1.23
DEFAULT_STRING = "test"


@dataclass
class CustomParam(Param):
    """Custom parameter."""

    number: float = DEFAULT_NUMBER
    string: str = DEFAULT_STRING


@dataclass
# pylint: disable-next=too-many-instance-attributes
class CustomStruct(Struct):
    """Custom parameter structure."""

    number: float = DEFAULT_NUMBER
    string: str = DEFAULT_STRING
    list: list[Any] = field(default_factory=list)
    dict: dict[str, Any] = field(default_factory=dict)
    param: CustomParam | None = None
    struct: CustomStruct | None = None
    param_list: ParamList[Any] = field(default_factory=ParamList)
    param_dict: ParamDict[Any] = field(default_factory=ParamDict)
    param_data: ParamData | None = None


class CustomParamList(ParamList[Any]):
    """Custom parameter list subclass."""


class CustomParamDict(ParamDict[Any]):
    """Custom parameter dictionary subclass."""


def sleep_for_datetime() -> None:
    """
    Wait for a short amount of time so that following calls to `datetime.now()` are
    different than those that come before.

    This is necessary because a `datetime` object is only precise to microseconds (see
    https://docs.python.org/3/library/datetime.html#datetime-objects), whereas modern
    computers execute instructions faster than this. So without waiting, it is difficult
    to ensure that something is using `datetime.now()`.
    """
    time.sleep(0.001)  # Wait for one millisecond
