"""Helper functions for paramdb tests."""

# In Python 3.9, Pylint complains that field() cannot be used in parameter dataclasses,
# so we disable the rule here.
# pylint: disable=invalid-field-call

from __future__ import annotations
from typing import Any
from collections.abc import Iterator
from dataclasses import dataclass, field
from contextlib import contextmanager
import time
from astropy.units import Quantity  # type: ignore # pylint: disable=import-error
from paramdb import ParamData, Param, Struct, ParamList, ParamDict

DEFAULT_NUMBER = 1.23
DEFAULT_STRING = "test"


class CustomParam(Param):
    """Custom parameter."""

    number: float = DEFAULT_NUMBER
    number_init_false: float = field(init=False, default=DEFAULT_NUMBER)
    number_with_units: Quantity = Quantity(12, "m")
    string: str = DEFAULT_STRING


class CustomStruct(Struct):
    """Custom parameter structure."""

    number: float = DEFAULT_NUMBER
    number_init_false: float = field(init=False, default=DEFAULT_NUMBER)
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


@dataclass
class Times:
    """Start and end times captured by ``capture_start_end_times()``."""

    start: float
    end: float = 0


@contextmanager
def capture_start_end_times(wait_time: float = 10e-6) -> Iterator[Times]:
    """
    Record the start and end times within a with statement using this context manager.

    Also waits for a short amount of time after setting the start time and before
    setting the end time so that following calls to ``datetime.now()`` are different
    that then one being targeted. This is necessary because a ``datetime`` object is
    only precise to microseconds (see
    https://docs.python.org/3/library/datetime.html#datetime-objects), whereas computers
    execute instructions faster. So without waiting a few microseconds, it is difficult
    to verify that something is using the current time.
    """
    times = Times(time.time())
    time.sleep(wait_time)
    yield times
    time.sleep(wait_time)
    times.end = time.time()
